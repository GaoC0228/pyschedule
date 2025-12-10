#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查审计日志"""
from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # 查看最近的审计日志
    result = conn.execute(text("""
        SELECT al.id, u.username, al.action, al.resource_type, 
               al.script_name, al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.id DESC
        LIMIT 20
    """))
    
    print("=" * 80)
    print("最近20条审计日志：")
    print("=" * 80)
    
    rows = result.fetchall()
    if not rows:
        print("❌ 数据库中没有审计日志记录！")
    else:
        for row in rows:
            print(f"ID: {row[0]:4d} | 用户: {row[1]:10s} | 操作: {row[2]:15s} | "
                  f"资源: {row[3]:10s} | 脚本: {row[4] or '-':20s} | "
                  f"时间: {row[5]}")
    
    print("=" * 80)
    
    # 统计各用户的操作数
    result = conn.execute(text("""
        SELECT u.username, COUNT(*) as count
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        GROUP BY u.username
        ORDER BY count DESC
    """))
    
    print("\n用户操作统计：")
    print("-" * 40)
    for row in result:
        print(f"  {row[0]:15s}: {row[1]:4d} 条")
    
    # 检查back用户的记录
    result = conn.execute(text("""
        SELECT al.id, al.action, al.resource_type, al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE u.username = 'back'
        ORDER BY al.id DESC
        LIMIT 10
    """))
    
    print("\n" + "=" * 80)
    print("back用户的最近操作：")
    print("=" * 80)
    
    rows = result.fetchall()
    if not rows:
        print("❌ back用户没有任何操作记录！")
    else:
        for row in rows:
            print(f"ID: {row[0]:4d} | 操作: {row[1]:20s} | 资源: {row[2]:15s} | 时间: {row[3]}")
