# 文件：app/core/config.py
"""集中配置管理 — 所有环境变量、模型参数、画像加载均在此处"""
import os
import json
from pathlib import Path

# ==========================================
# 路径常量
# ==========================================
# 项目根目录（FastAPIProject/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# ==========================================
# LLM 配置
# ==========================================
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-e6a0efee40b14d7a84dc2b6af048bd7d")

# ==========================================
# 对话规则常量
# ==========================================
MIN_TURNS_BEFORE_DECISION = 5  # 至少对话 N 轮后才允许进入决策阶段

# ==========================================
# 加载客户画像配置
# ==========================================
def load_personas() -> dict:
    """从 data/personas.json 加载所有客户画像，返回 {persona_id: persona_dict}"""
    personas_path = DATA_DIR / "personas.json"
    if not personas_path.exists():
        print(f"⚠️ 画像配置文件不存在: {personas_path}")
        return {}
    with open(personas_path, "r", encoding="utf-8") as f:
        personas_list = json.load(f)
    return {p["persona_id"]: p for p in personas_list}


def load_sales_strategies() -> dict:
    """从 data/sales_strategies.json 加载所有销售策略，返回 {strategy_id: strategy_dict}"""
    path = DATA_DIR / "sales_strategies.json"
    if not path.exists():
        print(f"⚠️ 销售策略配置文件不存在: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        strategies_list = json.load(f)
    return {s["strategy_id"]: s for s in strategies_list}


# 启动时一次性加载到内存
PERSONAS = load_personas()
SALES_STRATEGIES = load_sales_strategies()

if PERSONAS:
    print(f"✅ 客户画像加载完成！共 {len(PERSONAS)} 个画像: {', '.join(PERSONAS.keys())}")
else:
    print("⚠️ 未加载到任何客户画像配置")

if SALES_STRATEGIES:
    print(f"✅ 销售策略加载完成！共 {len(SALES_STRATEGIES)} 种策略: {', '.join(SALES_STRATEGIES.keys())}")
else:
    print("⚠️ 未加载到任何销售策略配置")
