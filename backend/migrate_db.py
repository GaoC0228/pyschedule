#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加执行记录的用户和触发方式字段
"""

from database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行数据库迁移"""
    try:
        with engine.connect() as conn:
            # 检查列是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'task_executions'
                AND COLUMN_NAME = 'executed_by'
            """))
            exists = result.fetchone()[0] > 0
            
            if not exists:
                logger.info("添加 executed_by 和 trigger_type 字段...")
                
                # 添加新字段
                conn.execute(text("""
                    ALTER TABLE task_executions
                    ADD COLUMN executed_by INT NULL,
                    ADD COLUMN trigger_type VARCHAR(20) DEFAULT 'scheduled'
                """))
                
                # 添加外键约束
                conn.execute(text("""
                    ALTER TABLE task_executions
                    ADD CONSTRAINT fk_task_executions_executed_by
                    FOREIGN KEY (executed_by) REFERENCES users(id)
                """))
                
                conn.commit()
                logger.info("✓ 数据库迁移完成")
            else:
                logger.info("字段已存在，跳过迁移")
                
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    migrate()
