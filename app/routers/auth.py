from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.database import get_session
from app.models.user import User
from app.utils.security import (
    verify_password, get_password_hash, create_access_token, decode_access_token
)
from app.config import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
settings = get_settings()


class UserRegisterRequest:
    def __init__(self, username: str, password: str, email: Optional[str] = None):
        self.username = username
        self.password = password
        self.email = email


@router.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """用户注册"""
    # 密码长度校验（bcrypt 限制 72 字节，中文 3 字节/字符）
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="密码过长，最多 72 字节（约 24 个中文或 72 个英文）")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码过短，至少 6 个字符")

    # 检查用户名是否已存在
    stmt = select(User).where(User.username == username)
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        auth_type="local"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"id": user.id, "username": user.username, "message": "注册成功"}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """用户登录"""
    stmt = select(User).where(User.username == form_data.username)
    user = session.exec(stmt).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/refresh")
def refresh_token(token: str = Depends(oauth2_scheme)):
    """刷新Token"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的token")

    access_token = create_access_token(data=payload)
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """获取当前用户（依赖注入用）"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user_id = int(payload.get("sub"))
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user
