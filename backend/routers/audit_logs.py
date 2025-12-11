#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计日志API路由
提供审计日志的查询、导出、文件管理等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import AuditLog, AuditLogFile, ScriptExecution, User
from auth import get_current_user, require_admin
from utils.file_archiver import FileArchiver
import io
import csv
import json
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["审计日志"])


# ============== 审计日志列表和查询 ==============

@router.get("")
def list_audit_logs(
    start_date: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD HH:mm:ss"),
    end_date: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD HH:mm:ss"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    username: Optional[str] = Query(None, description="用户名"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    status: Optional[str] = Query(None, description="搜索操作详情（模糊查询）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取审计日志列表（支持多条件筛选）
    仅管理员可访问
    """
    query = db.query(
        AuditLog,
        User.username.label('username'),
        User.role.label('user_role'),
        func.count(AuditLogFile.id).label('files_count')
    ).join(
        User, AuditLog.user_id == User.id
    ).outerjoin(
        AuditLogFile, and_(
            AuditLogFile.audit_log_id == AuditLog.id,
            AuditLogFile.is_deleted == False
        )
    ).group_by(AuditLog.id)
    
    # 日期时间筛选（支持精确到秒）
    if start_date:
        try:
            # URL解码：将+替换为空格
            start_date = start_date.replace('+', ' ')
            # 尝试精确时间格式
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # 降级为日期格式
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始时间格式错误")
    
    if end_date:
        try:
            # URL解码：将+替换为空格
            end_date = end_date.replace('+', ' ')
            # 尝试精确时间格式
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # 降级为日期格式，自动加1天
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AuditLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束时间格式错误")
    
    # 用户筛选
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if username:
        query = query.filter(User.username.like(f"%{username}%"))
    
    # 操作类型筛选（支持多个，逗号分隔）
    if action:
        # 如果包含逗号，说明是多个操作类型
        if ',' in action:
            actions = [a.strip() for a in action.split(',')]
            query = query.filter(AuditLog.action.in_(actions))
        else:
            query = query.filter(AuditLog.action.like(f"%{action}%"))
    
    # 资源类型筛选
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    # 操作详情模糊查询（支持搜索脚本名、文件路径等）
    if status:
        # 搜索多个字段：脚本名、脚本路径、详情内容
        # 注意：需要检查字段不为NULL，否则LIKE对NULL返回NULL
        search_conditions = []
        if status:
            search_conditions.append(
                and_(AuditLog.script_name.isnot(None), AuditLog.script_name.like(f"%{status}%"))
            )
            search_conditions.append(
                and_(AuditLog.script_path.isnot(None), AuditLog.script_path.like(f"%{status}%"))
            )
            search_conditions.append(
                and_(AuditLog.details.isnot(None), AuditLog.details.like(f"%{status}%"))
            )
        query = query.filter(or_(*search_conditions))
    
    # 按时间倒序
    query = query.order_by(AuditLog.created_at.desc())
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # 工作区基础路径
    workspace_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../work'))
    
    # 格式化返回
    items = []
    for audit_log, username, user_role, files_count in results:
        # 将绝对路径转为相对路径
        script_path = audit_log.script_path
        if script_path and os.path.isabs(script_path):
            try:
                script_path = os.path.relpath(script_path, workspace_base)
            except ValueError:
                # 如果无法计算相对路径，保持原样
                pass
        
        items.append({
            "id": audit_log.id,
            "username": username,
            "user_role": "管理员" if user_role == "admin" else "普通用户",
            "action": audit_log.action,
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "script_name": audit_log.script_name,
            "script_path": script_path,  # 使用相对路径
            "status": audit_log.status,
            "execution_duration": audit_log.execution_duration,
            "files_count": files_count,
            "has_log": audit_log.execution is not None,
            "ip_address": audit_log.ip_address,
            "created_at": audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "details": audit_log.details
        })
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/{audit_id}")
def get_audit_log_detail(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取审计日志详情（包含关联文件和执行信息）
    """
    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not audit_log:
        raise HTTPException(status_code=404, detail="审计日志不存在")
    
    # 获取用户信息
    user = db.query(User).filter(User.id == audit_log.user_id).first()
    
    # 获取关联文件
    files = db.query(AuditLogFile).filter(
        AuditLogFile.audit_log_id == audit_id
    ).all()
    
    # 获取执行详情
    execution = db.query(ScriptExecution).filter(
        ScriptExecution.audit_log_id == audit_id
    ).first()
    
    # 工作区基础路径
    workspace_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../work'))
    
    # 将绝对路径转为相对路径
    script_path = audit_log.script_path
    if script_path and os.path.isabs(script_path):
        try:
            script_path = os.path.relpath(script_path, workspace_base)
        except ValueError:
            pass
    
    return {
        "id": audit_log.id,
        "username": user.username if user else "未知",
        "user_role": "管理员" if user and user.role == "admin" else "普通用户",
        "action": audit_log.action,
        "resource_type": audit_log.resource_type,
        "resource_id": audit_log.resource_id,
        "script_name": audit_log.script_name,
        "script_path": script_path,  # 使用相对路径
        "status": audit_log.status,
        "execution_duration": audit_log.execution_duration,
        "ip_address": audit_log.ip_address,
        "created_at": audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "details": audit_log.details,
        "files": [
            {
                "id": f.id,
                "file_type": f.file_type,
                "filename": f.original_filename,
                "file_size": f.file_size,
                "mime_type": f.mime_type,
                "is_deleted": f.is_deleted,
                "deleted_at": f.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if f.deleted_at else None,
                "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "download_url": f"/api/audit/files/{f.id}/download"
            }
            for f in files
        ],
        "execution": {
            "start_time": execution.start_time.strftime("%Y-%m-%d %H:%M:%S") if execution else None,
            "end_time": execution.end_time.strftime("%Y-%m-%d %H:%M:%S") if execution and execution.end_time else None,
            "duration": execution.duration if execution else None,
            "status": execution.status if execution else None,
            "exit_code": execution.exit_code if execution else None,
            "has_stdout": bool(execution and execution.stdout),
            "has_stderr": bool(execution and execution.stderr)
        } if execution else None
    }


# ============== 执行日志查看 ==============

@router.get("/{audit_id}/log")
def get_execution_log(
    audit_id: int,
    full: bool = False,  # 是否返回全部日志
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取脚本执行日志（从文件读取）
    """
    # 获取审计日志
    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not audit_log:
        raise HTTPException(status_code=404, detail="审计记录不存在")
    
    # 解析details获取log_file路径
    import json
    import os
    from utils.execution_log import read_execution_log
    
    log_content = ""
    trigger_type = "unknown"
    log_file_path = ""
    log_file_relative = None
    is_partial = False
    file_info = {"exists": False}
    
    try:
        details = json.loads(audit_log.details) if audit_log.details else {}
        log_file = details.get("log_file", "")
        trigger_type = details.get("trigger_type", "unknown")
        log_file_path = log_file
        
        if log_file:
            # 构建完整路径检查文件
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            full_path = os.path.join(base_dir, log_file)
            
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                file_info = {
                    "exists": True,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "is_large": file_size > 1024 * 1024
                }
                
                # 获取相对路径
                log_file_relative = log_file
                
                # 读取日志内容
                log_content = read_execution_log(log_file)
                if log_content is None:
                    log_content = "(日志文件不存在或已被删除)"
                elif not full and len(log_content) > 50000:  # 如果内容超过50KB
                    # 只显示最后100行
                    lines = log_content.split('\n')
                    if len(lines) > 100:
                        log_content = "⚠️ 日志内容较大，仅显示最后100行\n" + "="*80 + "\n\n" + '\n'.join(lines[-100:])
                        is_partial = True
            else:
                log_content = "(日志文件不存在或已被删除)"
        else:
            log_content = "(未找到日志文件)"
    except Exception as e:
        log_content = f"(读取日志失败: {str(e)})"
    
    return {
        "audit_id": audit_id,
        "script_name": audit_log.script_name,
        "created_at": audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": audit_log.status,
        "trigger_type": trigger_type,
        "log_content": log_content,
        "log_file_relative": log_file_relative,  # 新增：日志文件相对路径
        "is_partial": is_partial,  # 新增：是否只是部分日志
        "file_info": file_info  # 新增：文件信息
    }


# ============== 文件管理 ==============

@router.get("/files/{file_id}/download")
def download_audit_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    下载审计归档文件或内容快照
    """
    audit_file = db.query(AuditLogFile).filter(AuditLogFile.id == file_id).first()
    if not audit_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 优先检查是否有内容快照（文件变更追踪）
    if audit_file.content_after:
        # 从数据库内容创建响应
        content = audit_file.content_after.encode('utf-8')
        filename = audit_file.file_name or audit_file.original_filename or "download.txt"
        
        return Response(
            content=content,
            media_type=audit_file.mime_type or "text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    # 否则尝试从归档文件系统获取
    archiver = FileArchiver(db)
    file_path = archiver.get_file_path(file_id)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="文件内容不存在")
    
    return FileResponse(
        path=file_path,
        filename=audit_file.original_filename or "download",
        media_type=audit_file.mime_type or "application/octet-stream"
    )


@router.delete("/files/{file_id}")
def delete_audit_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    逻辑删除审计文件
    """
    archiver = FileArchiver(db)
    success = archiver.logical_delete_file(file_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在或删除失败")
    
    return {"message": "文件已删除"}


@router.post("/files/{file_id}/restore")
def restore_audit_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    恢复逻辑删除的文件（仅管理员）
    """
    archiver = FileArchiver(db)
    success = archiver.restore_file(file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在或恢复失败")
    
    return {"message": "文件已恢复"}


# ============== 导出功能 ==============

@router.post("/export")
def export_audit_logs(
    format: str = Query("csv", description="导出格式: csv/excel"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    导出审计日志（仅管理员）
    """
    query = db.query(AuditLog, User.username).join(User, AuditLog.user_id == User.id)
    
    # 应用筛选条件
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(AuditLog.created_at >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(AuditLog.created_at < end_dt)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action.like(f"%{action}%"))
    
    # 限制最大导出数量
    results = query.order_by(AuditLog.created_at.desc()).limit(10000).all()
    
    if format == "csv":
        # CSV导出
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "ID", "用户名", "操作", "资源类型", "脚本名称",
            "状态", "执行时长(秒)", "IP地址", "创建时间", "详情"
        ])
        
        # 写入数据
        for audit_log, username in results:
            writer.writerow([
                audit_log.id,
                username,
                audit_log.action,
                audit_log.resource_type,
                audit_log.script_name or "-",
                audit_log.status or "-",
                audit_log.execution_duration or "-",
                audit_log.ip_address or "-",
                audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                audit_log.details or "-"
            ])
        
        # 返回CSV文件
        output.seek(0)
        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式")


# ============== 统计功能 ==============

@router.get("/stats/summary")
def get_audit_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取审计日志统计信息（仅管理员）
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 总记录数
    total_logs = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= start_date
    ).scalar()
    
    # 执行成功数
    success_count = db.query(func.count(AuditLog.id)).filter(
        and_(
            AuditLog.created_at >= start_date,
            AuditLog.status == "success"
        )
    ).scalar()
    
    # 执行失败数
    failed_count = db.query(func.count(AuditLog.id)).filter(
        and_(
            AuditLog.created_at >= start_date,
            AuditLog.status == "failed"
        )
    ).scalar()
    
    # 按操作类型统计
    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).all()
    
    # 按用户统计
    user_stats = db.query(
        User.username,
        func.count(AuditLog.id).label('count')
    ).join(
        User, AuditLog.user_id == User.id
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(User.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    
    return {
        "period_days": days,
        "total_logs": total_logs,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": round(success_count / total_logs * 100, 2) if total_logs > 0 else 0,
        "action_stats": [{"action": action, "count": count} for action, count in action_stats],
        "user_stats": [{"username": username, "count": count} for username, count in user_stats]
    }


@router.get("/{audit_id}/file-changes")
def get_file_changes(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取审计日志的文件变更详情"""
    from models import AuditLogFile
    from utils.content_differ import content_differ
    
    # 查询审计日志
    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not audit_log:
        raise HTTPException(status_code=404, detail="审计日志不存在")
    
    # 非管理员只能查看自己的日志
    if current_user.role != "admin" and audit_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此日志")
    
    # 查询关联的文件变更记录
    file_logs = db.query(AuditLogFile).filter(
        AuditLogFile.audit_log_id == audit_id,
        AuditLogFile.content_diff.isnot(None)  # 只返回有diff的记录
    ).all()
    
    if not file_logs:
        return {
            "audit_id": audit_id,
            "has_changes": False,
            "message": "此操作没有文件内容变更记录"
        }
    
    # 格式化返回数据
    changes = []
    for file_log in file_logs:
        # 格式化diff用于前端显示
        diff_lines = content_differ.format_diff_for_display(file_log.content_diff or "")
        
        changes.append({
            "file_id": file_log.id,
            "file_name": file_log.file_name,
            "file_path": file_log.file_path,
            "lines_added": file_log.lines_added,
            "lines_deleted": file_log.lines_deleted,
            "size_before": len(file_log.content_before or ""),
            "size_after": len(file_log.content_after or ""),
            "diff_lines": diff_lines,
            "has_content_before": bool(file_log.content_before),
            "has_content_after": bool(file_log.content_after)
        })
    
    return {
        "audit_id": audit_id,
        "has_changes": True,
        "file_count": len(changes),
        "total_lines_added": sum(c["lines_added"] for c in changes),
        "total_lines_deleted": sum(c["lines_deleted"] for c in changes),
        "changes": changes
    }


@router.get("/{audit_id}/file-changes/{file_id}/content")
def get_file_content(
    audit_id: int,
    file_id: int,
    version: str = Query(..., description="版本: old/new"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取文件的完整内容（修改前或修改后）"""
    from models import AuditLogFile
    
    # 查询审计日志
    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not audit_log:
        raise HTTPException(status_code=404, detail="审计日志不存在")
    
    # 非管理员只能查看自己的日志
    if current_user.role != "admin" and audit_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此日志")
    
    # 查询文件记录
    file_log = db.query(AuditLogFile).filter(
        AuditLogFile.id == file_id,
        AuditLogFile.audit_log_id == audit_id
    ).first()
    
    if not file_log:
        raise HTTPException(status_code=404, detail="文件记录不存在")
    
    # 返回指定版本的内容
    if version == "before":
        content = file_log.content_before or ""
    else:
        content = file_log.content_after or ""
    
    return {
        "file_id": file_id,
        "file_name": file_log.file_name,
        "file_path": file_log.file_path,
        "version": version,
        "content": content,
        "size": len(content),
        "lines": len(content.splitlines())
    }
