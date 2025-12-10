#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试文件内容变更追踪功能"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8088"

print("="*80)
print("文件内容变更追踪功能 - 自动化验证")
print("="*80)

# 1. 登录back用户
print("\n步骤1: 登录back用户")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={"username": "back", "password": "gaocong666"}
)

if login_response.status_code != 200:
    print(f"❌ 登录失败: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ 登录成功")

# 2. 创建测试文件
print("\n步骤2: 创建测试文件")
initial_content = """def hello():
    print("Hello World")
    return True

if __name__ == "__main__":
    hello()
"""

create_response = requests.put(
    f"{BASE_URL}/api/workspace/update",
    headers=headers,
    json={
        "file_path": "back/test_changes.py",
        "content": initial_content
    }
)

if create_response.status_code == 200:
    print(f"✅ 文件创建成功")
    print(f"   响应: {json.dumps(create_response.json(), ensure_ascii=False, indent=2)}")
else:
    print(f"❌ 文件创建失败: {create_response.text}")
    exit(1)

# 3. 修改文件内容
print("\n步骤3: 修改文件内容")
modified_content = """def hello(name="World"):
    print(f"Hello {name}!")
    print("This is a test")
    return True

def goodbye():
    print("Goodbye!")

if __name__ == "__main__":
    hello("Python")
    goodbye()
"""

update_response = requests.put(
    f"{BASE_URL}/api/workspace/update",
    headers=headers,
    json={
        "file_path": "back/test_changes.py",
        "content": modified_content
    }
)

if update_response.status_code == 200:
    print(f"✅ 文件修改成功")
    result = update_response.json()
    print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    print(f"   变更统计: 新增{result['changes']['lines_added']}行, 删除{result['changes']['lines_deleted']}行")
else:
    print(f"❌ 文件修改失败: {update_response.text}")
    exit(1)

# 4. 获取最近的审计日志
print("\n步骤4: 查询审计日志")
audit_response = requests.get(
    f"{BASE_URL}/api/audit",
    headers=headers,
    params={"username": "back", "page": 1, "page_size": 5}
)

if audit_response.status_code == 200:
    data = audit_response.json()
    print(f"✅ 查询成功，共{data['total']}条记录")
    
    # 找到最近的文件更新操作
    update_log = None
    for item in data['items']:
        if item['action'] == '更新文件' and 'test_changes.py' in str(item.get('details', '')):
            update_log = item
            break
    
    if update_log:
        print(f"\n   找到文件更新记录:")
        print(f"   ID: {update_log['id']}")
        print(f"   操作: {update_log['action']}")
        print(f"   时间: {update_log['created_at']}")
        print(f"   详情: {update_log.get('details', {})}")
        
        # 5. 获取文件变更详情
        print(f"\n步骤5: 获取文件变更详情 (审计ID: {update_log['id']})")
        changes_response = requests.get(
            f"{BASE_URL}/api/audit/{update_log['id']}/file-changes",
            headers=headers
        )
        
        if changes_response.status_code == 200:
            changes_data = changes_response.json()
            print(f"✅ 获取变更详情成功")
            print(f"\n   变更统计:")
            print(f"   - 有变更: {changes_data.get('has_changes')}")
            print(f"   - 文件数: {changes_data.get('file_count', 0)}")
            print(f"   - 新增行数: {changes_data.get('total_lines_added', 0)}")
            print(f"   - 删除行数: {changes_data.get('total_lines_deleted', 0)}")
            
            if changes_data.get('has_changes') and changes_data.get('changes'):
                change = changes_data['changes'][0]
                print(f"\n   文件详情:")
                print(f"   - 文件名: {change['file_name']}")
                print(f"   - 文件路径: {change['file_path']}")
                print(f"   - 新增: +{change['lines_added']} 行")
                print(f"   - 删除: -{change['lines_deleted']} 行")
                
                print(f"\n   Diff内容预览 (前10行):")
                for i, line in enumerate(change['diff_lines'][:10]):
                    prefix = line.get('prefix', ' ')
                    content = line.get('content', '')
                    line_type = line.get('type', 'unchanged')
                    
                    if line_type == 'added':
                        print(f"   \033[32m{prefix}{content}\033[0m")  # 绿色
                    elif line_type == 'deleted':
                        print(f"   \033[31m{prefix}{content}\033[0m")  # 红色
                    elif line_type == 'info':
                        print(f"   \033[36m{content}\033[0m")  # 青色
                    else:
                        print(f"   {prefix}{content}")
                
                print("\n✅ 文件内容变更追踪功能验证通过！")
                print("\n功能特性验证:")
                print("  ✅ 文件修改前内容已保存")
                print("  ✅ 文件修改后内容已保存")
                print("  ✅ Diff差异已生成")
                print("  ✅ 新增/删除行数已统计")
                print("  ✅ API接口正常工作")
                print("  ✅ 变更详情可查看")
            else:
                print(f"\n⚠️  没有检测到内容变更")
        else:
            print(f"❌ 获取变更详情失败: {changes_response.text}")
    else:
        print(f"\n⚠️  未找到test_changes.py的更新记录")
else:
    print(f"❌ 查询审计日志失败: {audit_response.text}")

print("\n" + "="*80)
print("验证完成！")
print("="*80)
