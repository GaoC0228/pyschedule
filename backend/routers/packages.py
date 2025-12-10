#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python包管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models import User
from auth import get_current_user
from utils.package_manager import package_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/packages", tags=["packages"])


# ==================== Pydantic模型 ====================

class PackageInstallRequest(BaseModel):
    """安装包请求"""
    package_name: str
    version: Optional[str] = None


class PackageUninstallRequest(BaseModel):
    """卸载包请求"""
    package_name: str


class BatchInstallRequest(BaseModel):
    """批量安装请求"""
    packages: List[str]  # 包名列表，如 ["pandas", "numpy==1.24.3"]


# ==================== 权限检查 ====================

def check_package_permission(current_user: User):
    """检查用户是否有包管理权限"""
    if current_user.role != "admin" and not current_user.can_manage_packages:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有包管理权限"
        )


# ==================== API路由 ====================

@router.get("/installed")
def get_installed_packages(
    search: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取已安装的包列表"""
    check_package_permission(current_user)
    
    try:
        packages = package_manager.get_installed_packages(search=search)
        return {
            "success": True,
            "data": packages,
            "total": len(packages)
        }
    except Exception as e:
        logger.error(f"获取包列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取包列表失败: {str(e)}")


@router.get("/info/{package_name}")
def get_package_info(
    package_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取包详细信息"""
    check_package_permission(current_user)
    
    try:
        info = package_manager.get_package_info(package_name)
        if not info:
            raise HTTPException(status_code=404, detail="包不存在或未安装")
        
        return {
            "success": True,
            "data": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取包信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取包信息失败: {str(e)}")


@router.post("/install")
def install_package(
    request: PackageInstallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """安装Python包"""
    check_package_permission(current_user)
    
    try:
        success, output = package_manager.install_package(
            request.package_name,
            request.version
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 安装了包: {request.package_name}")
            return {
                "success": True,
                "message": "安装成功",
                "output": output
            }
        else:
            return {
                "success": False,
                "message": "安装失败",
                "output": output
            }
            
    except Exception as e:
        logger.error(f"安装包异常: {e}")
        raise HTTPException(status_code=500, detail=f"安装包异常: {str(e)}")


@router.post("/uninstall")
def uninstall_package(
    request: PackageUninstallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """卸载Python包"""
    check_package_permission(current_user)
    
    # 防止卸载关键包
    critical_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pymysql', 'pydantic',
        'python-jose', 'passlib', 'bcrypt', 'APScheduler', 'pip', 'setuptools'
    ]
    
    if request.package_name.lower() in [pkg.lower() for pkg in critical_packages]:
        raise HTTPException(
            status_code=400,
            detail=f"不允许卸载关键包: {request.package_name}"
        )
    
    try:
        success, output = package_manager.uninstall_package(request.package_name)
        
        if success:
            logger.info(f"用户 {current_user.username} 卸载了包: {request.package_name}")
            return {
                "success": True,
                "message": "卸载成功",
                "output": output
            }
        else:
            return {
                "success": False,
                "message": "卸载失败",
                "output": output
            }
            
    except Exception as e:
        logger.error(f"卸载包异常: {e}")
        raise HTTPException(status_code=500, detail=f"卸载包异常: {str(e)}")


@router.post("/batch-install")
def batch_install(
    request: BatchInstallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量安装包"""
    check_package_permission(current_user)
    
    if not request.packages:
        raise HTTPException(status_code=400, detail="包列表不能为空")
    
    try:
        all_success, results = package_manager.batch_install(request.packages)
        
        logger.info(f"用户 {current_user.username} 批量安装了 {len(request.packages)} 个包")
        
        return {
            "success": all_success,
            "message": "批量安装完成" if all_success else "部分安装失败",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量安装异常: {e}")
        raise HTTPException(status_code=500, detail=f"批量安装异常: {str(e)}")
