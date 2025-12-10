from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse
from auth import get_password_hash, get_current_user, require_admin
from audit import create_audit_log, AuditAction, ResourceType
from utils.ip_utils import get_real_ip
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["用户管理"])

# 在线状态判断阈值（5分钟内有活动视为在线）
ONLINE_THRESHOLD_MINUTES = 5


@router.get("/simple")
def list_users_simple(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取简化的用户列表（所有用户可访问）- 用于筛选器"""
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取用户列表（仅管理员）- 包含在线状态"""
    query = db.query(User)
    
    # 支持搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.like(search_pattern)) | 
            (User.email.like(search_pattern))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    # 计算在线状态
    now = datetime.now()
    threshold = now - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    
    result = []
    for user in users:
        user_dict = UserResponse.from_orm(user).dict()
        # 判断是否在线：最后活动时间在阈值内
        user_dict['is_online'] = (
            user.last_activity is not None and 
            user.last_activity > threshold
        )
        result.append(user_dict)
    
    return result


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_create: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建用户（仅管理员）"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_create.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
        role=user_create.role if user_create.role else "user",
        is_active=user_create.is_active if user_create.is_active is not None else True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.USER_CREATE,
        resource_type=ResourceType.USER,
        resource_id=new_user.id,
        details={"username": new_user.username, "email": new_user.email, "role": new_user.role},
        ip_address=get_real_ip(request)
    )
    
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    # 只能查看自己或管理员可以查看所有
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此用户")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    # 只能更新自己或管理员可以更新所有
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此用户")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # 仅管理员可以修改角色和包管理权限
    if current_user.role != "admin":
        update_data.pop("role", None)
        update_data.pop("can_manage_packages", None)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.USER_UPDATE,
        resource_type=ResourceType.USER,
        resource_id=user.id,
        details={"updated_fields": list(update_data.keys())},
        ip_address=get_real_ip(request)
    )
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除用户（仅管理员）"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.USER_DELETE,
        resource_type=ResourceType.USER,
        resource_id=user.id,
        details={"username": user.username},
        ip_address=get_real_ip(request)
    )
    
    db.delete(user)
    db.commit()


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """重置用户密码（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 重置密码
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.USER_UPDATE,
        resource_type=ResourceType.USER,
        resource_id=user.id,
        details={"action": "reset_password", "username": user.username},
        ip_address=get_real_ip(request)
    )
    
    return {"message": "密码重置成功"}


@router.post("/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """切换用户状态（启用/禁用）（仅管理员）"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能修改自己的状态")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 切换状态
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.USER_UPDATE,
        resource_type=ResourceType.USER,
        resource_id=user.id,
        details={"action": "toggle_status", "new_status": user.is_active, "username": user.username},
        ip_address=get_real_ip(request)
    )
    
    return {"message": f"用户已{'启用' if user.is_active else '禁用'}", "is_active": user.is_active}
