#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脚本安全分析工具
"""
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import DatabaseConfig


class ScriptAnalyzer:
    """脚本安全分析器"""
    
    # 危险操作关键词
    DANGEROUS_OPERATIONS = {
        'delete': ['delete', 'delete_many', 'delete_one', 'remove'],
        'drop': ['drop', 'drop_database', 'drop_collection'],
        'update': ['update', 'update_many', 'update_one', 'replace_one'],
        'truncate': ['truncate'],
        'insert': ['insert', 'insert_many', 'insert_one']
    }
    
    @staticmethod
    def analyze_script(script_content: str, db: Session) -> Dict[str, Any]:
        """
        分析脚本安全风险
        
        Args:
            script_content: 脚本内容
            db: 数据库会话
            
        Returns:
            {
                'has_risk': bool,  # 是否有风险
                'risk_level': str,  # 风险等级: low/medium/high
                'database_configs': List[Dict],  # 使用的数据库配置
                'dangerous_operations': List[str],  # 危险操作列表
                'warnings': List[str]  # 警告信息
            }
        """
        result = {
            'has_risk': False,
            'risk_level': 'low',
            'database_configs': [],
            'dangerous_operations': [],
            'warnings': []
        }
        
        # 1. 检测使用的数据库配置
        db_configs = ScriptAnalyzer._detect_database_configs(script_content, db)
        result['database_configs'] = db_configs
        
        # 2. 检查是否使用生产环境数据库
        production_dbs = [cfg for cfg in db_configs if cfg.get('environment') == 'production']
        if production_dbs:
            result['has_risk'] = True
            result['risk_level'] = 'high'
            for cfg in production_dbs:
                result['warnings'].append(
                    f"⚠️ 脚本将连接生产环境数据库: {cfg['display_name']} ({cfg['db_type']})"
                )
        
        # 3. 检测危险操作
        dangerous_ops = ScriptAnalyzer._detect_dangerous_operations(script_content)
        result['dangerous_operations'] = dangerous_ops
        
        if dangerous_ops:
            result['has_risk'] = True
            if result['risk_level'] == 'low':
                result['risk_level'] = 'medium'
            
            # 如果既有生产环境又有危险操作，风险极高
            if production_dbs and dangerous_ops:
                result['risk_level'] = 'critical'
                result['warnings'].append(
                    f"🚨 严重警告: 脚本将在生产环境执行危险操作: {', '.join(dangerous_ops)}"
                )
            else:
                result['warnings'].append(
                    f"⚠️ 检测到危险操作: {', '.join(dangerous_ops)}"
                )
        
        return result
    
    @staticmethod
    def _detect_database_configs(script_content: str, db: Session) -> List[Dict[str, Any]]:
        """检测脚本中使用的数据库配置"""
        configs = []
        
        # 匹配 from db_configs import xxx 模式
        pattern = r'from\s+db_configs\s+import\s+(\w+)'
        matches = re.findall(pattern, script_content)
        
        for config_name in matches:
            # 从数据库查询配置信息
            db_config = db.query(DatabaseConfig).filter(
                DatabaseConfig.name == config_name
            ).first()
            
            if db_config:
                configs.append({
                    'name': db_config.name,
                    'display_name': db_config.display_name,
                    'db_type': db_config.db_type,
                    'environment': db_config.environment,
                    'host': db_config.host or '连接字符串',
                    'database': db_config.database
                })
        
        return configs
    
    @staticmethod
    def _detect_dangerous_operations(script_content: str) -> List[str]:
        """检测危险操作"""
        found_operations = []
        
        # 转换为小写便于匹配
        content_lower = script_content.lower()
        
        for op_type, keywords in ScriptAnalyzer.DANGEROUS_OPERATIONS.items():
            for keyword in keywords:
                # 匹配函数调用模式: .keyword( 或 keyword(
                pattern = rf'[\.\s]{keyword}\s*\('
                if re.search(pattern, content_lower):
                    if op_type not in found_operations:
                        found_operations.append(op_type.upper())
                    break
        
        return found_operations
