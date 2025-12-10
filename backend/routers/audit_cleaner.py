#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计日志清理API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import User
from auth import get_current_user
from utils.audit_cleaner import AuditCleaner
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class CleanByDaysRequest(BaseModel):
    days: int
    status: Optional[str] = None


class CleanByCountRequest(BaseModel):
    keep_count: int


@router.get("/statistics")
def get_audit_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取审计日志统计信息
    """
    # 只有管理员可以查看
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    cleaner = AuditCleaner(db)
    stats = cleaner.get_statistics()
    
    return {
        "success": True,
        "data": stats
    }


@router.post("/clean-by-days")
def clean_by_days(
    request: CleanByDaysRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    按天数清理审计日志
    保留最近N天的记录，删除更早的记录
    """
    # 只有管理员可以清理
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    if request.days < 1:
        raise HTTPException(status_code=400, detail="保留天数必须大于0")
    
    try:
        cleaner = AuditCleaner(db)
        result = cleaner.clean_by_days(request.days, request.status)
        
        logger.info(f"管理员 {current_user.username} 执行了审计日志清理（按天数），保留{request.days}天")
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {result['deleted_logs']} 条记录",
            "data": result
        }
    except Exception as e:
        logger.error(f"清理审计日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.post("/clean-by-count")
def clean_by_count(
    request: CleanByCountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    按数量清理审计日志
    只保留最新的N条记录
    """
    # 只有管理员可以清理
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    if request.keep_count < 100:
        raise HTTPException(status_code=400, detail="保留数量不能少于100条")
    
    try:
        cleaner = AuditCleaner(db)
        result = cleaner.clean_by_count(request.keep_count)
        
        logger.info(f"管理员 {current_user.username} 执行了审计日志清理（按数量），保留{request.keep_count}条")
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {result['deleted_logs']} 条记录",
            "data": result
        }
    except Exception as e:
        logger.error(f"清理审计日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.post("/clean-orphan-files")
def clean_orphan_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    清理孤儿日志文件
    删除数据库中没有记录的日志文件
    """
    # 只有管理员可以清理
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        cleaner = AuditCleaner(db)
        result = cleaner.clean_orphan_files()
        
        logger.info(f"管理员 {current_user.username} 执行了孤儿文件清理")
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {result['deleted_files']} 个孤儿文件",
            "data": result
        }
    except Exception as e:
        logger.error(f"清理孤儿文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")
