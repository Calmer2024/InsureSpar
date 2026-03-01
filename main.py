"""
InsureSpar — 多智能体保险销售对练系统
FastAPI 入口文件
"""
from fastapi import FastAPI
from starlette.responses import HTMLResponse

# 新版对练系统路由
from app.api.chat import router as chat_router

app = FastAPI(
    title="InsureSpar 保险销售对练系统",
    description="多智能体协作的保险销售训练平台：AI客户 + AI考官 + 状态机编排",
    version="2.0.0",
)

# 注册路由
app.include_router(chat_router)


# 首页
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
    <head><title>InsureSpar</title></head>
    <body style="font-family: sans-serif; text-align: center; padding-top: 80px; background: #f4f4f9;">
        <h1>🎭 InsureSpar 保险销售对练系统</h1>
        <p>请访问 <a href="/docs">/docs</a> 使用 Swagger UI 进行调试</p>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
