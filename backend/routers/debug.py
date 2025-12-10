"""
调试路由
用于测试获取真实IP等信息
"""
from fastapi import APIRouter, Request, Depends
from typing import Dict, Any
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.request_utils import get_client_ip, get_request_info
except ImportError:
    # 兼容不同的导入方式
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "request_utils",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "request_utils.py")
    )
    if spec and spec.loader:
        request_utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(request_utils)
        get_client_ip = request_utils.get_client_ip
        get_request_info = request_utils.get_request_info

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/ip")
async def get_ip_info(request: Request) -> Dict[str, Any]:
    """
    获取客户端IP信息（调试用）
    
    Returns:
        客户端IP和相关信息
    """
    return {
        "client_ip": get_client_ip(request),
        "x_real_ip": request.headers.get("X-Real-IP"),
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
        "direct_client": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
    }


@router.get("/request")
async def get_full_request_info(request: Request) -> Dict[str, Any]:
    """
    获取完整请求信息（调试用）
    
    Returns:
        完整的请求信息
    """
    return get_request_info(request)


@router.get("/headers")
async def get_all_headers(request: Request) -> Dict[str, str]:
    """
    获取所有请求头（调试用）
    
    Returns:
        所有HTTP请求头
    """
    return dict(request.headers)
