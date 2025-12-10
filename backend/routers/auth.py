from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from models import User
from schemas import Token, LoginRequest, UserCreate, UserResponse
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from audit import create_audit_log, AuditAction, ResourceType
from config import settings
from utils.ip_utils import get_real_ip

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # 创建新用户
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=db_user,
        action=AuditAction.USER_CREATE,
        resource_type=ResourceType.USER,
        resource_id=db_user.id,
        ip_address=get_real_ip(request)
    )
    
    return db_user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 检查用户名是否存在
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查密码是否正确
    if not verify_password(form_data.password, user.hashed_password):
        # 记录密码错误的审计日志
        create_audit_log(
            db=db,
            user=user,
            action=AuditAction.USER_LOGIN_FAILED,
            resource_type=ResourceType.USER,
            resource_id=user.id,
            status="failed",
            details={"reason": "密码错误"},
            ip_address=get_real_ip(request)
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 用户被禁用处理
    if not user.is_active:
        create_audit_log(
            db=db,
            user=user,
            action=AuditAction.USER_LOGIN_FAILED,
            resource_type=ResourceType.USER,
            resource_id=user.id,
            status="failed",
            details={"reason": "用户已被禁用"},
            ip_address=get_real_ip(request)
        )
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 记录登录成功的审计日志
    create_audit_log(
        db=db,
        user=user,
        action=AuditAction.USER_LOGIN,
        resource_type=ResourceType.USER,
        resource_id=user.id,
        status="success",
        ip_address=get_real_ip(request)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """用户登出"""
    # 清除最后活动时间，使用户立即显示为离线
    current_user.last_activity = None
    db.commit()
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.USER_LOGOUT,
        resource_type=ResourceType.USER,
        resource_id=current_user.id,
        ip_address=get_real_ip(request)
    )
    
    return {"message": "登出成功"}


@router.put("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 验证新密码长度
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码至少需要6个字符"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.USER_UPDATE,
        resource_type=ResourceType.USER,
        resource_id=current_user.id,
        details={"action": "修改密码"},
        ip_address=get_real_ip(request)
    )
    
    return {"message": "密码修改成功"}
