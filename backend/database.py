from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

try:
    from backend.config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)

# 数据库引擎配置
# 支持 MySQL: mysql+pymysql://user:password@host:port/database?charset=utf8mb4
# 支持 SQLite: sqlite:///./data/database.db

# 判断数据库类型
is_mysql = 'mysql' in settings.DATABASE_URL.lower()

# 创建引擎
engine_args = {
    'pool_pre_ping': True,      # 连接前检查
    'pool_recycle': 3600,       # 1小时回收连接
    'echo': settings.LOG_LEVEL == "DEBUG",
}

# MySQL特定配置
if is_mysql:
    engine_args.update({
        'pool_size': getattr(settings, 'DB_POOL_SIZE', 10),
        'max_overflow': getattr(settings, 'DB_MAX_OVERFLOW', 20),
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 10,
        }
    })
    logger.info(f"使用MySQL数据库连接池: pool_size={engine_args['pool_size']}, max_overflow={engine_args['max_overflow']}")
else:
    engine_args.update({
        'connect_args': {'check_same_thread': False}  # SQLite
    })
    logger.info("使用SQLite数据库")

engine = create_engine(settings.DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    logger.info("初始化数据库表结构...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表结构初始化完成")
