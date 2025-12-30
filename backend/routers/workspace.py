from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import os
import shutil
import subprocess
import asyncio
from datetime import datetime
from database import get_db
from models import User
from auth import get_current_user
from audit import create_audit_log, AuditAction, ResourceType
from config import settings
from utils.script_analyzer import ScriptAnalyzer
from utils.workspace_permissions import WorkspacePermissions
from utils.content_differ import content_differ
from utils.request_utils import get_client_ip
from utils.ip_utils import get_real_ip
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspace", tags=["工作区"])


class FileUpdateRequest(BaseModel):
    file_path: str
    content: str

# 工作区目录
WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "work")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# 权限管理器
workspace_permissions = WorkspacePermissions(WORKSPACE_DIR)


def detect_interactive_script(file_path: str) -> bool:
    """
    检测脚本是否包含交互式操作
    返回True表示是交互式脚本，False表示非交互式
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检测交互式操作特征
        interactive_patterns = [
            'input(',           # Python 3的input
            'raw_input(',       # Python 2的raw_input
            'getpass.getpass(', # 密码输入
            'sys.stdin.read',   # 标准输入读取
            'click.prompt(',    # click库的提示输入
            'inquirer.',        # inquirer交互式问答库
        ]
        
        for pattern in interactive_patterns:
            if pattern in content:
                logger.info(f"检测到交互式特征: {pattern} in {file_path}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检测交互式脚本失败: {str(e)}")
        return False


def check_path_permission(current_user: User, file_path: str, require_write: bool = False):
    """
    检查路径权限的辅助函数
    
    Args:
        current_user: 当前用户
        file_path: 文件路径
        require_write: 是否需要写权限
        
    Returns:
        完整路径
    """
    full_path, _ = workspace_permissions.get_accessible_path(current_user, file_path)
    if require_write:
        workspace_permissions.check_write_permission(current_user, file_path)
    return full_path


@router.get("/files")
def list_files(
    path: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作区文件列表（带权限控制）"""
    try:
        # 确保用户目录和共享目录存在
        workspace_permissions.ensure_user_workspace(current_user.username)
        workspace_permissions.ensure_shared_workspace()
        
        # 如果是根目录，返回用户可见的目录
        if not path or path == "":
            root_items = workspace_permissions.get_root_items(current_user)
            items = []
            for item in root_items:
                item_path = os.path.join(WORKSPACE_DIR, item)
                if os.path.exists(item_path):
                    stat = os.stat(item_path)
                    items.append({
                        "type": "directory",
                        "name": item,
                        "path": item,
                        "size": 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "count": len(os.listdir(item_path)) if os.path.isdir(item_path) else 0
                    })
            return {"items": items, "path": ""}
        
        # 检查权限并获取完整路径
        full_path, display_path = workspace_permissions.get_accessible_path(current_user, path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="路径不存在")
        
        files = []
        dirs = []
        
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            rel_path = os.path.relpath(item_path, WORKSPACE_DIR)
            
            stat = os.stat(item_path)
            
            if os.path.isdir(item_path):
                dirs.append({
                    "name": item,
                    "path": rel_path,
                    "type": "directory",
                    "size": 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            else:
                files.append({
                    "name": item,
                    "path": rel_path,
                    "type": "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": os.path.splitext(item)[1]
                })
        
        # 目录排在前面，然后是文件
        return {
            "current_path": path,
            "items": dirs + files
        }
        
    except Exception as e:
        logger.error(f"列出文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = "",
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件到工作区（带权限控制）"""
    try:
        # 权限检查
        target_dir = check_path_permission(current_user, path, require_write=True)
        
        os.makedirs(target_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(target_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        relative_path = os.path.relpath(file_path, WORKSPACE_DIR)
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_UPLOAD,
            resource_type=ResourceType.FILE,
            status="success",
            details={
                "filename": file.filename,
                "path": relative_path,
                "size": file_size,
                "readable_size": f"{file_size / 1024:.2f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.2f} MB"
            },
            ip_address=get_real_ip(request) if request else None
        )
        
        return {
            "message": "文件上传成功",
            "filename": file.filename,
            "path": os.path.relpath(file_path, WORKSPACE_DIR),
            "size": os.path.getsize(file_path)
        }
        
    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-script")
async def analyze_script(
    file_path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分析脚本安全风险（带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, file_path, require_write=False)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not full_path.endswith('.py'):
            raise HTTPException(status_code=400, detail="只能分析Python脚本")
        
        # 读取脚本内容
        with open(full_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 分析脚本
        analysis_result = ScriptAnalyzer.analyze_script(script_content, db)
        
        # 检测是否为交互式脚本
        is_interactive = detect_interactive_script(full_path)
        analysis_result['is_interactive'] = is_interactive
        
        logger.info(f"用户 {current_user.username} 分析脚本: {file_path}, 风险等级: {analysis_result['risk_level']}, 交互式: {is_interactive}")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析脚本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _execute_script_in_background(audit_log_id: int, full_path: str, file_path: str, start_time: datetime, user_id: int):
    """后台执行脚本的函数"""
    from database import SessionLocal
    from models import AuditLog
    import json
    
    db = SessionLocal()
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = f"/app:{env.get('PYTHONPATH', '')}"
        
        result = subprocess.run(
            ["python", full_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
            cwd=os.path.dirname(full_path),
            env=env
        )
        
        status = "success" if result.returncode == 0 else "failed"
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 保存执行日志到文件
        from utils.execution_log import save_execution_log
        log_content = f"=== 标准输出 ===\n{result.stdout or '(无输出)'}\n\n=== 错误输出 ===\n{result.stderr or '(无错误)'}\n\n=== 执行信息 ===\n退出码: {result.returncode}\n执行时长: {duration}秒\n"
        log_file_path = save_execution_log(
            audit_log_id=audit_log_id,
            script_name=os.path.basename(file_path),
            trigger_type="manual",
            content=log_content
        )
        
        # 更新审计日志
        db_audit_log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        if db_audit_log:
            db_audit_log.status = status
            db_audit_log.execution_duration = duration
            details = json.loads(db_audit_log.details) if db_audit_log.details else {}
            details.update({
                "log_file": log_file_path,
                "returncode": result.returncode,
                "has_output": bool(result.stdout),
                "has_error": bool(result.stderr)
            })
            db_audit_log.details = json.dumps(details, ensure_ascii=False)
            db.commit()
            
        logger.info(f"后台脚本执行完成: {file_path}, 状态: {status}, 时长: {duration}秒")
        
    except subprocess.TimeoutExpired:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        db_audit_log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        if db_audit_log:
            db_audit_log.status = "failed"
            db_audit_log.execution_duration = duration
            details = json.loads(db_audit_log.details) if db_audit_log.details else {}
            details["error"] = "执行超时"
            db_audit_log.details = json.dumps(details, ensure_ascii=False)
            db.commit()
            
        logger.warning(f"后台脚本执行超时: {file_path}")
        
    except Exception as e:
        logger.error(f"后台脚本执行异常: {file_path}, 错误: {str(e)}")
        
        db_audit_log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        if db_audit_log:
            db_audit_log.status = "failed"
            details = json.loads(db_audit_log.details) if db_audit_log.details else {}
            details["error"] = str(e)
            db_audit_log.details = json.dumps(details, ensure_ascii=False)
            db.commit()
    finally:
        db.close()


@router.post("/execute")
async def execute_script(
    file_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行Python脚本（异步非阻塞，立即返回，带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, file_path, require_write=False)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not full_path.endswith('.py'):
            raise HTTPException(status_code=400, detail="只能执行Python脚本")
        
        logger.info(f"用户 {current_user.username} 启动脚本执行（异步）: {file_path}")
        
        start_time = datetime.now()
        
        # 创建审计日志（状态为running）
        audit_log = create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_EXECUTE,
            resource_type=ResourceType.SCRIPT,
            script_name=os.path.basename(file_path),
            script_path=file_path,
            status="running",
            details={
                "file_path": file_path, 
                "trigger_type": "manual",
                "log_file": ""
            },
            ip_address=get_real_ip(request)
        )
        db.commit()
        
        # 将脚本执行任务添加到后台任务队列
        background_tasks.add_task(
            _execute_script_in_background,
            audit_log.id,
            full_path,
            file_path,
            start_time,
            current_user.id
        )
        
        # 立即返回响应（脚本在后台执行）
        return {
            "success": True,
            "message": "脚本已开始在后台执行",
            "audit_log_id": audit_log.id,
            "file_path": file_path,
            "started_at": start_time.isoformat(),
            "status": "running",
            "tip": "请在审计日志页面查看执行结果"
        }
            
    except Exception as e:
        logger.error(f"启动脚本执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/read")
def read_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """读取文件内容（带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, file_path, require_write=False)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail="不能读取目录")
        
        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": os.path.basename(file_path),
            "path": file_path,
            "content": content,
            "size": os.path.getsize(full_path)
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="无法读取文件（非文本文件）")
    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
def download_file(
    file_path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载文件（带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, file_path, require_write=False)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail="不能下载目录")
        
        # 记录审计日志
        file_size = os.path.getsize(full_path)
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_DOWNLOAD,
            resource_type=ResourceType.FILE,
            status="success",
            details={
                "filename": os.path.basename(file_path),
                "path": file_path,
                "size": file_size,
                "readable_size": f"{file_size / 1024:.2f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.2f} MB"
            },
            ip_address=get_real_ip(request)
        )
        
        # 返回文件流
        filename = os.path.basename(file_path)
        
        # 处理中文文件名编码（RFC 5987）
        from urllib.parse import quote
        encoded_filename = quote(filename)
        
        def iterfile():
            with open(full_path, 'rb') as f:
                yield from f
        
        return StreamingResponse(
            iterfile(),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update")
def update_file(
    data: FileUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文件内容（带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, data.file_path, require_write=True)
        
        # 确保父目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 读取修改前的内容（如果文件存在）
        content_before = ""
        file_exists = os.path.exists(full_path)
        if file_exists:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content_before = f.read()
            except Exception as e:
                logger.warning(f"无法读取旧文件内容: {e}")
        
        content_after = data.content
        
        # 计算内容变更
        diff_text = ""
        lines_added = 0
        lines_deleted = 0
        change_summary = {}
        
        if file_exists and content_before != content_after:
            # 生成diff
            diff_text, lines_added, lines_deleted = content_differ.generate_diff(
                content_before, content_after
            )
            change_summary = content_differ.get_change_summary(content_before, content_after)
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content_after)
        
        # 记录审计日志（区分创建和更新操作）
        audit_action = AuditAction.WORKSPACE_CREATE if not file_exists else AuditAction.WORKSPACE_UPDATE
        audit_log = create_audit_log(
            db=db,
            user=current_user,
            action=audit_action,
            resource_type=ResourceType.FILE,
            resource_id=0,
            status="success",
            details={
                "file_path": data.file_path, 
                "size": len(content_after),
                "size_before": len(content_before) if file_exists else 0,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "has_changes": content_before != content_after,
                **change_summary
            },
            ip_address=get_client_ip(request)
        )
        
        # 如果文件不超过100KB，保存快照和diff
        if content_differ.should_save_content(content_after):
            from models import AuditLogFile
            
            # 创建文件快照记录
            file_log = AuditLogFile(
                audit_log_id=audit_log.id,
                file_type="text",
                original_filename=os.path.basename(data.file_path),
                stored_filename=os.path.basename(data.file_path),
                file_name=os.path.basename(data.file_path),
                file_path=data.file_path,
                file_size=len(content_after),
                content_before=content_before if file_exists else None,
                content_after=content_after,
                content_diff=diff_text if diff_text else None,
                lines_added=lines_added,
                lines_deleted=lines_deleted
            )
            db.add(file_log)
            db.commit()
        
        logger.info(f"用户 {current_user.username} 更新文件: {data.file_path} (新增{lines_added}行, 删除{lines_deleted}行)")
        
        return {
            "message": "文件保存成功",
            "file_path": data.file_path,
            "size": os.path.getsize(full_path),
            "changes": {
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "has_diff": bool(diff_text)
            }
        }
        
    except Exception as e:
        logger.error(f"更新文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
def delete_file(
    file_path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文件或目录（带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, file_path, require_write=True)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件或目录不存在")
        
        # 删除文件或目录
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_DELETE,
            resource_type=ResourceType.FILE,
            resource_id=0,
            status="success",
            details={"file_path": file_path},
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"用户 {current_user.username} 删除文件: {file_path}")
        
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename")
def rename_file(
    old_path: str,
    new_path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重命名文件或目录（带权限控制）"""
    try:
        # 权限检查
        old_full_path = check_path_permission(current_user, old_path, require_write=True)
        new_full_path = check_path_permission(current_user, new_path, require_write=True)
        
        if not os.path.exists(old_full_path):
            raise HTTPException(status_code=404, detail="文件或目录不存在")
        
        if os.path.exists(new_full_path):
            raise HTTPException(status_code=400, detail="目标文件已存在")
        
        # 重命名
        os.rename(old_full_path, new_full_path)
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_RENAME,
            resource_type=ResourceType.FILE,
            resource_id=0,
            status="success",
            details={"old_path": old_path, "new_path": new_path},
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"用户 {current_user.username} 重命名: {old_path} → {new_path}")
        
        return {"message": "重命名成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重命名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mkdir")
def create_directory(
    dir_path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建目录（带权限控制）"""
    try:
        # 权限检查
        full_path = check_path_permission(current_user, dir_path, require_write=True)
        
        os.makedirs(full_path, exist_ok=True)
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_UPLOAD,
            resource_type=ResourceType.WORKSPACE,
            details={"dir_path": dir_path},
            ip_address=get_client_ip(request)
        )
        
        return {"message": "目录创建成功", "path": dir_path}
        
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class MoveRequest(BaseModel):
    source_paths: List[str]
    target_dir: str

@router.post("/move")
def move_files(
    move_req: MoveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移动文件或目录（带权限控制）"""
    source_paths = move_req.source_paths
    target_dir = move_req.target_dir
    try:
        # 检查目标目录权限
        target_full_path = check_path_permission(current_user, target_dir, require_write=True)
        
        if not os.path.exists(target_full_path):
            raise HTTPException(status_code=404, detail="目标目录不存在")
        
        if not os.path.isdir(target_full_path):
            raise HTTPException(status_code=400, detail="目标路径不是目录")
        
        moved_items = []
        failed_items = []
        
        for source_path in source_paths:
            try:
                # 检查源文件权限
                source_full_path = check_path_permission(current_user, source_path, require_write=True)
                
                if not os.path.exists(source_full_path):
                    failed_items.append({"path": source_path, "error": "文件不存在"})
                    continue
                
                # 获取文件/目录名称
                item_name = os.path.basename(source_full_path)
                new_full_path = os.path.join(target_full_path, item_name)
                
                # 检查目标位置是否已存在同名文件
                if os.path.exists(new_full_path):
                    failed_items.append({"path": source_path, "error": "目标位置已存在同名文件"})
                    continue
                
                # 检查是否试图将目录移动到自己的子目录中
                if os.path.isdir(source_full_path):
                    try:
                        rel_path = os.path.relpath(target_full_path, source_full_path)
                        if not rel_path.startswith('..'):
                            failed_items.append({"path": source_path, "error": "不能将目录移动到自己的子目录中"})
                            continue
                    except ValueError:
                        # 不同驱动器，允许移动
                        pass
                
                # 执行移动
                shutil.move(source_full_path, new_full_path)
                
                # 计算新的相对路径
                new_relative_path = os.path.relpath(new_full_path, WORKSPACE_DIR)
                if new_relative_path == '.':
                    new_relative_path = item_name
                
                moved_items.append({
                    "source": source_path,
                    "target": new_relative_path
                })
                
            except HTTPException:
                raise
            except Exception as e:
                failed_items.append({"path": source_path, "error": str(e)})
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_MOVE,
            resource_type=ResourceType.FILE,
            resource_id=0,
            status="success" if len(failed_items) == 0 else "partial",
            details={
                "target_dir": target_dir,
                "moved_count": len(moved_items),
                "failed_count": len(failed_items),
                "moved_items": moved_items,
                "failed_items": failed_items
            },
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"用户 {current_user.username} 移动文件: {len(moved_items)} 成功, {len(failed_items)} 失败")
        
        return {
            "message": f"移动完成: {len(moved_items)} 成功, {len(failed_items)} 失败",
            "moved_items": moved_items,
            "failed_items": failed_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移动文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/copy")
def copy_files(
    move_req: MoveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复制文件或目录（带权限控制）"""
    source_paths = move_req.source_paths
    target_dir = move_req.target_dir
    
    try:
        # 检查目标目录权限
        target_full_path = check_path_permission(current_user, target_dir, require_write=True)
        
        if not os.path.exists(target_full_path):
            raise HTTPException(status_code=404, detail="目标目录不存在")
        
        if not os.path.isdir(target_full_path):
            raise HTTPException(status_code=400, detail="目标路径不是目录")
        
        copied_items = []
        failed_items = []
        
        for source_path in source_paths:
            try:
                # 检查源文件权限（读权限即可）
                source_full_path = check_path_permission(current_user, source_path, require_write=False)
                
                if not os.path.exists(source_full_path):
                    failed_items.append({"path": source_path, "error": "文件不存在"})
                    continue
                
                # 获取文件/目录名称
                item_name = os.path.basename(source_full_path)
                new_full_path = os.path.join(target_full_path, item_name)
                
                # 如果目标位置已存在，添加后缀
                if os.path.exists(new_full_path):
                    base_name = item_name
                    counter = 1
                    if os.path.isfile(source_full_path):
                        # 文件：在扩展名前添加后缀
                        name_parts = os.path.splitext(item_name)
                        while os.path.exists(new_full_path):
                            base_name = f"{name_parts[0]}_副本{counter}{name_parts[1]}"
                            new_full_path = os.path.join(target_full_path, base_name)
                            counter += 1
                    else:
                        # 目录：在名称后添加后缀
                        while os.path.exists(new_full_path):
                            base_name = f"{item_name}_副本{counter}"
                            new_full_path = os.path.join(target_full_path, base_name)
                            counter += 1
                    item_name = base_name
                
                # 执行复制
                if os.path.isdir(source_full_path):
                    shutil.copytree(source_full_path, new_full_path)
                else:
                    shutil.copy2(source_full_path, new_full_path)
                
                # 计算新的相对路径
                new_relative_path = os.path.relpath(new_full_path, WORKSPACE_DIR)
                if new_relative_path == '.':
                    new_relative_path = item_name
                
                copied_items.append({
                    "source": source_path,
                    "target": new_relative_path
                })
                
            except HTTPException:
                raise
            except Exception as e:
                failed_items.append({"path": source_path, "error": str(e)})
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.WORKSPACE_COPY,
            resource_type=ResourceType.FILE,
            resource_id=0,
            status="success" if len(failed_items) == 0 else "partial",
            details={
                "target_dir": target_dir,
                "copied_count": len(copied_items),
                "failed_count": len(failed_items),
                "copied_items": copied_items,
                "failed_items": failed_items
            },
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"用户 {current_user.username} 复制文件: {len(copied_items)} 成功, {len(failed_items)} 失败")
        
        return {
            "message": f"复制完成: {len(copied_items)} 成功, {len(failed_items)} 失败",
            "copied_items": copied_items,
            "failed_items": failed_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
