#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库配置管理API
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from models import User, DatabaseConfig
from db_schemas import (
    DatabaseConfigCreate,
    DatabaseConfigUpdate,
    DatabaseConfigResponse,
    DatabaseConfigTestRequest,
    DatabaseConfigTestResponse
)
from auth import get_current_user
from audit import AuditAction, ResourceType, create_audit_log
from utils.crypto import encrypt_password, decrypt_password
from utils.ip_utils import get_real_ip

# 测试连接用的库
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, OperationFailure
except ImportError:
    MongoClient = None

try:
    import pymysql
except ImportError:
    pymysql = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/database-configs", tags=["数据库配置"])


@router.get("", response_model=List[DatabaseConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据库配置列表（带权限控制）"""
    query = db.query(DatabaseConfig)
    
    # 普通用户只能看到自己创建的和公开的配置
    # 管理员可以看到所有配置
    if current_user.role != "admin":
        query = query.filter(
            (DatabaseConfig.created_by == current_user.username) | 
            (DatabaseConfig.is_public == True)
        )
    
    configs = query.order_by(DatabaseConfig.created_at.desc()).all()
    return configs


@router.get("/{config_name}", response_model=DatabaseConfigResponse)
def get_config(
    config_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定数据库配置（带权限控制）"""
    config = db.query(DatabaseConfig).filter(DatabaseConfig.name == config_name).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 权限检查：普通用户只能查看自己创建的或公开的配置
    if current_user.role != "admin":
        if config.created_by != current_user.username and not config.is_public:
            raise HTTPException(status_code=403, detail="无权限访问此配置")
    
    return config


@router.post("", response_model=DatabaseConfigResponse)
def create_config(
    config: DatabaseConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的数据库配置"""
    # 检查名称是否已存在
    existing = db.query(DatabaseConfig).filter(DatabaseConfig.name == config.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")
    
    # 加密密码
    encrypted_password = None
    if config.password:
        encrypted_password = encrypt_password(config.password)
    
    # 创建配置
    db_config = DatabaseConfig(
        name=config.name,
        display_name=config.display_name,
        db_type=config.db_type,
        environment=config.environment,
        host=config.host,
        port=config.port,
        username=config.username,
        password=encrypted_password,
        database=config.database,
        connection_string=config.connection_string,
        replica_set=config.replica_set,
        auth_source=config.auth_source,
        description=config.description,
        is_active=config.is_active,
        is_public=config.is_public,
        created_by=current_user.username  # 记录创建者用户名
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.CONFIG_CREATE,
        resource_type=ResourceType.CONFIG,
        resource_id=db_config.id,
        status="success",
        details={"config_name": db_config.name, "db_type": db_config.db_type},
        ip_address=get_real_ip(request)
    )
    
    logger.info(f"用户 {current_user.username} 创建数据库配置: {config.name}")
    
    return db_config


@router.put("/{config_name}", response_model=DatabaseConfigResponse)
def update_config(
    config_name: str,
    config: DatabaseConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据库配置（带权限控制）"""
    db_config = db.query(DatabaseConfig).filter(DatabaseConfig.name == config_name).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 权限检查：只有创建者或管理员可以修改
    if current_user.role != "admin" and db_config.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="无权限修改此配置")
    
    # 更新字段，记录修改前后的值
    update_data = config.dict(exclude_unset=True)
    
    # 记录修改前的值（用于审计日志）
    field_mapping = {
        'display_name': '显示名称',
        'db_type': '数据库类型',
        'environment': '环境',
        'host': '主机地址',
        'port': '端口',
        'username': '用户名',
        'password': '密码',
        'database': '数据库名',
        'connection_string': '连接字符串',
        'replica_set': '副本集',
        'auth_source': '认证源',
        'description': '描述',
        'is_active': '是否启用',
        'is_public': '是否公开'
    }
    
    changes = {}
    for field, new_value in update_data.items():
        old_value = getattr(db_config, field, None)
        
        # 密码字段特殊处理
        if field == 'password':
            if new_value:  # 只在密码有更新时记录
                changes[field_mapping.get(field, field)] = {
                    'old': '******',
                    'new': '******'
                }
                update_data['password'] = encrypt_password(new_value)
        else:
            # 只记录真正变化的字段
            if old_value != new_value:
                changes[field_mapping.get(field, field)] = {
                    'old': str(old_value) if old_value is not None else '',
                    'new': str(new_value) if new_value is not None else ''
                }
    
    # 应用更新
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.CONFIG_UPDATE,
        resource_type=ResourceType.CONFIG,
        resource_id=db_config.id,
        status="success",
        details={
            "config_name": config_name,
            "db_type": db_config.db_type,
            "changes": changes
        },
        ip_address=get_real_ip(request)
    )
    
    logger.info(f"用户 {current_user.username} 更新数据库配置: {config_name}")
    
    return db_config


@router.delete("/{config_name}")
def delete_config(
    config_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据库配置（带权限控制）"""
    db_config = db.query(DatabaseConfig).filter(DatabaseConfig.name == config_name).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 权限检查：只有创建者或管理员可以删除
    if current_user.role != "admin" and db_config.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="无权限删除此配置")
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.CONFIG_DELETE,
        resource_type=ResourceType.CONFIG,
        resource_id=db_config.id,
        status="success",
        details={"config_name": config_name, "db_type": db_config.db_type},
        ip_address=get_real_ip(request)
    )
    
    db.delete(db_config)
    db.commit()
    
    logger.info(f"用户 {current_user.username} 删除数据库配置: {config_name}")
    
    return {"message": "删除成功"}


@router.post("/test-direct", response_model=DatabaseConfigTestResponse)
def test_connection_direct(
    config_data: DatabaseConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """直接测试数据库连接（不需要先保存配置）"""
    # 创建临时配置对象用于测试
    from models import DatabaseConfig as DBConfigModel
    temp_config = DBConfigModel(**config_data.dict())
    
    # 密码不需要解密（前端传的是明文）
    password = config_data.password
    
    try:
        if config_data.db_type == "mongodb":
            return test_mongodb_connection(temp_config, password)
        elif config_data.db_type == "mysql":
            return test_mysql_connection(temp_config, password)
        elif config_data.db_type == "postgresql":
            return test_postgresql_connection(temp_config, password)
        elif config_data.db_type == "redis":
            return test_redis_connection(temp_config, password)
        else:
            return DatabaseConfigTestResponse(
                success=False,
                message=f"不支持的数据库类型: {config_data.db_type}"
            )
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}", exc_info=True)
        return DatabaseConfigTestResponse(
            success=False,
            message=f"测试失败: {str(e)}"
        )


@router.post("/test", response_model=DatabaseConfigTestResponse)
def test_connection(
    test_request: DatabaseConfigTestRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试数据库连接（已保存的配置）"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.name == test_request.config_name
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 解密密码
    password = None
    if config.password:
        password = decrypt_password(config.password)
    
    result = None
    try:
        if config.db_type == "mongodb":
            result = test_mongodb_connection(config, password)
        elif config.db_type == "mysql":
            result = test_mysql_connection(config, password)
        elif config.db_type == "postgresql":
            result = test_postgresql_connection(config, password)
        elif config.db_type == "redis":
            result = test_redis_connection(config, password)
        else:
            result = DatabaseConfigTestResponse(
                success=False,
                message=f"不支持的数据库类型: {config.db_type}"
            )
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.CONFIG_TEST,
            resource_type=ResourceType.CONFIG,
            status="success" if result.success else "failed",
            details={
                "config_name": config.name,
                "db_type": config.db_type,
                "test_result": "成功" if result.success else "失败",
                "message": result.message
            },
            ip_address=get_real_ip(request)
        )
        
        return result
    except Exception as e:
        logger.error(f"测试数据库连接失败: {str(e)}")
        
        # 记录失败的审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.CONFIG_TEST,
            resource_type=ResourceType.CONFIG,
            status="failed",
            details={
                "config_name": config.name,
                "db_type": config.db_type,
                "error": str(e)
            },
            ip_address=get_real_ip(request)
        )
        
        return DatabaseConfigTestResponse(
            success=False,
            message=f"连接失败: {str(e)}"
        )


def test_mongodb_connection(config: DatabaseConfig, password: str) -> DatabaseConfigTestResponse:
    """测试MongoDB连接"""
    if not MongoClient:
        return DatabaseConfigTestResponse(
            success=False,
            message="pymongo库未安装，请先安装: pip install pymongo"
        )
    
    try:
        # 使用连接字符串或构建连接
        if config.connection_string:
            client = MongoClient(config.connection_string, serverSelectionTimeoutMS=5000)
        else:
            uri = f"mongodb://{config.username}:{password}@{config.host}"
            if config.port:
                uri += f":{config.port}"
            if config.database:
                uri += f"/{config.database}"
            if config.auth_source:
                uri += f"?authSource={config.auth_source}"
            if config.replica_set:
                uri += f"&replicaSet={config.replica_set}"
            
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        client.admin.command('ping')
        
        # 获取数据库信息
        db_list = client.list_database_names()
        
        return DatabaseConfigTestResponse(
            success=True,
            message="MongoDB连接成功",
            details={
                "databases": db_list,
                "server_info": client.server_info().get('version', 'unknown')
            }
        )
    except ConnectionFailure as e:
        error_msg = str(e)
        if "timed out" in error_msg.lower():
            error_msg = f"连接超时，请检查主机地址和端口是否正确，以及网络是否可达。详细错误: {error_msg}"
        elif "connection refused" in error_msg.lower():
            error_msg = f"连接被拒绝，请检查MongoDB服务是否正在运行。详细错误: {error_msg}"
        return DatabaseConfigTestResponse(
            success=False,
            message=f"MongoDB连接失败: {error_msg}"
        )
    except OperationFailure as e:
        error_msg = str(e)
        if "authentication failed" in error_msg.lower() or "auth failed" in error_msg.lower():
            error_msg = f"用户名或密码错误，请检查认证信息。详细错误: {error_msg}"
        return DatabaseConfigTestResponse(
            success=False,
            message=f"MongoDB认证失败: {error_msg}"
        )
    except Exception as e:
        return DatabaseConfigTestResponse(
            success=False,
            message=f"MongoDB连接错误: {str(e)}"
        )


def test_mysql_connection(config: DatabaseConfig, password: str) -> DatabaseConfigTestResponse:
    """测试MySQL连接"""
    if not pymysql:
        return DatabaseConfigTestResponse(
            success=False,
            message="pymysql库未安装，请先安装: pip install pymysql"
        )
    
    try:
        connection = pymysql.connect(
            host=config.host,
            port=config.port or 3306,
            user=config.username,
            password=password,
            database=config.database,
            connect_timeout=5
        )
        
        with connection.cursor() as cursor:
            # 获取版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # 获取数据库列表
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]
            
            # 获取当前数据库
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
        
        connection.close()
        
        return DatabaseConfigTestResponse(
            success=True,
            message="MySQL连接成功",
            details={
                "version": version,
                "current_database": current_db,
                "databases": databases[:10]  # 只显示前10个
            }
        )
    except Exception as e:
        error_msg = str(e)
        if "Access denied" in error_msg:
            error_msg = f"用户名或密码错误。详细错误: {error_msg}"
        elif "Can't connect" in error_msg or "timed out" in error_msg.lower():
            error_msg = f"无法连接到MySQL服务器，请检查主机地址和端口。详细错误: {error_msg}"
        elif "Unknown database" in error_msg:
            error_msg = f"数据库不存在，请检查数据库名称。详细错误: {error_msg}"
        return DatabaseConfigTestResponse(
            success=False,
            message=f"MySQL连接失败: {error_msg}"
        )


def test_postgresql_connection(config: DatabaseConfig, password: str) -> DatabaseConfigTestResponse:
    """测试PostgreSQL连接"""
    if not psycopg2:
        return DatabaseConfigTestResponse(
            success=False,
            message="psycopg2库未安装，请先安装: pip install psycopg2-binary"
        )
    
    try:
        connection = psycopg2.connect(
            host=config.host,
            port=config.port or 5432,
            user=config.username,
            password=password,
            database=config.database,
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        # 获取版本
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # 获取当前数据库
        cursor.execute("SELECT current_database()")
        current_db = cursor.fetchone()[0]
        
        # 获取数据库列表
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return DatabaseConfigTestResponse(
            success=True,
            message="PostgreSQL连接成功",
            details={
                "version": version.split(',')[0],  # 只显示版本号
                "current_database": current_db,
                "databases": databases
            }
        )
    except Exception as e:
        error_msg = str(e)
        if "authentication failed" in error_msg.lower() or "password authentication failed" in error_msg.lower():
            error_msg = f"用户名或密码错误。详细错误: {error_msg}"
        elif "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
            error_msg = f"无法连接到PostgreSQL服务器。详细错误: {error_msg}"
        elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            error_msg = f"数据库不存在。详细错误: {error_msg}"
        return DatabaseConfigTestResponse(
            success=False,
            message=f"PostgreSQL连接失败: {error_msg}"
        )


def test_redis_connection(config: DatabaseConfig, password: str) -> DatabaseConfigTestResponse:
    """测试Redis连接"""
    if not redis:
        return DatabaseConfigTestResponse(
            success=False,
            message="redis库未安装，请先安装: pip install redis"
        )
    
    try:
        r = redis.Redis(
            host=config.host,
            port=config.port or 6379,
            password=password,
            db=int(config.database) if config.database else 0,
            socket_connect_timeout=5
        )
        
        r.ping()
        info = r.info()
        
        return DatabaseConfigTestResponse(
            success=True,
            message="Redis连接成功",
            details={
                "version": info.get('redis_version', 'unknown'),
                "mode": info.get('redis_mode', 'standalone'),
                "used_memory": info.get('used_memory_human', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "db_keys": r.dbsize()
            }
        )
    except Exception as e:
        error_msg = str(e)
        if "NOAUTH" in error_msg or "authentication" in error_msg.lower():
            error_msg = f"认证失败，请检查密码。详细错误: {error_msg}"
        elif "Connection refused" in error_msg or "timed out" in error_msg.lower():
            error_msg = f"无法连接到Redis服务器。详细错误: {error_msg}"
        return DatabaseConfigTestResponse(
            success=False,
            message=f"Redis连接失败: {error_msg}"
        )
