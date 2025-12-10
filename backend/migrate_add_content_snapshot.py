#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移：为audit_log_files表添加内容快照字段
"""
from sqlalchemy import create_engine, text
from config import settings

def migrate():
    """执行迁移"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("开始迁移...")
        
        # 添加快照相关字段（MySQL不支持IF NOT EXISTS，使用try-except处理）
        fields = [
            ("content_before", "TEXT", "修改前的文件内容"),
            ("content_after", "TEXT", "修改后的文件内容"),
            ("content_diff", "TEXT", "内容差异（Diff格式）"),
            ("lines_added", "INT DEFAULT 0", "新增行数"),
            ("lines_deleted", "INT DEFAULT 0", "删除行数")
        ]
        
        for field_name, field_type, comment in fields:
            try:
                conn.execute(text(f"""
                    ALTER TABLE audit_log_files 
                    ADD COLUMN {field_name} {field_type} COMMENT '{comment}';
                """))
                conn.commit()
                print(f"✅ 添加{field_name}字段成功")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"⏭️  {field_name}字段已存在，跳过")
                else:
                    print(f"❌ 添加{field_name}字段失败: {e}")
        
        print("\n迁移完成！")

if __name__ == "__main__":
    migrate()
