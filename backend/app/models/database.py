# 文件：app/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import DATABASE_URL

# 创建 SQLAlchemy 引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # 每次连接前检查有效性
    pool_recycle=3600,       # 1小时回收连接
    pool_size=10,
    max_overflow=20,
)

# 创建线程安全的 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# 依赖项：每个请求获取独立的数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
