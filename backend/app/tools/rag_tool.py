# 文件：app/tools/rag_tool.py
"""RAG 混合检索引擎 — 向量检索 + BM25 关键词检索 + RRF 融合"""
import json
import numpy as np
from langchain_core.tools import tool
from app.core.config import DATA_DIR

# ==========================================
# 初始化：加载多源数据 + 构建统一索引
# ==========================================
unified_docs = []
search_texts = []
doc_embeddings = None
embedder = None
bm25_index = None


def load_and_unify_data():
    """加载三个 JSON 文件，并统一转换为标准文档格式"""
    global unified_docs, search_texts

    # 1. 加载内部保险规则 (insurance_rules.json)
    try:
        with open(DATA_DIR / "insurance_rules.json", "r", encoding="utf-8") as f:
            rules_data = json.load(f)
            for r in rules_data:
                unified_docs.append({
                    "source_type": "internal_rule",
                    "title": f"规则ID: {r.get('rule_id', '未知')}",
                    "content": f"▶️ 核心事实：{r.get('content', '')}\n▶️ 内部防坑指南：{r.get('evaluator_criteria', '')}",
                    # 检索用的文本：把分类、标签和正文揉在一起
                    "search_text": f"{r.get('category', '')} {' '.join(r.get('tags', []))} {r.get('content', '')}"
                })
        print(f"📄 已加载 {len(rules_data)} 条内部保险规则。")
    except Exception as e:
        print(f"⚠️ 内部规则文件加载失败: {e}")

    # 2. 加载保险法 (insurance_law_structured.json)
    try:
        with open(DATA_DIR / "insurance_law_structured.json", "r", encoding="utf-8") as f:
            law_data = json.load(f)
            for l in law_data:
                unified_docs.append({
                    "source_type": "insurance_law",
                    "title": f"《保险法》{l.get('chapter', '')} {l.get('article_number', '')}",
                    "content": l.get('content', ''),
                    "search_text": l.get('text_for_embedding', '')
                })
        print(f"📄 已加载 {len(law_data)} 条《保险法》条款。")
    except Exception as e:
        print(f"⚠️ 《保险法》文件加载失败: {e}")

    # 3. 加载疾病与术语定义 (insurance_definitions_structured.json)
    try:
        with open(DATA_DIR / "insurance_definitions_structured.json", "r", encoding="utf-8") as f:
            def_data = json.load(f)
            for d in def_data:
                is_core = " (行业统一规范核心28种重疾)" if d.get("is_standard_28") else ""
                prefix = "重大疾病" if d.get("source_type") == "disease_definition" else "术语定义"
                unified_docs.append({
                    "source_type": d.get("source_type", "definition"),
                    "title": f"[{prefix}] {d.get('entity_name', '')}{is_core}",
                    "content": d.get('content', ''),
                    "search_text": d.get('text_for_embedding', '')
                })
        print(f"📄 已加载 {len(def_data)} 条疾病与术语定义。")
    except Exception as e:
        print(f"⚠️ 定义文件加载失败: {e}")

    # 提取所有用于检索的文本
    search_texts = [doc["search_text"] for doc in unified_docs]


# 执行数据加载
load_and_unify_data()

try:
    if search_texts:
        # ---- 构建向量索引 ----
        try:
            from sentence_transformers import SentenceTransformer

            print("⏳ 正在构建向量索引（包含规则、法律、定义）...")
            embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            doc_embeddings = embedder.encode(search_texts)
            print(f"✅ 全局向量索引构建完成！")
        except ImportError:
            print("⚠️ sentence_transformers 未安装，向量检索不可用")
        except Exception as e:
            print(f"⚠️ 向量索引构建失败: {e}")

        # ---- 构建 BM25 关键词索引 ----
        try:
            from rank_bm25 import BM25Okapi
            import jieba

            tokenized_docs = [list(jieba.cut(text)) for text in search_texts]
            bm25_index = BM25Okapi(tokenized_docs)
            print(f"✅ 全局 BM25 倒排索引构建完成！")
        except ImportError:
            print("⚠️ rank_bm25 或 jieba 未安装，关键词检索不可用。")
        except Exception as e:
            print(f"⚠️ BM25 索引构建失败: {e}")
    else:
        print("❌ 没有加载到任何文档，跳过索引构建。")
except Exception as e:
    print(f"❌ 索引构建流程发生严重错误: {e}")


# ==========================================
# 核心：RRF (Reciprocal Rank Fusion) 融合算法
# ==========================================
def reciprocal_rank_fusion(ranked_lists: list[list[int]], k: int = 60) -> list[int]:
    """将多个排序结果通过 RRF 融合为统一排序。"""
    scores = {}
    for ranked_list in ranked_lists:
        for rank, doc_idx in enumerate(ranked_list):
            if doc_idx not in scores:
                scores[doc_idx] = 0.0
            scores[doc_idx] += 1.0 / (k + rank + 1)
    sorted_docs = sorted(scores.keys(), key=lambda idx: scores[idx], reverse=True)
    return sorted_docs


# ==========================================
# 工具：统一混合检索 (供 Agent 调用)
# ==========================================
@tool
def search_insurance_knowledge(query: str) -> str:
    """
    当遇到保险条款、核保规则、理赔条件、《保险法》法律条文、重大疾病医学定义、或保险专业术语时，必须调用此工具！
    参数 query: 一句简短的自然语言查询或者词语，例如 "收缩压150能投保吗"、“高血压投保”、"原位癌属于重疾吗" 、“佣金” 或 "保险法中关于如实告知是怎么规定的"。
    """
    if not unified_docs:
        return "【系统错误】知识库未加载或为空。"

    print(f"🔍 [RAG全局检索] 查询: '{query}'")
    # 因为现在知识库变大了，我们将召回数量稍微调高一点，保证上下文充足
    top_k = 4
    ranked_lists = []

    # ---- 通道1：向量语义检索 ----
    if embedder is not None and doc_embeddings is not None:
        from sklearn.metrics.pairwise import cosine_similarity
        query_embedding = embedder.encode([query])
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        vec_top_indices = np.argsort(similarities)[::-1][:top_k].tolist()
        ranked_lists.append(vec_top_indices)

    # ---- 通道2：BM25 关键词检索 ----
    if bm25_index is not None:
        try:
            import jieba
            tokenized_query = list(jieba.cut(query))
            bm25_scores = bm25_index.get_scores(tokenized_query)
            bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k].tolist()
            ranked_lists.append(bm25_top_indices)
        except Exception as e:
            print(f"  ⚠️ BM25 检索出错: {e}")

    # ---- 融合 ----
    if not ranked_lists:
        return "【系统错误】所有检索通道均不可用。"

    if len(ranked_lists) >= 2:
        fused_indices = reciprocal_rank_fusion(ranked_lists)[:top_k]
    else:
        fused_indices = ranked_lists[0]

    # ---- 组装返回给 Agent 的上下文 ----
    result_str = f"【查询成功】为您在全局知识库中找到最相关的 {len(fused_indices)} 条参考信息：\n\n"

    for rank, idx in enumerate(fused_indices, 1):
        doc = unified_docs[idx]
        result_str += f"=== [参考资料 {rank}] {doc['title']} ===\n"
        result_str += f"{doc['content']}\n\n"

    print(f"🎯 [RAG全局检索] 命中项: {[unified_docs[i]['title'] for i in fused_indices]}")
    return result_str