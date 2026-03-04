"""
InsureSpar — 多智能体保险销售对练系统
FastAPI 入口文件
"""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

# 新版对练系统路由
from app.api.chat import router as chat_router
from app.api.auto import router as auto_router
from app.api.history import router as history_router
from app.api.tools import router as tools_router
from app.models.database import engine, Base

# 关闭 Uvicorn 的 ACCESS 访问日志（避免反复刷屏）
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# 初始化数据库表结构（生产环境建议用 Alembic，目前对练系统直接全量创建即可）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="InsureSpar 保险销售对练系统",
    description="""
### 多智能体协作的保险销售训练平台

**系统特性**：
- **🎙️ 人机对练 (Manual)**: 销售人员（人类）与 AI 客户进行实时对话
- **🤖 自动对战 (Auto)**: 指定销售策略，由 AI 销售与 AI 客户全自动完成对决
- **⚖️ 状态机闭环**: 采用 LangGraph 状态机驱动，实现 `介绍 -> 异议 -> 逼单 -> 成交/拒绝` 的闭环控制
- **🏆 多维考官**: 每轮对话结束后，独立的考官 Agent 会从 [专业、合规、策略] 三个维度进行异步打分与指导

**业务防线机制**:
- 🛡️ **至少5轮防线**: 对话未满5轮强制进入异议处理，禁止过快逼单
- ⚖️ **决策观察期**: 必须连续2轮保持在决策状态（如：同意投保），对话才算真正结束

**核心数据实体**:
- **会话 (Session)**: 贯穿全剧的主键 (`session_id`)
- **历史 (Logs)**: 逐轮对话发言记录
- **评分 (Evaluations)**: 考官的逐轮打分明细
- **报告 (Final Report)**: 对局结束后的六维雷达图与总监综合点评
""",
    version="2.0.0",
)

# 注册路由
app.include_router(chat_router)
app.include_router(auto_router)
app.include_router(history_router)
app.include_router(tools_router)
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


# 调试前端
@app.get("/", response_class=HTMLResponse)
async def root():
    """访问根目录时，返回调试前端页面"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>InsureSpar</h1><p>前端文件未找到，请访问 <a href='/docs'>/docs</a></p>"


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

