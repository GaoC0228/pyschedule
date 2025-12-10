#!/usr/bin/env python3
"""
数据库迁移脚本：添加任务执行产出文件记录字段
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

def upgrade():
    """添加output_files字段到task_executions表"""
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'task_executions' 
            AND COLUMN_NAME = 'output_files';
        """))
        exists = result.fetchone()[0] > 0
        
        if not exists:
            # 添加output_files字段
            conn.execute(text("""
                ALTER TABLE task_executions 
                ADD COLUMN output_files TEXT;
            """))
            conn.commit()
            print("✅ 已添加output_files字段到task_executions表")
        else:
            print("ℹ️  output_files字段已存在，跳过")

def downgrade():
    """回滚：删除output_files字段"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE task_executions 
            DROP COLUMN IF EXISTS output_files;
        """))
        conn.commit()
        print("✅ 已删除output_files字段")

if __name__ == "__main__":
    print("开始数据库迁移...")
    try:
        upgrade()
        print("✅ 数据库迁移完成！")
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)
