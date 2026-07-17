# 文件：app/models/database.py
import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

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

_database_status = {
    "connected": False,
    "error": "not initialized",
}


def _format_db_error(exc: Exception) -> str:
    original = getattr(exc, "orig", exc)
    return str(original)


def init_db() -> bool:
    """Create database tables if the configured database is reachable."""
    try:
        # Ensure model classes are imported so SQLAlchemy metadata is populated.
        from app.models import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        message = _format_db_error(exc)
        _database_status.update({"connected": False, "error": message})
        logger.warning(
            "Database initialization skipped; persistence is unavailable: %s",
            message,
        )
        return False

    _database_status.update({"connected": True, "error": None})
    logger.info("Database initialized successfully.")
    return True


def get_database_status() -> dict:
    return dict(_database_status)


# 依赖项：每个请求获取独立的数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
