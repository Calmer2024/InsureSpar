# 文件：tools/insurance_tools.py
from langchain_core.tools import tool
import pandas as pd
from langchain_core.tools import tool

import json
import numpy as np

# 尝试导入机器学习库
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    # 1. 加载一个极其经典的轻量级多语言 Embedding 模型（首次运行会自动从 HuggingFace 下载，大概 400MB）
    print("⏳ 正在初始化本地向量库（首次加载可能稍慢）...")
    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    # 2. 读取你的 JSON 规则
    with open("insurance_rules.json", "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    # 3. 核心：在 FastAPI 启动时，把所有规则的“文本”一次性翻译成“向量坐标”
    # 我们把 tag 和 content 拼在一起，让坐标的信息更丰富
    rule_texts = [f"{r['category']} {' '.join(r['tags'])} {r['content']}" for r in rules_data]
    rule_embeddings = embedder.encode(rule_texts)

    print(f"✅ 规则向量库构建完成！共加载 {len(rules_data)} 条规则。")

except Exception as e:
    print(f"❌ 向量库初始化失败: {e}")
    embedder = None
    rules_data = []
    rule_embeddings = None


# ==========================================
# 真实工具 3：基于 RAG 的智能规则检索
# ==========================================
@tool
def search_insurance_rules(query: str) -> str:
    """
    当你（客户）遇到不懂的保险条款、核保规则（如高血压能不能买）、理赔条件时，必须调用此工具！
    参数 query: 一句简短的自然语言查询，例如 "收缩压150能投保吗？" 或 "理赔门槛是什么"
    """
    if embedder is None or not rules_data:
        return "【系统错误】规则知识库未加载，无法查询。"

    print(f"🔍 [系统日志] RAG 检索触发，正在知识库中寻找: '{query}'")

    # 1. 把大模型传过来的自然语言问题，也变成“向量坐标”
    query_embedding = embedder.encode([query])

    # 2. 算距离 (保持不变)
    similarities = cosine_similarity(query_embedding, rule_embeddings)[0]

    # 3. 【核心优化】：获取匹配度最高的前 3 名规则的索引
    top_k = 3
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # 4. 组装多条规则的返回字符串
    result_str = f"【查询成功】为您找到最相关的 {top_k} 条规则：\n\n"
    valid_count = 0
    valid_ids = []  # 新增：记录实际命中的规则ID

    for idx in top_indices:
        score = similarities[idx]
        if score < 0.2:  # 稍微放宽一点最低阈值
            continue

        rule = rules_data[idx]
        valid_count += 1
        valid_ids.append(rule['rule_id'])  # 记录ID
        result_str += f"--- 规则ID: {rule['rule_id']} (匹配度: {score:.2f}) ---\n"
        result_str += f"▶️ 核心事实：{rule['content']}\n"
        result_str += f"▶️ 内部防坑指南：{rule['evaluator_criteria']}\n\n"

    if valid_count == 0:
        return "【查询失败】知识库中没有找到相关的保险规则，请勿自行编造。"

    # 修改：在日志中一并打印出规则ID
    print(f"🎯 [系统日志] 检索命中！共返回 {valid_count} 条参考规则，规则ID: {', '.join(valid_ids)}")
    return result_str


# ==========================================
# 初始化：在 FastAPI 启动时把 CSV 加载到内存，避免每次查询都读文件
# ==========================================
try:
    df_rates = pd.read_csv("insurance_rates.csv")
    print("✅ 费率表 (insurance_rates.csv) 加载成功！")
except Exception as e:
    print(f"❌ 警告：未找到费率表文件或读取失败 ({e})")
    df_rates = None


# ==========================================
# 真实工具 1：保费费率查询
# ==========================================
@tool
def query_premium_rate(age: int, gender: str, pay_period: int, base_amount: int = 10000) -> str:
    """
    当你（客户）或者评估考官需要查阅“每年交多少钱保费”时调用此工具。
    参数:
        age (int): 投保年龄 (例如 0-70)
        gender (str): 性别 ('男' 或 '女')
        pay_period (int): 交费期。只能输入: 1 (代表一次性交纳), 3, 5, 10, 15, 20, 25, 30
        base_amount (int): 客户想购买的基本保额，默认为 10000
    返回:
        每年需要交的精准保费金额，或者由于规则限制被拒保的提示。
    """
    print(f"🔧 [系统日志] AI 正在查询费率表: 年龄={age}, 性别={gender}, 交费期={pay_period}年, 保额={base_amount}")

    if df_rates is None:
        return "【系统错误】费率表未正确加载，无法查询保费。"

    # 1. 规整化性别参数
    if gender in ['男', 'M', 'm', 'male', 'Male']:
        g_str = '男性'
    elif gender in ['女', 'F', 'f', 'female', 'Female']:
        g_str = '女性'
    else:
        return "【查询失败】性别参数输入错误，请使用 '男' 或 '女'。"

    # 2. 规整化交费期参数并匹配列名
    if pay_period == 1:
        period_str = "一次性交纳"
    elif pay_period in [3, 5, 10, 15, 20, 25, 30]:
        period_str = f"{pay_period}年交"
    else:
        return f"【查询失败】不支持的交费期：{pay_period}年。仅支持 1, 3, 5, 10, 15, 20, 25, 30年交。"

    col_name = f"{period_str}_{g_str}"

    # 3. 在数据框里查表
    if col_name not in df_rates.columns:
        return f"【查询失败】找不到对应的费率组合：{col_name}"

    row = df_rates[df_rates['投保年龄'] == age]
    if row.empty:
        return f"【查询失败】投保年龄 {age} 岁超出了可投保范围（0-70岁）。"

    rate = row.iloc[0][col_name]

    # 4. 如果查出来是空值(NaN)，说明超出了风控规则
    if pd.isna(rate):
        return f"【查询失败】规则限制：{age}岁客户无法选择 {pay_period}年交（年龄+交费期过高，触发风控拦截）。"

    # 5. 计算最终保费（表里的数字对应 10000 元保额）
    premium = rate * (base_amount / 10000)
    return f"【查询成功】客户画像 ({age}岁{g_str}) 购买 {base_amount}元 保额，选择 {period_str}，每年的保费为: {premium:.2f} 元。"


# ==========================================
# 真实工具 2：现金价值拟合查询
# ==========================================
@tool
def query_cash_value(gender: str, age: int, pay_period: int, year: int, base_amount: int = 10000) -> str:
    """
    当你（客户）关心“我中途退保能拿回多少钱”、“老了以后账户里有多少钱”时，查询特定保单年度的【现金价值】。
    参数:
        gender (str): 性别 ('男' 或 '女')
        age (int): 投保时的年龄 (0-70)
        pay_period (int): 交费期 (例如 1, 5, 10, 20)
        year (int): 想到查询的保单年度。比如客户问“第15年退保能拿多少”，填 15。
        base_amount (int): 基本保险金额，默认为 10000
    返回:
        该保单年度末的预估现金价值。
    """
    print(
        f"🔧 [系统日志] AI 正在计算现金价值: 性别={gender}, 投保年龄={age}, 交费期={pay_period}, 第{year}年退保, 保额={base_amount}")

    # 格式化性别，因为你的拟合函数里需要 'M' 或 'F'
    g_code = 'M' if gender in ['男', '男性', 'M', 'm'] else 'F'

    # 防呆设计：满期为 105 岁
    if age + year > 105:
        return f"【计算失败】客户届时已经 {age + year} 岁，超出了产品满期年龄 105 岁。"

    # --- 下面完全是你的数学拟合逻辑 ---
    def get_v10(a, g):
        v = 1.01 * a ** 2 + 53.8 * a + 1437
        return v * 0.904 if g == 'F' else v

    def get_v30(a, g):
        v = -0.39 * a ** 2 + 105.4 * a + 5160
        return v * 0.937 if g == 'F' else v

    v10 = get_v10(age, g_code)
    v30 = get_v30(age, g_code)
    v_end = 9901
    y_end = 105 - age

    def get_pu_cv(y):
        if y <= 10:
            v0 = 0.72 * v10
            return v0 + (v10 - v0) * (y / 10)
        elif y <= 30:
            return v10 + (v30 - v10) * ((y - 10) / 20)
        elif y <= y_end:
            return v30 + (v_end - v30) * ((y - 30) / (y_end - 30))
        else:
            return v_end

    if year >= pay_period:
        cv_10000 = get_pu_cv(year)
    else:
        target_cv = get_pu_cv(pay_period)
        k = 1.2 + pay_period * 0.05 + age * 0.005
        cv_10000 = target_cv * ((year / pay_period) ** k)

    final_cv = int(cv_10000 * (base_amount / 10000))
    # --- 逻辑结束 ---

    return f"【计算成功】该客户在第 {year} 个保单年度（客户 {age + year} 岁时），如果选择退保，预计可拿回的现金价值约为: {final_cv} 元。"



# # =============== 简单的测试用例 ===============
# if __name__ == "__main__":
#     print("【男性 30岁 10年交】")
#     print("第1年:", get_simplified_cash_value('M', 30, 10, 1), "(真实值: 70)")
#     print("第5年:", get_simplified_cash_value('M', 30, 10, 5), "(真实值: 1180)")
#     print("第10年:", get_simplified_cash_value('M', 30, 10, 10), "(真实值: 3959)")
#     print("第30年:", get_simplified_cash_value('M', 30, 10, 30), "(真实值: 7970)")
#
#     print("\n【男性 30岁 3年交】")
#     print("第1年:", get_simplified_cash_value('M', 30, 3, 1), "(真实值: 619)")
#
#     print("\n【女性 30岁 10年交】")
#     print("第10年:", get_simplified_cash_value('F', 30, 10, 10), "(真实值: 3579)")
#     print("第30年:", get_simplified_cash_value('F', 30, 10, 30), "(真实值: 7469)")