#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试工作区审计日志"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8088"

# 1. 登录back用户
print("=" * 80)
print("步骤1: 登录back用户")
print("=" * 80)

login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={"username": "back", "password": "gaocong666"}
)

if login_response.status_code != 200:
    print(f"❌ 登录失败: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ 登录成功，Token: {token[:20]}...")

# 2. 在工作区创建文件
print("\n" + "=" * 80)
print("步骤2: 在工作区创建测试文件")
print("=" * 80)

create_response = requests.put(
    f"{BASE_URL}/api/workspace/update",
    headers=headers,
    json={
        "file_path": "back/test_audit.txt",  # 在back用户目录下创建
        "content": "这是一个测试审计日志的文件\n创建时间: " + str(datetime.now())
    }
)

print(f"状态码: {create_response.status_code}")
print(f"响应: {create_response.text}")

if create_response.status_code == 200:
    print("✅ 文件创建成功")
else:
    print(f"❌ 文件创建失败: {create_response.text}")

# 3. 查询审计日志
print("\n" + "=" * 80)
print("步骤3: 查询back用户的审计日志")
print("=" * 80)

audit_response = requests.get(
    f"{BASE_URL}/api/audit",
    headers=headers,
    params={"username": "back", "page": 1, "page_size": 5}
)

if audit_response.status_code == 200:
    data = audit_response.json()
    if isinstance(data, dict):
        print(f"总记录数: {data.get('total', 0)}")
        items = data.get('items', [])
    else:
        items = data
        print(f"总记录数: {len(items)}")
    
    print(f"\n最近的操作:")
    for item in items[:10]:
        print(f"  - ID:{item['id']} | {item['action']} | {item['resource_type']} | {item['created_at']}")
        if item.get('details'):
            print(f"    详情: {item['details']}")
else:
    print(f"❌ 查询审计日志失败: {audit_response.text}")

# 4. 检查数据库
print("\n" + "=" * 80)
print("步骤4: 直接查询数据库验证")
print("=" * 80)

from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT al.id, u.username, al.action, al.resource_type, al.created_at, al.details
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE u.username = 'back'
        ORDER BY al.id DESC
        LIMIT 5
    """))
    
    rows = result.fetchall()
    print(f"数据库中back用户的最近操作:")
    for row in rows:
        print(f"  - ID:{row[0]} | {row[2]} | {row[3]} | {row[4]}")
        if row[5]:
            print(f"    详情: {row[5]}")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)
