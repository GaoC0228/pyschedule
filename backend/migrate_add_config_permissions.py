#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为database_configs表添加权限控制字段
"""
from sqlalchemy import create_engine, text
from config import settings

def migrate():
    """执行迁移"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 添加或修改created_by字段
        try:
            # 先尝试添加
            conn.execute(text("""
                ALTER TABLE database_configs 
                ADD COLUMN created_by VARCHAR(50) NULL COMMENT '创建者用户名'
            """))
            print("✅ 成功添加 created_by 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("⚠️ created_by 字段已存在，修改类型...")
                # 字段已存在，修改类型
                try:
                    conn.execute(text("""
                        ALTER TABLE database_configs 
                        MODIFY COLUMN created_by VARCHAR(50) NULL COMMENT '创建者用户名'
                    """))
                    print("✅ 成功修改 created_by 字段类型为VARCHAR(50)")
                except Exception as modify_error:
                    print(f"❌ 修改 created_by 字段类型失败: {modify_error}")
                    raise
            else:
                print(f"❌ 添加 created_by 字段失败: {e}")
                raise
        
        # 添加is_public字段
        try:
            conn.execute(text("""
                ALTER TABLE database_configs 
                ADD COLUMN is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开'
            """))
            print("✅ 成功添加 is_public 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("⚠️ is_public 字段已存在，跳过")
            else:
                print(f"❌ 添加 is_public 字段失败: {e}")
                raise
        
        # 提交更改
        conn.commit()
        
        print("\n✅ 数据库迁移完成！")
        print("新增字段:")
        print("  - created_by: 记录配置创建者")
        print("  - is_public: 标记配置是否公开")

if __name__ == "__main__":
    migrate()
