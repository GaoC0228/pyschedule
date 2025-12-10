#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库配置动态模块
自动为每个数据库配置生成对应的Python模块

使用方法：
    from db_configs import mongo_test as mongos
    client = mongos.mongo_connect()
    
注意：此模块会自动设置Python路径，无需在脚本中手动添加sys.path
"""

import sys
import os

# 自动添加backend目录到sys.path（固定路径）
_backend_dir = '/opt/soft/exec_python_web/v1/backend'
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient

try:
    from backend.models import DatabaseConfig
    from backend.utils.crypto import decrypt_password
    from backend.config import settings
except ImportError:
    from models import DatabaseConfig
    from utils.crypto import decrypt_password
    from config import settings

# 创建数据库会话
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def __getattr__(name):
    """
    动态导入：import mongo_test 会自动调用这个函数
    name 就是 'mongo_test'
    """
    # 从数据库获取配置
    db = SessionLocal()
    try:
        config = db.query(DatabaseConfig).filter(
            DatabaseConfig.name == name,
            DatabaseConfig.is_active == True
        ).first()
        
        if not config:
            raise ImportError(f"数据库配置不存在或未启用: {name}")
        
        # 解密密码
        password = None
        if config.password:
            password = decrypt_password(config.password)
        
        # 创建一个模块对象
        import types
        module = types.ModuleType(name)
        
        # 连接MongoDB
        if config.connection_string:
            client = MongoClient(config.connection_string)
        else:
            uri = f"mongodb://{config.username}:{password}@{config.host}"
            if config.port:
                uri += f":{config.port}"
            if config.database:
                uri += f"/{config.database}"
            if config.auth_source:
                uri += f"?authSource={config.auth_source}"
            if config.replica_set:
                if '?' in uri:
                    uri += f"&replicaSet={config.replica_set}"
                else:
                    uri += f"?replicaSet={config.replica_set}"
            
            client = MongoClient(uri)
        
        # 添加属性到模块
        module.client = client
        module.mongo_connect = lambda: client
        
        # 缓存模块
        sys.modules[f'db_configs.{name}'] = module
        
        return module
        
    finally:
        db.close()
