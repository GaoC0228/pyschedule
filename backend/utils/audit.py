#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计日志工具函数
"""

from sqlalchemy.orm import Session
from models import AuditLog
from audit import AuditAction, ResourceType
from typing import Optional


def create_audit_log(
    db: Session,
    user_id: int,
    action: AuditAction,
    resource_type: ResourceType,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    创建审计日志
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID（可选）
        details: 详细信息（可选）
        ip_address: IP地址（可选）
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action.value if hasattr(action, 'value') else action,
        resource_type=resource_type.value if hasattr(resource_type, 'value') else resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    return audit_log
