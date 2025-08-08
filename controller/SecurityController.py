from datetime import timedelta, datetime
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "1sdff34vcsdr4"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
        "disabled": False,
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    full_name: str
    email: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password, hashed_password):
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """获取密码哈希"""
    return pwd_context.hash(password)


def get_user(db, username: str):
    """从数据库获取用户"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db, username: str, password: str):
    """验证用户"""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


class SecurityController:
    def __init__(self):
        self.router = APIRouter()
        self._setup_router()

    def _setup_router(self):
        self.router.post("/token", response_model=Token, summary="用户登录")(
            self.login_for_access_token
        )
        self.router.get("/users/me", response_model=User, summary="用户信息")(
            self.read_users_me
        )

    async def login_for_access_token(
        self, form_data: OAuth2PasswordRequestForm = Depends()
    ):
        """
        OAuth2兼容的登录接口
        测试账户：
        - 用户名: testuser, 密码: secret
        - 用户名: alice, 密码: secret
        :param form_data: 表单
        :return: 登录返回token
        """
        user = authenticate_user(fake_users_db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    async def read_users_me(self, current_user: User = Depends(get_current_user)):
        """
        获取当前登录用户的信息
        :param current_user: 当前用户
        :return: 信息
        """
        return current_user
