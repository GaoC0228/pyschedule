#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移：为tasks表添加script_params字段
用于存储Python脚本的命令行参数
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

def upgrade():
    """添加script_params字段"""
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'tasks'
            AND COLUMN_NAME = 'script_params'
        """))
        
        exists = result.fetchone()[0] > 0
        
        if not exists:
            print("添加script_params字段...")
            conn.execute(text("""
                ALTER TABLE tasks 
                ADD COLUMN script_params TEXT COMMENT '脚本参数（命令行参数）'
                AFTER script_path
            """))
            conn.commit()
            print("✓ script_params字段添加成功")
        else:
            print("✓ script_params字段已存在，跳过")

def downgrade():
    """删除script_params字段"""
    with engine.connect() as conn:
        print("删除script_params字段...")
        conn.execute(text("""
            ALTER TABLE tasks DROP COLUMN IF EXISTS script_params
        """))
        conn.commit()
        print("✓ script_params字段已删除")

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加脚本参数字段")
    print("=" * 60)
    
    try:
        upgrade()
        print("\n迁移成功！")
    except Exception as e:
        print(f"\n迁移失败: {e}")
        sys.exit(1)
