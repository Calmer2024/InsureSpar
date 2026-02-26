from pydantic import BaseModel, EmailStr, Field

# 1. 接收前端传来的注册数据 (类似 UserRegisterDTO)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    # EmailStr 会自动帮你用正则校验邮箱格式！
    # (你之前装的 fastapi[standard] 里已经自带了 email-validator 库，所以直接可用)
    email: EmailStr
    password: str = Field(..., min_length=6, description="密码，至少6位")

# 2. 返回给前端的数据模型 (类似 UserVO)
# 规范：永远不要把包含密码的实体类直接返回给前端！
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    # 这是一个 Pydantic 的配置类，允许模型从 ORM 对象(比如数据库查询结果)中直接读取数据
    class Config:
        from_attributes = True