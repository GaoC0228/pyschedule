#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件归档工具模块
用于审计日志的文件管理和归档
"""
import os
import shutil
import uuid
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from models import AuditLogFile
import logging

logger = logging.getLogger(__name__)

# 审计存档根目录
ARCHIVE_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audit_archives")

# 文件类型映射
FILE_TYPE_MAP = {
    ".log": "log",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "excel",
    ".json": "json",
    ".txt": "text",
    ".py": "script",
    ".sql": "sql",
}


class FileArchiver:
    """文件归档器"""
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保存档目录存在"""
        os.makedirs(os.path.join(ARCHIVE_ROOT, "logs"), exist_ok=True)
        os.makedirs(os.path.join(ARCHIVE_ROOT, "outputs"), exist_ok=True)
        os.makedirs(os.path.join(ARCHIVE_ROOT, "scripts"), exist_ok=True)
    
    def _get_file_type(self, filename: str) -> str:
        """根据文件扩展名获取文件类型"""
        ext = os.path.splitext(filename)[1].lower()
        return FILE_TYPE_MAP.get(ext, "other")
    
    def _generate_stored_filename(self, user_id: int, original_filename: str) -> str:
        """生成存储文件名"""
        date_str = datetime.now().strftime("%Y%m%d")
        uuid_str = str(uuid.uuid4())[:8]
        return f"{date_str}_{user_id}_{uuid_str}_{original_filename}"
    
    def _get_archive_subdir(self, file_type: str) -> str:
        """根据文件类型获取存档子目录"""
        if file_type == "log":
            return "logs"
        elif file_type == "script":
            return "scripts"
        else:
            return "outputs"
    
    def archive_file(
        self, 
        source_path: str, 
        audit_log_id: int,
        user_id: int,
        file_type: Optional[str] = None
    ) -> Optional[AuditLogFile]:
        """
        归档单个文件
        
        Args:
            source_path: 源文件路径
            audit_log_id: 关联的审计日志ID
            user_id: 用户ID
            file_type: 文件类型（可选，自动检测）
        
        Returns:
            AuditLogFile对象，失败返回None
        """
        try:
            if not os.path.exists(source_path):
                logger.warning(f"源文件不存在: {source_path}")
                return None
            
            # 获取文件信息
            original_filename = os.path.basename(source_path)
            file_size = os.path.getsize(source_path)
            mime_type, _ = mimetypes.guess_type(source_path)
            
            # 确定文件类型
            if not file_type:
                file_type = self._get_file_type(original_filename)
            
            # 生成存储文件名
            stored_filename = self._generate_stored_filename(user_id, original_filename)
            
            # 确定存档目录
            subdir = self._get_archive_subdir(file_type)
            archive_dir = os.path.join(ARCHIVE_ROOT, subdir)
            os.makedirs(archive_dir, exist_ok=True)
            
            # 目标路径
            dest_path = os.path.join(archive_dir, stored_filename)
            
            # 复制文件
            shutil.copy2(source_path, dest_path)
            logger.info(f"文件已归档: {original_filename} -> {dest_path}")
            
            # 创建数据库记录
            audit_file = AuditLogFile(
                audit_log_id=audit_log_id,
                file_type=file_type,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=dest_path,
                file_size=file_size,
                mime_type=mime_type
            )
            
            self.db.add(audit_file)
            self.db.commit()
            self.db.refresh(audit_file)
            
            return audit_file
            
        except Exception as e:
            logger.error(f"归档文件失败 {source_path}: {e}")
            self.db.rollback()
            return None
    
    def archive_directory(
        self,
        directory: str,
        audit_log_id: int,
        user_id: int,
        patterns: Optional[List[str]] = None
    ) -> List[AuditLogFile]:
        """
        归档目录中的文件
        
        Args:
            directory: 目录路径
            audit_log_id: 审计日志ID
            user_id: 用户ID
            patterns: 文件名模式列表（如 ['*.csv', '*.log']）
        
        Returns:
            归档的文件列表
        """
        archived_files = []
        
        try:
            if not os.path.isdir(directory):
                logger.warning(f"目录不存在: {directory}")
                return archived_files
            
            # 如果没有指定模式，归档所有文件
            if not patterns:
                patterns = ['*']
            
            # 遍历目录
            for pattern in patterns:
                for file_path in Path(directory).glob(pattern):
                    if file_path.is_file():
                        audit_file = self.archive_file(
                            str(file_path),
                            audit_log_id,
                            user_id
                        )
                        if audit_file:
                            archived_files.append(audit_file)
            
            logger.info(f"目录归档完成: {directory}, 共 {len(archived_files)} 个文件")
            
        except Exception as e:
            logger.error(f"归档目录失败 {directory}: {e}")
        
        return archived_files
    
    def get_file_path(self, file_id: int) -> Optional[str]:
        """获取归档文件的实际路径"""
        audit_file = self.db.query(AuditLogFile).filter(AuditLogFile.id == file_id).first()
        if audit_file and os.path.exists(audit_file.file_path):
            return audit_file.file_path
        return None
    
    def logical_delete_file(self, file_id: int, user_id: int) -> bool:
        """
        逻辑删除文件
        
        Args:
            file_id: 文件ID
            user_id: 执行删除的用户ID
        
        Returns:
            成功返回True
        """
        try:
            audit_file = self.db.query(AuditLogFile).filter(AuditLogFile.id == file_id).first()
            if not audit_file:
                return False
            
            audit_file.is_deleted = True
            audit_file.deleted_at = datetime.now()
            audit_file.deleted_by = user_id
            
            self.db.commit()
            logger.info(f"文件已逻辑删除: ID={file_id}, by user={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"逻辑删除文件失败 ID={file_id}: {e}")
            self.db.rollback()
            return False
    
    def restore_file(self, file_id: int) -> bool:
        """
        恢复逻辑删除的文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            成功返回True
        """
        try:
            audit_file = self.db.query(AuditLogFile).filter(AuditLogFile.id == file_id).first()
            if not audit_file:
                return False
            
            audit_file.is_deleted = False
            audit_file.deleted_at = None
            audit_file.deleted_by = None
            
            self.db.commit()
            logger.info(f"文件已恢复: ID={file_id}")
            return True
            
        except Exception as e:
            logger.error(f"恢复文件失败 ID={file_id}: {e}")
            self.db.rollback()
            return False
    
    def physical_delete_file(self, file_id: int) -> bool:
        """
        物理删除文件（谨慎使用）
        
        Args:
            file_id: 文件ID
        
        Returns:
            成功返回True
        """
        try:
            audit_file = self.db.query(AuditLogFile).filter(AuditLogFile.id == file_id).first()
            if not audit_file:
                return False
            
            # 删除物理文件
            if os.path.exists(audit_file.file_path):
                os.remove(audit_file.file_path)
                logger.info(f"物理文件已删除: {audit_file.file_path}")
            
            # 删除数据库记录
            self.db.delete(audit_file)
            self.db.commit()
            
            logger.info(f"文件已物理删除: ID={file_id}")
            return True
            
        except Exception as e:
            logger.error(f"物理删除文件失败 ID={file_id}: {e}")
            self.db.rollback()
            return False


def scan_new_files(directory: str, since_time: datetime) -> List[str]:
    """
    扫描目录中新生成的文件
    
    Args:
        directory: 目录路径
        since_time: 起始时间
    
    Returns:
        新文件路径列表
    """
    new_files = []
    
    if not os.path.isdir(directory):
        return new_files
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime >= since_time:
                    new_files.append(file_path)
            except Exception as e:
                logger.error(f"检查文件时间失败 {file_path}: {e}")
    
    return new_files
