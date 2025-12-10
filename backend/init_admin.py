#!/usr/bin/env python3
"""
初始化管理员账户
在容器首次启动时自动执行
"""
import sys
import logging
from sqlalchemy.orm import Session

try:
    from backend.database import SessionLocal, engine, Base
    from backend.models import User
    from backend.auth import get_password_hash
except ImportError:
    from database import SessionLocal, engine, Base
    from models import User
    from auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_admin():
    """初始化管理员账户"""
    db: Session = SessionLocal()
    try:
        # 检查是否已存在admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if admin_user:
            # 如果存在但不是管理员，升级为管理员
            from models import UserRole
            if admin_user.role != UserRole.ADMIN:
                admin_user.role = UserRole.ADMIN
                db.commit()
                logger.info("✅ 已将现有admin用户升级为管理员")
            else:
                logger.info("✅ 管理员账户已存在，跳过初始化")
            return
        
        # 创建管理员用户
        from models import UserRole
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            role=UserRole.ADMIN  # 设置为管理员角色
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("=" * 60)
        logger.info("✅ 管理员账户初始化成功！")
        logger.info("=" * 60)
        logger.info(f"  用户名: admin")
        logger.info(f"  密码:   admin123")
        logger.info(f"  邮箱:   admin@example.com")
        logger.info(f"  角色:   ADMIN")
        logger.info("=" * 60)
        logger.info("⚠️  请在首次登录后立即修改密码！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 初始化管理员账户失败: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        # 确保数据库表已创建
        Base.metadata.create_all(bind=engine)
        logger.info("📊 数据库表检查完成")
        
        # 初始化管理员
        init_admin()
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        sys.exit(1)
