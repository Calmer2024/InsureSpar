from fastapi import FastAPI
from starlette.responses import HTMLResponse

from routers import user, chat

from core.database import Base, engine

# 这句话会让 SQLAlchemy 检查 models，如果 MySQL 里没有这个表，就自动帮你建表！
# (注意：必须在这之前把你的 models 导入进来，但为了简单，我们在 user 路由里导入了就生效)
import models.user_model
Base.metadata.create_all(bind=engine)

app = FastAPI(title="我的安全认证练习 API")

# 相当于把 Controller 注册到 Spring 容器里
app.include_router(user.router)
app.include_router(chat.router)

# === 新增：配置静态网页 ===
@app.get("/", response_class=HTMLResponse)
async def read_html():
    """访问根目录时，直接返回我们写好的前端页面"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"你好，{name}！这是你的第一个 FastAPI 接口。"}
