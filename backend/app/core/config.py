# 文件：app/core/config.py
"""集中配置管理 — 所有环境变量、模型参数、画像加载均在此处"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 加载 .env 文件
# ==========================================
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

# ==========================================
# 路径常量
# ==========================================
# 项目根目录（FastAPIProject/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# ==========================================
# 数据库配置
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root@localhost:3306/insurespar")

# ==========================================
# LLM 配置
# ==========================================
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

if not LLM_API_KEY:
    print("⚠️ 未检测到 DEEPSEEK_API_KEY，请在 backend/.env 中配置")

# ==========================================
# 业务逻辑配置
# ==========================================
MIN_TURNS_BEFORE_DECISION = 5  # 前5轮强制拦截决策
DECISION_STRIKES_REQUIRED = 2  # 连续判定为决策状态 N 次后，才真正结束对话

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
