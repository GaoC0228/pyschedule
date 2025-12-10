from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import AuditLog, User
from schemas import AuditLogResponse
from auth import get_current_user, require_admin

router = APIRouter(prefix="/api/audit", tags=["审计日志"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志列表"""
    query = db.query(AuditLog)
    
    # 非管理员只能查看自己的日志
    if current_user.role != "admin":
        query = query.filter(AuditLog.user_id == current_user.id)
    elif user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志详情"""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    # 非管理员只能查看自己的日志
    if current_user.role != "admin" and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此日志")
    
    return log
