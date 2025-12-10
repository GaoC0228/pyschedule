#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移工具 - 自动检查并升级表结构
"""
from sqlalchemy import text, inspect
from database import engine
import logging

logger = logging.getLogger(__name__)


def check_and_add_column(table_name: str, column_name: str, column_definition: str):
    """检查并添加缺失的列
    
    Args:
        table_name: 表名
        column_name: 列名
        column_definition: 列定义SQL（如：BOOLEAN NOT NULL DEFAULT FALSE）
    """
    try:
        # 检查列是否存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            # 列不存在，添加它
            with engine.connect() as conn:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✅ 已添加列: {table_name}.{column_name}")
                return True
        else:
            logger.debug(f"列已存在: {table_name}.{column_name}")
            return False
            
    except Exception as e:
        logger.error(f"检查/添加列失败 {table_name}.{column_name}: {e}")
        raise


def upgrade_database():
    """执行所有数据库升级"""
    logger.info("🔄 开始检查数据库结构...")
    
    migrations = [
        # 格式: (表名, 列名, 列定义, 插入位置AFTER)
        ("users", "can_manage_packages", "BOOLEAN NOT NULL DEFAULT FALSE", "is_active"),
    ]
    
    upgraded_count = 0
    
    for table_name, column_name, column_def, after_column in migrations:
        try:
            # 构建完整的列定义（包含位置）
            full_definition = f"{column_def} AFTER {after_column}"
            if check_and_add_column(table_name, column_name, full_definition):
                upgraded_count += 1
        except Exception as e:
            logger.error(f"迁移失败: {table_name}.{column_name} - {e}")
            # 继续执行其他迁移
            continue
    
    if upgraded_count > 0:
        logger.info(f"✅ 数据库升级完成，共升级 {upgraded_count} 个字段")
    else:
        logger.info("✅ 数据库结构已是最新")
