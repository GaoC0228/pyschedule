#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为users表添加last_activity字段
"""
from sqlalchemy import create_engine, text
from config import settings

def migrate():
    """执行迁移"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 添加last_activity字段
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_activity DATETIME NULL COMMENT '最后活动时间'
            """))
            print("✅ 成功添加 last_activity 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("⚠️ last_activity 字段已存在，跳过")
            else:
                print(f"❌ 添加 last_activity 字段失败: {e}")
                raise
        
        # 提交更改
        conn.commit()
        
        print("\n✅ 数据库迁移完成！")
        print("新增字段:")
        print("  - last_activity: 记录用户最后活动时间（用于在线状态判断）")

if __name__ == "__main__":
    migrate()
