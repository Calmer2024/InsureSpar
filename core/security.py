import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer


def get_password_hash(password: str) -> str:
    """把明文密码变成密文 (原生 bcrypt 写法)"""
    # 1. bcrypt 算法要求输入的是字节流 (bytes)，所以要先把字符串 encode
    pwd_bytes = password.encode('utf-8')
    # 2. 随机生成一个盐值 (Salt)
    salt = bcrypt.gensalt()
    # 3. 进行哈希加密
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    # 4. 把加密后的字节流转回字符串，方便存进数据库
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验密码是否正确 (登录时用)
    相当于 Java 里的 BCrypt.checkpw(plainPassword, hashed)
    """
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')

    # bcrypt 自带的安全比对函数
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)


# 相当于 Spring Boot 里 application.yml 配置的 jwt.secret
# 实际生产中必须极其复杂并放在 .env 里！现在我们随便写一个。
SECRET_KEY = "my-super-secret-key-fastapi-is-awesome"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token 有效期 24 小时


def create_access_token(data: dict) -> str:
    """生成 JWT 令牌"""
    to_encode = data.copy()

    # 1. 设置过期时间 (exp 是 JWT 标准里代表过期时间的保留字段)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # 2. 签名并生成字符串 (这行代码等价于 Java 里的 Jwts.builder().setClaims(to_encode).signWith(...).compact())
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# 这行代码有两个作用：
# 1. 告诉 FastAPI，去请求头的 "Authorization" 字段里提取 "Bearer xxx" 格式的 token。
# 2. tokenUrl="/api/users/login" 是专门给 Swagger UI 看的！它会让文档页面右上角出现一个绿色的 "Authorize" 锁头按钮！
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def verify_token(token: str) -> str:
    """校验 Token 的合法性，并解析出用户名"""
    try:
        # 解码并验证签名和过期时间
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的凭证：找不到用户信息")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的Token格式")