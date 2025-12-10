#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库配置相关的Pydantic模型（避免与现有 schemas.py 冲突）
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DatabaseConfigBase(BaseModel):
    name: str = Field(..., description="配置名称（唯一标识）", min_length=1, max_length=100)
    display_name: str = Field(..., description="显示名称", min_length=1, max_length=100)
    db_type: str = Field(..., description="数据库类型", pattern="^(mongodb|mysql|postgresql|redis)$")
    environment: str = Field(..., description="环境", pattern="^(production|test|dev)$")

    host: Optional[str] = Field(None, description="主机地址", max_length=255)
    port: Optional[int] = Field(None, description="端口", ge=1, le=65535)
    username: Optional[str] = Field(None, description="用户名", max_length=100)
    password: Optional[str] = Field(None, description="密码", max_length=255)
    database: Optional[str] = Field(None, description="数据库名", max_length=100)

    # MongoDB特有
    connection_string: Optional[str] = Field(None, description="MongoDB完整连接字符串", max_length=500)
    replica_set: Optional[str] = Field(None, description="副本集名称", max_length=100)
    auth_source: Optional[str] = Field(None, description="认证数据库", max_length=100)

    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否启用")
    is_public: bool = Field(False, description="是否公开（所有用户可见）")


class DatabaseConfigCreate(DatabaseConfigBase):
    pass


class DatabaseConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    db_type: Optional[str] = None
    environment: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    connection_string: Optional[str] = None
    replica_set: Optional[str] = None
    auth_source: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class DatabaseConfigResponse(DatabaseConfigBase):
    id: int
    password: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str] = None  # 创建者用户名

    class Config:
        from_attributes = True

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        if data.get('password'):
            data['password'] = '******'
        return data


class DatabaseConfigTestRequest(BaseModel):
    config_name: str = Field(..., description="配置名称")


class DatabaseConfigTestResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None
