# 文件：app/tools/calculators.py
"""保费费率查询 & 现金价值拟合计算工具"""
import pandas as pd
from langchain_core.tools import tool
from app.core.config import DATA_DIR

# ==========================================
# 初始化：启动时加载 CSV 到内存
# ==========================================
try:
    df_rates = pd.read_csv(DATA_DIR / "insurance_rates.csv")
    print(f"✅ 费率表加载成功！共 {len(df_rates)} 条记录。")
except Exception as e:
    print(f"❌ 费率表加载失败: {e}")
    df_rates = None


# ==========================================
# 工具 1：保费费率查询
# ==========================================
@tool
def query_premium_rate(age: int, gender: str, pay_period: int, base_amount: int = 10000) -> str:
    """
    当需要查阅"每年交多少钱保费"时调用此工具。
    参数:
        age (int): 投保年龄 (0-70)
        gender (str): 性别 ('男' 或 '女')
        pay_period (int): 交费期，可选: 1(趸交), 3, 5, 10, 15, 20, 25, 30
        base_amount (int): 基本保额，默认 10000
    返回:
        精准保费金额或拒保提示。
    """
    print(f"🔧 [工具调用] 查询费率: 年龄={age}, 性别={gender}, 交费期={pay_period}年, 保额={base_amount}")

    if df_rates is None:
        return "【系统错误】费率表未加载，无法查询保费。"

    # 规整化性别
    if gender in ['男', 'M', 'm', 'male', 'Male']:
        g_str = '男性'
    elif gender in ['女', 'F', 'f', 'female', 'Female']:
        g_str = '女性'
    else:
        return "【查询失败】性别参数错误，请使用 '男' 或 '女'。"

    # 规整化交费期
    if pay_period == 1:
        period_str = "一次性交纳"
    elif pay_period in [3, 5, 10, 15, 20, 25, 30]:
        period_str = f"{pay_period}年交"
    else:
        return f"【查询失败】不支持的交费期：{pay_period}年。仅支持 1, 3, 5, 10, 15, 20, 25, 30。"

    col_name = f"{period_str}_{g_str}"

    if col_name not in df_rates.columns:
        return f"【查询失败】找不到费率组合：{col_name}"

    row = df_rates[df_rates['投保年龄'] == age]
    if row.empty:
        return f"【查询失败】投保年龄 {age} 岁超出可投保范围（0-70岁）。"

    rate = row.iloc[0][col_name]

    if pd.isna(rate):
        return f"【查询失败】规则限制：{age}岁客户无法选择 {pay_period}年交（年龄+交费期过高，触发风控）。"

    premium = rate * (base_amount / 10000)
    return f"【查询成功】{age}岁{g_str}，{base_amount}元保额，{period_str}，每年保费: {premium:.2f} 元。"


# ==========================================
# 工具 2：现金价值拟合查询
# ==========================================
@tool
def query_cash_value(gender: str, age: int, pay_period: int, year: int, base_amount: int = 10000) -> str:
    """
    当关心"中途退保能拿回多少钱"、"老了以后账户里有多少钱"时，查询特定年度的现金价值。
    参数:
        gender (str): 性别 ('男' 或 '女')
        age (int): 投保时年龄 (0-70)
        pay_period (int): 交费期 (1, 3, 5, 10, 15, 20, 25, 30)
        year (int): 保单年度，如第15年退保填15
        base_amount (int): 基本保额，默认 10000
    返回:
        该年度末的预估现金价值。
    """
    print(f"🔧 [工具调用] 计算现金价值: 性别={gender}, 年龄={age}, 交费期={pay_period}, 第{year}年, 保额={base_amount}")

    g_code = 'M' if gender in ['男', '男性', 'M', 'm'] else 'F'

    if age + year > 105:
        return f"【计算失败】{age + year} 岁超出产品满期年龄 105 岁。"

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

    return f"【计算成功】第 {year} 年（{age + year} 岁时）退保，预计现金价值约: {final_cv} 元。"
