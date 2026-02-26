from sqlalchemy import Column, Integer, String
from core.database import Base


# 相当于 Java 里的 @Entity 和 @Table(name = "users")
class User(Base):
    __tablename__ = "users"

    # 相当于 @Id 和 @GeneratedValue(strategy = GenerationType.IDENTITY)
    id = Column(Integer, primary_key=True, index=True)

    # 相当于 @Column(unique=true, nullable=false)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)

    # 密码密文存得比较长，给 255
    password = Column(String(255), nullable=False)