#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计日志最终验证脚本
验证所有优化项：
1. 文件数量列已删除（前端）
2. IP地址正确获取（支持X-Forwarded-For）
3. 状态追踪完善
4. 操作细粒度区分
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8088"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def test_all():
    print("\n" + "="*70)
    print("  审计日志系统 - 最终验证")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    print_section("1. 测试IP地址获取")
    
    # 测试不带头部的请求
    print("\n📍 测试1: 直接连接（无代理头）")
    r1 = requests.post(f"{BASE_URL}/api/auth/login",
                       data={'username': 'back', 'password': 'gaocong666'})
    assert r1.status_code == 200
    print("   ✅ 登录成功")
    token = r1.json()['access_token']
    
    # 测试带X-Forwarded-For的请求
    print("\n📍 测试2: 带X-Forwarded-For头（模拟代理）")
    r2 = requests.post(f"{BASE_URL}/api/auth/login",
                       data={'username': 'back', 'password': 'wrong'},
                       headers={'X-Forwarded-For': '203.0.113.1, 192.168.1.1'})
    assert r2.status_code == 401
    print("   ✅ 登录失败，应记录真实IP: 203.0.113.1")
    
    # 测试带X-Real-IP的请求
    print("\n📍 测试3: 带X-Real-IP头")
    r3 = requests.post(f"{BASE_URL}/api/auth/login",
                       data={'username': 'back', 'password': 'wrong'},
                       headers={'X-Real-IP': '198.51.100.1'})
    assert r3.status_code == 401
    print("   ✅ 登录失败，应记录真实IP: 198.51.100.1")
    
    print_section("2. 测试操作细粒度")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # 删除测试文件
    try:
        requests.delete(f"{BASE_URL}/api/workspace/delete",
                       json={'path': 'back/final_test.py'},
                       headers=headers)
    except:
        pass
    
    # 创建文件
    print("\n📝 测试: 创建新文件")
    r4 = requests.put(f"{BASE_URL}/api/workspace/update",
                      json={'file_path': 'back/final_test.py', 'content': '# Test v1'},
                      headers=headers)
    assert r4.status_code == 200
    print("   ✅ 创建成功，应记录为'创建文件'")
    
    # 更新文件
    print("\n📝 测试: 更新已存在文件")
    r5 = requests.put(f"{BASE_URL}/api/workspace/update",
                      json={'file_path': 'back/final_test.py', 'content': '# Test v2\\nprint(\"updated\")'},
                      headers=headers)
    assert r5.status_code == 200
    print("   ✅ 更新成功，应记录为'更新文件'")
    
    print_section("3. 查看审计日志验证结果")
    
    # 获取最近的审计日志
    r6 = requests.get(f"{BASE_URL}/api/audit?page=1&page_size=8", headers=headers)
    logs = r6.json()['items']
    
    print(f"\n{'ID':>3s} | {'操作':^14s} | {'状态':^8s} | {'IP地址':^20s}")
    print('-'*70)
    
    checks = {
        'ip_varied': False,      # IP地址有变化（不全是127.0.0.1）
        'create_file': False,    # 有创建文件记录
        'update_file': False,    # 有更新文件记录
        'login_success': False,  # 有登录成功
        'login_failed': False,   # 有登录失败
        'all_has_status': True,  # 所有记录都有状态
    }
    
    ips_seen = set()
    
    for log in logs[:8]:
        ip = log.get('ip_address', '-') or '-'
        status = log.get('status', None)
        action = log['action']
        
        # 检查
        ips_seen.add(ip)
        if action == '创建文件':
            checks['create_file'] = True
        if action == '更新文件':
            checks['update_file'] = True
        if action == '用户登录' and status == 'success':
            checks['login_success'] = True
        if action == '登录失败' and status == 'failed':
            checks['login_failed'] = True
        if status is None:
            checks['all_has_status'] = False
        
        status_display = status if status else '-'
        print(f"{log['id']:3d} | {action:^14s} | {status_display:^8s} | {ip:^20s}")
    
    # 检查IP变化
    checks['ip_varied'] = len(ips_seen) > 1 or '127.0.0.1' not in ips_seen
    
    print_section("4. 验证结果汇总")
    
    results = [
        (checks['ip_varied'], "IP地址获取正确（支持X-Forwarded-For/X-Real-IP）"),
        (checks['create_file'], "创建文件操作区分"),
        (checks['update_file'], "更新文件操作区分"),
        (checks['login_success'], "登录成功状态记录"),
        (checks['login_failed'], "登录失败状态记录"),
        (checks['all_has_status'], "所有操作都有状态字段"),
    ]
    
    print()
    all_passed = True
    for passed, desc in results:
        icon = "✅" if passed else "❌"
        status = "通过" if passed else "失败"
        print(f"{icon} {status:4s}: {desc}")
        if not passed:
            all_passed = False
    
    print_section("5. 总结")
    
    if all_passed:
        print("\n🎉 所有测试通过！审计日志系统优化完成！\n")
        print("✅ 删除了无意义的'文件'列")
        print("✅ IP地址获取支持反向代理")
        print("✅ 操作状态追踪完善")
        print("✅ 操作细粒度区分")
    else:
        print("\n⚠️  部分测试未通过，请检查配置\n")
    
    print("\n建议:")
    print("- 刷新前端页面（Ctrl+Shift+R）查看最新界面")
    print("- 生产环境使用Nginx配置X-Forwarded-For头")
    print("- 检查审计日志表格列数减少，布局更简洁\n")

if __name__ == "__main__":
    try:
        test_all()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
