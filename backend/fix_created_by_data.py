#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复created_by字段数据：将user_id转换为username
"""
from sqlalchemy import create_engine, text
from config import settings

def fix_created_by():
    """修复created_by字段数据"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 先查看当前数据
        result = conn.execute(text("SELECT id, name, created_by FROM database_configs"))
        print("当前数据:")
        for row in result:
            print(f"  ID: {row[0]}, Name: {row[1]}, created_by: {row[2]} (类型: {type(row[2])})")
        
        # 将created_by从user_id转换为username
        # 先查询user_id=1的用户名
        user_result = conn.execute(text("SELECT username FROM users WHERE id = 1")).fetchone()
        if user_result:
            admin_username = user_result[0]
            print(f"\n找到admin用户: {admin_username}")
            
            # 更新所有created_by为1的记录
            conn.execute(text("""
                UPDATE database_configs 
                SET created_by = :username 
                WHERE created_by = '1' OR created_by = 1
            """), {"username": admin_username})
            
            # 将created_by为NULL的记录也设置为admin
            conn.execute(text("""
                UPDATE database_configs 
                SET created_by = :username 
                WHERE created_by IS NULL
            """), {"username": admin_username})
            
            conn.commit()
            
            print(f"\n✅ 已更新所有配置的created_by为: {admin_username}")
        else:
            print("\n❌ 未找到ID=1的用户")
        
        # 验证修复结果
        result = conn.execute(text("SELECT id, name, created_by FROM database_configs"))
        print("\n修复后数据:")
        for row in result:
            print(f"  ID: {row[0]}, Name: {row[1]}, created_by: {row[2]}")

if __name__ == "__main__":
    fix_created_by()
