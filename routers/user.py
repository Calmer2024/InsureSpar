from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session  # 导入 Session 类型

# 导入我们的数据模型和校验模型
from schemas.user_schema import UserCreate, UserResponse
from models.user_model import User as DBUser
from core.database import get_db

# 导入安全相关的工具函数
from core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    oauth2_scheme,
    verify_token
)

# 相当于 Spring Boot 类上的 @RequestMapping("/api/users") 和 @RestController
router = APIRouter(
    prefix="/api/users",
    tags=["用户模块"]  # 这个 tag 会让 Swagger UI 自动给你分门别类，超好看！
)


# ==========================================
# 1. 注册接口
# ==========================================
@router.post("/register", response_model=UserResponse)
# 注意参数里注入了 db: Session = Depends(get_db)，获取数据库连接！
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 1. 查重 (相当于 userMapper.findByUsername)
    # 使用 SQLAlchemy 的链式调用查询
    existing_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已被注册")

    # 2. 组装实体对象 (把 DTO 转换成 Entity)
    new_db_user = DBUser(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password)  # 密码依然要加密！
    )

    # 3. 保存到数据库
    db.add(new_db_user)  # 相当于 em.persist()
    db.commit()          # 提交事务
    db.refresh(new_db_user)  # 刷新对象，以获取 MySQL 自动生成的自增主键 ID！

    # 4. 返回保存好的对象 (Pydantic 会自动把 DBUser 转成 UserResponse JSON，剔除密码)
    return new_db_user


# ==========================================
# 2. 登录接口
# ==========================================
@router.post("/login")
# 这里不仅注入了表单，还注入了 db: Session 用于连数据库查人！
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. 从真实数据库里找人 (相当于 userMapper.findByUsername)
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()

    # 如果没找到这个人
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 2. 校验密码
    # form_data.password 是前端传来的明文，user.password 是数据库里查出来的密文
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 3. 密码正确，签发 JWT！
    access_token = create_access_token(data={"sub": user.username})

    # 4. 标准返回格式
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==========================================
# 3. 全局拦截器依赖 (获取当前登录用户)
# ==========================================
# 以后哪个接口需要登录才能访问，就把这个函数当作参数传进去
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # 1. 验证 token，拿到藏在里面的用户名
    username = verify_token(token)

    # 2. 去真实数据库里找这个人
    user = db.query(DBUser).filter(DBUser.username == username).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Token对应的用户已不存在")

    # 返回的是真实的 SQLAlchemy 实体对象
    return user


# ==========================================
# 4. 受保护的获取个人信息接口
# ==========================================
# response_model=UserResponse 会帮我们自动把查出来用户的密码屏蔽掉
@router.get("/me", response_model=UserResponse)
# 核心魔法：Depends(get_current_user)！
# 注意这里 current_user 的类型变成了 DBUser (也就是我们刚刚查出来的实体对象)
async def get_my_profile(current_user: DBUser = Depends(get_current_user)):
    """获取当前登录的用户信息"""

    # 只要代码能走到这一行，说明拦截器全票通过，current_user 绝对是安全的真实数据！
    return current_user