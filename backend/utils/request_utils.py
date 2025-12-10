"""
请求工具函数
用于获取客户端真实IP等信息
"""
from fastapi import Request
from typing import Optional


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址
    
    优先级：
    1. X-Real-IP (最直接的真实IP)
    2. X-Forwarded-For (第一个IP为真实IP)
    3. request.client.host (直接连接IP，可能是代理IP)
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        客户端真实IP地址
    """
    # 方式1: X-Real-IP (Nginx设置的真实IP)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 方式2: X-Forwarded-For (代理链中的第一个IP)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For格式: client, proxy1, proxy2
        # 取第一个IP（客户端真实IP）
        return forwarded_for.split(",")[0].strip()
    
    # 方式3: 直接连接IP（没有代理时）
    if request.client:
        return request.client.host
    
    return "unknown"


def get_request_info(request: Request) -> dict:
    """
    获取请求详细信息
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        包含请求信息的字典
    """
    return {
        "client_ip": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "headers": dict(request.headers),
        "x_real_ip": request.headers.get("X-Real-IP"),
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
    }


def get_user_agent(request: Request) -> str:
    """获取用户代理信息"""
    return request.headers.get("User-Agent", "unknown")


def get_referer(request: Request) -> Optional[str]:
    """获取来源页面"""
    return request.headers.get("Referer")


def is_https(request: Request) -> bool:
    """判断是否是HTTPS请求"""
    # 检查X-Forwarded-Proto头
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_proto:
        return forwarded_proto.lower() == "https"
    
    # 检查URL scheme
    return request.url.scheme == "https"
