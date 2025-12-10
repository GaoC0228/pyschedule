#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python包管理工具
支持安装、卸载包，并同步到requirements.txt实现持久化
"""
import subprocess
import logging
import re
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# requirements.txt路径
REQUIREMENTS_FILE = "/app/requirements.txt"


class PackageManager:
    """Python包管理器"""
    
    @staticmethod
    def get_installed_packages(search: str = "") -> List[Dict[str, str]]:
        """获取已安装的包列表
        
        Args:
            search: 搜索关键词（模糊匹配包名）
            
        Returns:
            包列表，每个包包含name和version
        """
        try:
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"获取包列表失败: {result.stderr}")
                return []
            
            import json
            packages = json.loads(result.stdout)
            
            # 过滤搜索
            if search:
                search_lower = search.lower()
                packages = [
                    pkg for pkg in packages
                    if search_lower in pkg['name'].lower()
                ]
            
            return packages
            
        except Exception as e:
            logger.error(f"获取包列表异常: {e}")
            return []
    
    @staticmethod
    def get_package_info(package_name: str) -> Optional[Dict]:
        """获取包详细信息
        
        Args:
            package_name: 包名
            
        Returns:
            包信息字典
        """
        try:
            result = subprocess.run(
                ['pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            
            return info
            
        except Exception as e:
            logger.error(f"获取包信息异常: {e}")
            return None
    
    @staticmethod
    def install_package(package_name: str, version: str = None) -> tuple[bool, str]:
        """安装Python包
        
        Args:
            package_name: 包名
            version: 版本号（可选）
            
        Returns:
            (成功标志, 输出信息)
        """
        try:
            # 构建安装命令
            if version:
                package_spec = f"{package_name}=={version}"
            else:
                package_spec = package_name
            
            result = subprocess.run(
                ['pip', 'install', package_spec, '-i', 'https://mirrors.aliyun.com/pypi/simple/'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # 安装成功，同步到requirements.txt
                PackageManager._sync_to_requirements(package_name, version)
                logger.info(f"包安装成功: {package_spec}")
                return True, result.stdout
            else:
                logger.error(f"包安装失败: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            error_msg = "安装超时（超过5分钟）"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"安装异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def uninstall_package(package_name: str) -> tuple[bool, str]:
        """卸载Python包
        
        Args:
            package_name: 包名
            
        Returns:
            (成功标志, 输出信息)
        """
        try:
            result = subprocess.run(
                ['pip', 'uninstall', package_name, '-y'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # 卸载成功，从requirements.txt移除
                PackageManager._remove_from_requirements(package_name)
                logger.info(f"包卸载成功: {package_name}")
                return True, result.stdout
            else:
                logger.error(f"包卸载失败: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            error_msg = f"卸载异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def _sync_to_requirements(package_name: str, version: str = None):
        """将包同步到requirements.txt
        
        Args:
            package_name: 包名
            version: 版本号（如果为None则获取当前安装的版本）
        """
        try:
            # 读取现有requirements.txt
            requirements_path = Path(REQUIREMENTS_FILE)
            if requirements_path.exists():
                lines = requirements_path.read_text().split('\n')
            else:
                lines = []
            
            # 获取当前安装的版本
            if version is None:
                info = PackageManager.get_package_info(package_name)
                if info and 'Version' in info:
                    version = info['Version']
            
            # 构建包规范
            package_spec = f"{package_name}=={version}" if version else package_name
            
            # 移除旧的包记录（不区分大小写）
            pattern = re.compile(f"^{re.escape(package_name)}(==|>=|<=|~=|!=|>|<)", re.IGNORECASE)
            lines = [line for line in lines if not pattern.match(line.strip())]
            
            # 添加新包（插入到合适位置，保持有序）
            # 跳过注释和空行，找到合适的插入位置
            insert_pos = len(lines)
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    insert_pos = i
                    break
            
            # 在最后一个非注释行之后插入
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() and not lines[i].strip().startswith('#'):
                    insert_pos = i + 1
                    break
            
            lines.insert(insert_pos, package_spec)
            
            # 写回文件
            requirements_path.write_text('\n'.join(lines))
            logger.info(f"已同步到requirements.txt: {package_spec}")
            
        except Exception as e:
            logger.error(f"同步到requirements.txt失败: {e}")
    
    @staticmethod
    def _remove_from_requirements(package_name: str):
        """从requirements.txt移除包
        
        Args:
            package_name: 包名
        """
        try:
            requirements_path = Path(REQUIREMENTS_FILE)
            if not requirements_path.exists():
                return
            
            lines = requirements_path.read_text().split('\n')
            
            # 移除包记录（不区分大小写）
            pattern = re.compile(f"^{re.escape(package_name)}(==|>=|<=|~=|!=|>|<|$)", re.IGNORECASE)
            lines = [line for line in lines if not pattern.match(line.strip())]
            
            # 写回文件
            requirements_path.write_text('\n'.join(lines))
            logger.info(f"已从requirements.txt移除: {package_name}")
            
        except Exception as e:
            logger.error(f"从requirements.txt移除失败: {e}")
    
    @staticmethod
    def batch_install(packages: List[str]) -> tuple[bool, List[Dict]]:
        """批量安装包
        
        Args:
            packages: 包名列表（可包含版本，如 "pandas==2.0.3"）
            
        Returns:
            (是否全部成功, 安装结果列表)
        """
        results = []
        all_success = True
        
        for package in packages:
            # 解析包名和版本
            if '==' in package:
                name, version = package.split('==', 1)
            else:
                name = package
                version = None
            
            success, output = PackageManager.install_package(name, version)
            results.append({
                'package': package,
                'success': success,
                'output': output
            })
            
            if not success:
                all_success = False
        
        return all_success, results


# 全局包管理器实例
package_manager = PackageManager()
