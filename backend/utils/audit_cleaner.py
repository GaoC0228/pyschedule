#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计日志清理工具
支持按时间、数量、状态等条件清理审计日志
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models import AuditLog
from utils.execution_log import delete_execution_log
import logging

logger = logging.getLogger(__name__)


class AuditCleaner:
    """审计日志清理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def clean_by_days(self, days: int, status: Optional[str] = None) -> dict:
        """
        按天数清理审计日志
        
        Args:
            days: 保留最近N天的记录
            status: 可选，只清理指定状态的记录（success/failed/running）
            
        Returns:
            清理统计信息
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AuditLog).filter(AuditLog.created_at < cutoff_date)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        # 获取要删除的记录
        logs_to_delete = query.all()
        
        deleted_count = 0
        deleted_files = 0
        failed_files = 0
        
        for log in logs_to_delete:
            # 删除关联的日志文件
            if log.details:
                try:
                    details = json.loads(log.details)
                    log_file = details.get("log_file")
                    if log_file:
                        if delete_execution_log(log_file):
                            deleted_files += 1
                        else:
                            failed_files += 1
                except Exception as e:
                    logger.warning(f"删除日志文件失败: {e}")
                    failed_files += 1
            
            # 删除数据库记录
            self.db.delete(log)
            deleted_count += 1
        
        self.db.commit()
        
        return {
            "deleted_logs": deleted_count,
            "deleted_files": deleted_files,
            "failed_files": failed_files,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    def clean_by_count(self, keep_count: int) -> dict:
        """
        按数量清理，只保留最新的N条记录
        
        Args:
            keep_count: 保留的记录数量
            
        Returns:
            清理统计信息
        """
        # 获取总数
        total_count = self.db.query(AuditLog).count()
        
        if total_count <= keep_count:
            return {
                "deleted_logs": 0,
                "deleted_files": 0,
                "message": f"当前记录数({total_count})未超过保留数量({keep_count})"
            }
        
        # 获取要保留的最小ID
        logs_to_keep = self.db.query(AuditLog).order_by(AuditLog.id.desc()).limit(keep_count).all()
        min_keep_id = min(log.id for log in logs_to_keep)
        
        # 删除ID小于min_keep_id的记录
        logs_to_delete = self.db.query(AuditLog).filter(AuditLog.id < min_keep_id).all()
        
        deleted_count = 0
        deleted_files = 0
        
        for log in logs_to_delete:
            if log.details:
                try:
                    details = json.loads(log.details)
                    log_file = details.get("log_file")
                    if log_file and delete_execution_log(log_file):
                        deleted_files += 1
                except Exception:
                    pass
            
            self.db.delete(log)
            deleted_count += 1
        
        self.db.commit()
        
        return {
            "deleted_logs": deleted_count,
            "deleted_files": deleted_files,
            "kept_logs": keep_count,
            "min_keep_id": min_keep_id
        }
    
    # clean_orphan_files 功能已移除
    # 原因：逻辑不完善，只检查 AuditLog 表，可能误删定时任务（TaskExecution表）的日志
    # 风险太大，日志删除后无法恢复
    # 建议：管理员在宿主机上手动清理不需要的日志文件
    
    def get_statistics(self) -> dict:
        """
        获取审计日志统计信息
        
        Returns:
            统计信息
        """
        from utils.execution_log import EXECUTION_LOG_DIR
        
        total_logs = self.db.query(AuditLog).count()
        
        # 按状态统计
        success_count = self.db.query(AuditLog).filter(AuditLog.status == "success").count()
        failed_count = self.db.query(AuditLog).filter(AuditLog.status == "failed").count()
        running_count = self.db.query(AuditLog).filter(AuditLog.status == "running").count()
        
        # 按类型统计
        interactive_count = 0
        manual_count = 0
        
        all_logs = self.db.query(AuditLog).all()
        for log in all_logs:
            if log.details:
                try:
                    details = json.loads(log.details)
                    trigger_type = details.get("trigger_type")
                    if trigger_type == "interactive":
                        interactive_count += 1
                    elif trigger_type == "manual":
                        manual_count += 1
                except Exception:
                    pass
        
        # 日志文件统计
        file_count = 0
        total_size = 0
        
        if os.path.exists(EXECUTION_LOG_DIR):
            for filename in os.listdir(EXECUTION_LOG_DIR):
                if filename.endswith('.log'):
                    filepath = os.path.join(EXECUTION_LOG_DIR, filename)
                    file_count += 1
                    total_size += os.path.getsize(filepath)
        
        # 最老和最新的记录
        oldest_log = self.db.query(AuditLog).order_by(AuditLog.created_at.asc()).first()
        newest_log = self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
        
        return {
            "total_logs": total_logs,
            "status_breakdown": {
                "success": success_count,
                "failed": failed_count,
                "running": running_count
            },
            "type_breakdown": {
                "interactive": interactive_count,
                "manual": manual_count,
                "other": total_logs - interactive_count - manual_count
            },
            "log_files": {
                "count": file_count,
                "total_size_mb": round(total_size / 1024 / 1024, 2)
            },
            "date_range": {
                "oldest": oldest_log.created_at.isoformat() if oldest_log else None,
                "newest": newest_log.created_at.isoformat() if newest_log else None
            }
        }
