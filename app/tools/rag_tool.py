# 文件：app/tools/rag_tool.py
"""RAG 混合检索引擎 — 向量检索 + BM25 关键词检索 + RRF 融合"""
import json
import numpy as np
from langchain_core.tools import tool
from app.core.config import DATA_DIR

# ==========================================
# 初始化：加载规则数据 + 构建索引
# ==========================================
rules_data = []
rule_texts = []
rule_embeddings = None
embedder = None
bm25_index = None

try:
    # 1. 加载规则 JSON
    with open(DATA_DIR / "insurance_rules.json", "r", encoding="utf-8") as f:
        rules_data = json.load(f)
    rule_texts = [f"{r['category']} {' '.join(r['tags'])} {r['content']}" for r in rules_data]
    print(f"📄 已加载 {len(rules_data)} 条保险规则。")

    # 2. 构建向量索引
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity

        print("⏳ 正在构建向量索引（首次加载可能稍慢）...")
        embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        rule_embeddings = embedder.encode(rule_texts)
        print(f"✅ 向量索引构建完成！")
    except ImportError:
        print("⚠️ sentence_transformers 未安装，向量检索不可用")
    except Exception as e:
        print(f"⚠️ 向量索引构建失败: {e}")

    # 3. 构建 BM25 关键词索引
    try:
        from rank_bm25 import BM25Okapi
        import jieba

        # 对每条规则做分词
        tokenized_rules = [list(jieba.cut(text)) for text in rule_texts]
        bm25_index = BM25Okapi(tokenized_rules)
        print(f"✅ BM25 倒排索引构建完成！")
    except ImportError:
        print("⚠️ rank_bm25 或 jieba 未安装，关键词检索不可用。可通过 pip install rank_bm25 jieba 安装。")
    except Exception as e:
        print(f"⚠️ BM25 索引构建失败: {e}")

except Exception as e:
    print(f"❌ 规则文件加载失败: {e}")


# ==========================================
# 核心：RRF (Reciprocal Rank Fusion) 融合算法
# ==========================================
def reciprocal_rank_fusion(ranked_lists: list[list[int]], k: int = 60) -> list[int]:
    """
    将多个排序结果通过 RRF 融合为统一排序。
    score(doc) = Σ 1 / (k + rank_i)
    """
    scores = {}
    for ranked_list in ranked_lists:
        for rank, doc_idx in enumerate(ranked_list):
            if doc_idx not in scores:
                scores[doc_idx] = 0.0
            scores[doc_idx] += 1.0 / (k + rank + 1)  # rank 从 0 开始, +1 转为 1-based

    # 按 RRF 分数降序排列
    sorted_docs = sorted(scores.keys(), key=lambda idx: scores[idx], reverse=True)
    return sorted_docs


# ==========================================
# 工具：混合检索
# ==========================================
@tool
def search_insurance_rules(query: str) -> str:
    """
    当遇到不懂的保险条款、核保规则（如高血压能不能买）、理赔条件时，必须调用此工具！
    参数 query: 一句简短的自然语言查询，例如 "收缩压150能投保吗？" 或 "理赔门槛是什么"
    """
    if not rules_data:
        return "【系统错误】规则知识库未加载。"

    print(f"🔍 [RAG检索] 查询: '{query}'")
    top_k = 3
    ranked_lists = []

    # ---- 通道1：向量语义检索 ----
    if embedder is not None and rule_embeddings is not None:
        from sklearn.metrics.pairwise import cosine_similarity
        query_embedding = embedder.encode([query])
        similarities = cosine_similarity(query_embedding, rule_embeddings)[0]
        vec_top_indices = np.argsort(similarities)[::-1][:top_k].tolist()
        ranked_lists.append(vec_top_indices)
        print(f"  📐 向量检索 Top-{top_k}: {[rules_data[i]['rule_id'] for i in vec_top_indices]}")

    # ---- 通道2：BM25 关键词检索 ----
    if bm25_index is not None:
        try:
            import jieba
            tokenized_query = list(jieba.cut(query))
            bm25_scores = bm25_index.get_scores(tokenized_query)
            bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k].tolist()
            ranked_lists.append(bm25_top_indices)
            print(f"  🔤 BM25检索 Top-{top_k}: {[rules_data[i]['rule_id'] for i in bm25_top_indices]}")
        except Exception as e:
            print(f"  ⚠️ BM25 检索出错: {e}")

    # ---- 融合 ----
    if not ranked_lists:
        return "【系统错误】所有检索通道均不可用。"

    if len(ranked_lists) >= 2:
        # RRF 融合
        fused_indices = reciprocal_rank_fusion(ranked_lists)[:top_k]
        print(f"  🔀 RRF融合结果: {[rules_data[i]['rule_id'] for i in fused_indices]}")
    else:
        # 只有一个通道可用，直接使用
        fused_indices = ranked_lists[0]

    # ---- 组装返回 ----
    result_str = f"【查询成功】为您找到最相关的 {len(fused_indices)} 条规则：\n\n"
    valid_ids = []

    for idx in fused_indices:
        rule = rules_data[idx]
        valid_ids.append(rule['rule_id'])
        result_str += f"--- 规则ID: {rule['rule_id']} ---\n"
        result_str += f"▶️ 核心事实：{rule['content']}\n"
        result_str += f"▶️ 内部防坑指南：{rule['evaluator_criteria']}\n\n"

    print(f"🎯 [RAG检索] 命中规则: {', '.join(valid_ids)}")
    return result_str
