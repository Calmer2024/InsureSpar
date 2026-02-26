from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL 连接字符串格式: mysql+驱动://用户名:密码@主机:端口/数据库名
# ⚠️ 请把 root 和 123456 换成你本地 MySQL 的账号密码！
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:95515@127.0.0.1:3306/fastapi_demo"

# 1. 创建数据库引擎 (相当于 Spring 里的 DataSource)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. 创建一个会话工厂 (相当于 Hibernate 的 SessionFactory / EntityManager)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 创建所有实体类的基类 (所有实体类都要继承它)
Base = declarative_base()

# 4. 获取数据库会话的依赖函数！(极度核心)
def get_db():
    """
    这个函数会配合 FastAPI 的 Depends 使用。
    它的作用是：每个 HTTP 请求进来时，打开一个数据库连接；请求处理完后，自动关闭连接。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()