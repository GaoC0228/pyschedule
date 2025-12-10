#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计日志状态追踪验证脚本
用于验证：
1. 登录成功/失败状态记录
2. 创建文件 vs 更新文件操作区分
3. 所有操作的状态字段
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8088"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_login_status():
    """测试登录状态追踪"""
    print_section("测试1: 登录状态追踪")
    
    # 登录成功
    print("\n✅ 测试登录成功...")
    r1 = requests.post(f"{BASE_URL}/api/auth/login", 
                       data={'username': 'back', 'password': 'gaocong666'})
    assert r1.status_code == 200, "登录失败"
    token = r1.json()['access_token']
    print("   登录成功，获得token")
    
    # 登录失败 - 密码错误
    print("\n❌ 测试登录失败（密码错误）...")
    r2 = requests.post(f"{BASE_URL}/api/auth/login",
                       data={'username': 'back', 'password': 'wrongpassword'})
    assert r2.status_code == 401, "应该返回401"
    print("   密码错误，返回401")
    
    return token

def test_file_operations(token):
    """测试文件操作细粒度"""
    print_section("测试2: 文件操作细粒度")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 删除测试文件（如果存在）
    try:
        requests.delete(f"{BASE_URL}/api/workspace/delete",
                       json={'path': 'back/test_status.py'},
                       headers=headers)
    except:
        pass
    
    # 创建新文件
    print("\n📝 测试创建新文件...")
    r1 = requests.put(f"{BASE_URL}/api/workspace/update",
                     json={'file_path': 'back/test_status.py', 'content': '# Version 1'},
                     headers=headers)
    assert r1.status_code == 200, "创建文件失败"
    print("   创建文件成功")
    
    # 更新已存在文件
    print("\n✏️  测试更新文件...")
    r2 = requests.put(f"{BASE_URL}/api/workspace/update",
                     json={'file_path': 'back/test_status.py', 'content': '# Version 2\nprint("updated")'},
                     headers=headers)
    assert r2.status_code == 200, "更新文件失败"
    print("   更新文件成功")

def verify_audit_logs(token):
    """验证审计日志"""
    print_section("验证: 审计日志状态")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 获取最近的审计日志
    r = requests.get(f"{BASE_URL}/api/audit?page=1&page_size=10", headers=headers)
    logs = r.json()['items']
    
    print(f"\n{'ID':>4s} | {'操作':^12s} | {'状态':^10s} | {'用户':^8s} | 时间")
    print('-' * 70)
    
    # 统计
    stats = {
        'total': 0,
        'with_status': 0,
        'login_success': 0,
        'login_failed': 0,
        'file_create': 0,
        'file_update': 0
    }
    
    for log in logs[:10]:
        stats['total'] += 1
        status = log.get('status', None)
        if status:
            stats['with_status'] += 1
        
        action = log['action']
        if action == '用户登录' and status == 'success':
            stats['login_success'] += 1
        elif action == '登录失败' and status == 'failed':
            stats['login_failed'] += 1
        elif action == '创建文件':
            stats['file_create'] += 1
        elif action == '更新文件':
            stats['file_update'] += 1
        
        status_display = status if status else '-'
        print(f"{log['id']:4d} | {action:^12s} | {status_display:^10s} | {log['username']:^8s} | {log['created_at']}")
    
    print(f"\n📊 统计结果:")
    print(f"   总记录数: {stats['total']}")
    print(f"   有状态的记录: {stats['with_status']}")
    print(f"   登录成功: {stats['login_success']}")
    print(f"   登录失败: {stats['login_failed']}")
    print(f"   创建文件: {stats['file_create']}")
    print(f"   更新文件: {stats['file_update']}")
    
    # 验证
    print(f"\n✅ 验证结果:")
    checks = [
        (stats['login_success'] > 0, "登录成功状态记录"),
        (stats['login_failed'] > 0, "登录失败状态记录"),
        (stats['file_create'] > 0, "创建文件操作区分"),
        (stats['file_update'] > 0, "更新文件操作记分"),
    ]
    
    for check, desc in checks:
        status = "✅ 通过" if check else "❌ 失败"
        print(f"   {status}: {desc}")

def main():
    print("\n" + "="*60)
    print("  审计日志状态追踪验证脚本")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # 测试登录
        token = test_login_status()
        
        # 测试文件操作
        test_file_operations(token)
        
        # 验证审计日志
        verify_audit_logs(token)
        
        print_section("✅ 所有测试完成")
        print("\n建议: 刷新前端页面（Ctrl+Shift+R）查看最新数据\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
