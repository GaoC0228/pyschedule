#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IP地址工具模块
用于获取客户端真实IP地址
"""
from fastapi import Request
from typing import Optional


def get_real_ip(request: Request) -> str:
    """
    获取客户端真实IP地址
    
    优先级：
    1. X-Forwarded-For (第一个IP)
    2. X-Real-IP
    3. request.client.host
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        客户端真实IP地址
    """
    # 1. 尝试从 X-Forwarded-For 获取（支持代理链）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个IP，格式: client, proxy1, proxy2
        # 取第一个IP作为客户端真实IP
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    
    # 2. 尝试从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 3. 降级使用直接连接的客户端IP
    if request.client and request.client.host:
        return request.client.host
    
    # 4. 默认返回未知
    return "unknown"


def is_local_ip(ip: str) -> bool:
    """
    判断是否是本地IP地址
    
    Args:
        ip: IP地址字符串
    
    Returns:
        是否是本地IP
    """
    local_ips = ["127.0.0.1", "localhost", "::1", "0.0.0.0"]
    return ip in local_ips or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")
