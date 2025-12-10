#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重置管理员密码
"""

from database import SessionLocal
from models import User
from auth import get_password_hash

def reset_admin_password():
    """重置管理员密码为 admin123"""
    db = SessionLocal()
    try:
        # 查找admin用户
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            # 重置密码
            new_password = "admin123"
            admin.hashed_password = get_password_hash(new_password)
            db.commit()
            print(f"✓ 管理员密码已重置")
            print(f"  用户名: admin")
            print(f"  新密码: {new_password}")
        else:
            print("✗ 未找到admin用户")
            print("正在创建admin用户...")
            
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"✓ 管理员账户已创建")
            print(f"  用户名: admin")
            print(f"  密码: admin123")
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("重置管理员密码")
    print("=" * 50)
    reset_admin_password()
    print("=" * 50)
