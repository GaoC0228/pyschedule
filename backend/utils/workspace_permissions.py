#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工作区权限管理工具
"""
import os
from typing import Tuple
from fastapi import HTTPException
from models import User


class WorkspacePermissions:
    """工作区权限管理"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.shared_dir = "shared"
    
    def get_user_workspace_dir(self, username: str) -> str:
        """
        获取用户工作目录路径
        
        Args:
            username: 用户名
            
        Returns:
            用户工作目录的绝对路径
        """
        return os.path.join(self.workspace_root, username)
    
    def get_shared_workspace_dir(self) -> str:
        """
        获取共享工作目录路径
        
        Returns:
            共享工作目录的绝对路径
        """
        return os.path.join(self.workspace_root, self.shared_dir)
    
    def ensure_user_workspace(self, username: str):
        """
        确保用户工作目录存在
        
        Args:
            username: 用户名
        """
        user_dir = self.get_user_workspace_dir(username)
        os.makedirs(user_dir, exist_ok=True)
    
    def ensure_shared_workspace(self):
        """确保共享工作目录存在"""
        shared_dir = self.get_shared_workspace_dir()
        os.makedirs(shared_dir, exist_ok=True)
    
    def get_accessible_path(self, current_user: User, relative_path: str = "") -> Tuple[str, str]:
        """
        获取用户可访问的完整路径
        
        Args:
            current_user: 当前用户
            relative_path: 相对路径（可以为空，表示根目录）
            
        Returns:
            (完整路径, 显示路径): 完整的文件系统路径和用于显示的路径
            
        Raises:
            HTTPException: 如果路径不可访问
        """
        # 如果是管理员，可以访问所有目录
        if current_user.role == "admin":
            full_path = os.path.join(self.workspace_root, relative_path)
            display_path = relative_path
        else:
            # 普通用户只能访问自己的目录和共享目录
            # 检查是否访问共享目录
            if relative_path.startswith(f"{self.shared_dir}/") or relative_path == self.shared_dir:
                full_path = os.path.join(self.workspace_root, relative_path)
                display_path = relative_path
            else:
                # 访问自己的目录
                # 如果路径为空或者是自己的用户名开头，允许访问
                if not relative_path or relative_path == current_user.username:
                    full_path = os.path.join(self.workspace_root, current_user.username)
                    display_path = current_user.username
                elif relative_path.startswith(f"{current_user.username}/"):
                    full_path = os.path.join(self.workspace_root, relative_path)
                    display_path = relative_path
                else:
                    # 尝试访问其他用户目录，拒绝
                    raise HTTPException(status_code=403, detail="无权限访问此目录")
        
        # 安全检查：确保路径在工作区内
        abs_full_path = os.path.abspath(full_path)
        abs_workspace = os.path.abspath(self.workspace_root)
        if not abs_full_path.startswith(abs_workspace):
            raise HTTPException(status_code=403, detail="非法路径")
        
        return full_path, display_path
    
    def get_root_items(self, current_user: User) -> list:
        """
        获取根目录下用户可见的项目
        
        Args:
            current_user: 当前用户
            
        Returns:
            可见目录列表
        """
        items = []
        
        if current_user.role == "admin":
            # 管理员可以看到所有用户目录和共享目录
            if os.path.exists(self.workspace_root):
                for item in os.listdir(self.workspace_root):
                    item_path = os.path.join(self.workspace_root, item)
                    if os.path.isdir(item_path):
                        items.append(item)
        else:
            # 普通用户只能看到自己的目录和共享目录
            user_dir = current_user.username
            if os.path.exists(os.path.join(self.workspace_root, user_dir)):
                items.append(user_dir)
            
            if os.path.exists(os.path.join(self.workspace_root, self.shared_dir)):
                items.append(self.shared_dir)
        
        return sorted(items)
    
    def check_write_permission(self, current_user: User, relative_path: str):
        """
        检查用户是否有写权限
        
        Args:
            current_user: 当前用户
            relative_path: 相对路径
            
        Raises:
            HTTPException: 如果没有写权限
        """
        # 管理员有所有权限
        if current_user.role == "admin":
            return
        
        # 普通用户可以写自己的目录和共享目录
        if relative_path.startswith(f"{self.shared_dir}/") or relative_path == self.shared_dir:
            return
        
        if relative_path.startswith(f"{current_user.username}/") or relative_path == current_user.username:
            return
        
        raise HTTPException(status_code=403, detail="无权限修改此路径")
