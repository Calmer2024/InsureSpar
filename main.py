"""
InsureSpar — 多智能体保险销售对练系统
FastAPI 入口文件
"""
from fastapi import FastAPI
from starlette.responses import HTMLResponse

# 新版对练系统路由
from app.api.chat import router as chat_router
from app.api.auto import router as auto_router

app = FastAPI(
    title="InsureSpar 保险销售对练系统",
    description="多智能体协作的保险销售训练平台：AI客户 + AI考官 + 状态机编排",
    version="2.0.0",
)

# 注册路由
app.include_router(chat_router)
app.include_router(auto_router)


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

