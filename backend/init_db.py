"""初始化数据库脚本"""
from database import engine, Base, SessionLocal
from models import User, DatabaseConfig  # 导入所有模型
from auth import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已创建")
    
    # 创建默认管理员账户
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
            db.commit()
            logger.info("默认管理员账户已创建: username=admin, password=admin123")
        else:
            logger.info("管理员账户已存在")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
