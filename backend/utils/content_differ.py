#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件内容差异对比工具
用于审计日志的文件变更追踪
"""
import difflib
from typing import Tuple, List, Dict
import hashlib


class ContentDiffer:
    """文件内容差异对比工具"""
    
    def __init__(self, max_content_size: int = 1024 * 100):  # 默认100KB
        """
        初始化
        
        Args:
            max_content_size: 最大内容大小（字节），超过此大小不保存完整内容
        """
        self.max_content_size = max_content_size
    
    def should_save_content(self, content: str) -> bool:
        """
        判断是否应该保存完整内容
        
        Args:
            content: 文件内容
            
        Returns:
            是否保存
        """
        return len(content.encode('utf-8')) <= self.max_content_size
    
    def calculate_hash(self, content: str) -> str:
        """
        计算内容哈希
        
        Args:
            content: 文件内容
            
        Returns:
            SHA256哈希值
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def generate_diff(self, content_before: str, content_after: str) -> Tuple[str, int, int]:
        """
        生成内容差异
        
        Args:
            content_before: 修改前的内容
            content_after: 修改后的内容
            
        Returns:
            (diff文本, 新增行数, 删除行数)
        """
        lines_before = content_before.splitlines(keepends=True)
        lines_after = content_after.splitlines(keepends=True)
        
        # 生成unified diff
        diff = difflib.unified_diff(
            lines_before,
            lines_after,
            fromfile='修改前',
            tofile='修改后',
            lineterm=''
        )
        
        diff_text = '\n'.join(diff)
        
        # 统计新增和删除的行数
        lines_added = 0
        lines_deleted = 0
        
        for line in diff_text.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                lines_deleted += 1
        
        return diff_text, lines_added, lines_deleted
    
    def generate_html_diff(self, content_before: str, content_after: str) -> str:
        """
        生成HTML格式的差异对比（适合网页显示）
        
        Args:
            content_before: 修改前的内容
            content_after: 修改后的内容
            
        Returns:
            HTML格式的差异
        """
        lines_before = content_before.splitlines()
        lines_after = content_after.splitlines()
        
        html_diff = difflib.HtmlDiff(wrapcolumn=80)
        return html_diff.make_table(
            lines_before,
            lines_after,
            fromdesc='修改前',
            todesc='修改后',
            context=True,
            numlines=3
        )
    
    def get_change_summary(self, content_before: str, content_after: str) -> Dict:
        """
        获取变更摘要
        
        Args:
            content_before: 修改前的内容
            content_after: 修改后的内容
            
        Returns:
            变更摘要字典
        """
        diff_text, lines_added, lines_deleted = self.generate_diff(content_before, content_after)
        
        return {
            "size_before": len(content_before),
            "size_after": len(content_after),
            "size_change": len(content_after) - len(content_before),
            "lines_before": len(content_before.splitlines()),
            "lines_after": len(content_after.splitlines()),
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "lines_changed": lines_added + lines_deleted,
            "hash_before": self.calculate_hash(content_before),
            "hash_after": self.calculate_hash(content_after),
            "has_changes": content_before != content_after
        }
    
    def format_diff_for_display(self, diff_text: str) -> List[Dict]:
        """
        格式化diff文本用于前端显示
        
        Args:
            diff_text: unified diff文本
            
        Returns:
            格式化后的差异列表
        """
        lines = diff_text.split('\n')
        result = []
        
        for line in lines:
            if not line:
                continue
                
            if line.startswith('+++') or line.startswith('---'):
                continue
            elif line.startswith('@@'):
                # 行号信息
                result.append({
                    "type": "info",
                    "content": line,
                    "line_number": None
                })
            elif line.startswith('+'):
                # 新增的行
                result.append({
                    "type": "added",
                    "content": line[1:],
                    "prefix": "+"
                })
            elif line.startswith('-'):
                # 删除的行
                result.append({
                    "type": "deleted",
                    "content": line[1:],
                    "prefix": "-"
                })
            else:
                # 未改变的行
                result.append({
                    "type": "unchanged",
                    "content": line[1:] if line.startswith(' ') else line,
                    "prefix": " "
                })
        
        return result


# 全局实例
content_differ = ContentDiffer()
