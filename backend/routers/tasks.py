from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Task, TaskExecution, User, TaskStatus
from schemas import TaskCreate, TaskUpdate, TaskResponse, TaskExecutionResponse
from auth import get_current_user, require_admin
from audit import create_audit_log, AuditAction, ResourceType
from task_scheduler import task_scheduler
from config import settings
from utils.ip_utils import get_real_ip
from utils.task_logger import task_logger
from utils.paths import get_execution_output_file
import os
import shutil
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务"""
    # 创建任务记录（脚本稍后上传）
    db_task = Task(
        name=task.name,
        description=task.description,
        script_path="",  # 稍后更新
        script_params=task.script_params,  # 保存脚本参数
        cron_expression=task.cron_expression,
        is_active=False,  # 创建时默认禁用，上传脚本后再根据用户选择决定是否启用
        owner_id=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_CREATE,
        resource_type=ResourceType.TASK,
        resource_id=db_task.id,
        details={"name": task.name, "cron": task.cron_expression},
        ip_address=get_real_ip(request)
    )
    
    return db_task


@router.post("/{task_id}/upload", response_model=TaskResponse)
async def upload_script(
    task_id: int,
    request: Request,
    file: UploadFile = File(...),
    is_active: bool = False,  # 接收是否启用的参数
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传任务脚本并设置启用状态"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限操作此任务")
    
    # 验证文件类型
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="只能上传Python脚本文件(.py)")
    
    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_dir, f"task_{task_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 更新任务脚本路径和启用状态
    task.script_path = file_path
    task.is_active = is_active  # 设置用户选择的启用状态
    db.commit()
    db.refresh(task)
    
    # 如果启用，添加到调度器并计算下次执行时间
    if task.is_active:
        try:
            next_run = task_scheduler.add_task(task.id, task.cron_expression)
            if next_run:
                task.next_run_at = next_run
                db.commit()
                db.refresh(task)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"添加任务到调度器失败: {str(e)}")
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_UPLOAD,
        resource_type=ResourceType.SCRIPT,
        resource_id=task.id,
        details={"filename": file.filename},
        ip_address=get_real_ip(request)
    )
    
    return task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,  # 按创建者筛选
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表（支持搜索和按创建者筛选）"""
    # 基础查询
    if current_user.role == "admin":
        query = db.query(Task)
    else:
        query = db.query(Task).filter(Task.owner_id == current_user.id)
    
    # 创建者过滤（仅管理员可用）
    if owner_id is not None and current_user.role == "admin":
        query = query.filter(Task.owner_id == owner_id)
    
    # 搜索过滤
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Task.name.like(search_pattern)) |
            (Task.description.like(search_pattern)) |
            (Task.cron_expression.like(search_pattern))
        )
    
    tasks = query.offset(skip).limit(limit).all()
    
    # 添加创建者用户名
    result = []
    for task in tasks:
        task_dict = TaskResponse.from_orm(task).dict()
        owner = db.query(User).filter(User.id == task.owner_id).first()
        task_dict['owner_username'] = owner.username if owner else "未知"
        result.append(task_dict)
    
    return result


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    # 添加创建者用户名
    task_dict = TaskResponse.from_orm(task).dict()
    owner = db.query(User).filter(User.id == task.owner_id).first()
    task_dict['owner_username'] = owner.username if owner else "未知"
    
    return task_dict


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限操作此任务")
    
    # 更新字段
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    # 更新调度器
    if task.is_active and task.script_path:
        try:
            task_scheduler.add_task(task.id, task.cron_expression)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"更新调度器失败: {str(e)}")
    else:
        task_scheduler.remove_task(task.id)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_UPDATE,
        resource_type=ResourceType.TASK,
        resource_id=task.id,
        details=update_data,
        ip_address=get_real_ip(request)
    )
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限操作此任务")
    
    # 从调度器移除
    task_scheduler.remove_task(task.id)
    
    # 删除脚本文件
    if task.script_path and os.path.exists(task.script_path):
        os.remove(task.script_path)
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_DELETE,
        resource_type=ResourceType.TASK,
        resource_id=task.id,
        details={"name": task.name},
        ip_address=get_real_ip(request)
    )
    
    # 删除任务
    db.delete(task)
    db.commit()


@router.post("/{task_id}/execute", status_code=status.HTTP_202_ACCEPTED)
def execute_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动执行任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限操作此任务")
    
    if not task.script_path:
        raise HTTPException(status_code=400, detail="任务脚本未上传")
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_EXECUTE,
        resource_type=ResourceType.TASK,
        resource_id=task.id,
        details={"trigger_type": "manual"},
        ip_address=get_real_ip(request)
    )
    
    # 异步执行任务，传递执行用户信息
    task_scheduler.execute_task(task.id, executed_by=current_user.id, trigger_type="manual")
    
    return {"message": "任务已提交执行", "task_id": task.id, "executed_by": current_user.username}


@router.get("/{task_id}/executions", response_model=List[TaskExecutionResponse])
def get_task_executions(
    task_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务执行记录"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id
    ).order_by(TaskExecution.start_time.desc()).offset(skip).limit(limit).all()
    
    return executions


@router.get("/{task_id}/executions/search")
def search_execution_logs(
    task_id: int,
    keyword: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据关键字搜索任务执行日志"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    # 获取所有执行记录
    executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id,
        TaskExecution.log_file.isnot(None)
    ).order_by(TaskExecution.start_time.desc()).all()
    
    # 搜索日志文件（优化：流式读取，避免大文件卡顿）
    matched_executions = []
    for execution in executions:
        if execution.log_file and os.path.exists(execution.log_file):
            try:
                # 检查文件大小，超过10MB跳过
                file_size = os.path.getsize(execution.log_file)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    continue
                
                # 流式读取，只保存匹配的行
                matched_lines = []
                with open(execution.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if keyword.lower() in line.lower():
                            matched_lines.append(line.strip())
                            if len(matched_lines) >= 3:  # 最多保存3行
                                break
                
                if matched_lines:
                    matched_executions.append({
                        "id": execution.id,
                        "task_id": execution.task_id,
                        "trigger_type": execution.trigger_type,
                        "status": execution.status,
                        "start_time": execution.start_time,
                        "end_time": execution.end_time,
                        "exit_code": execution.exit_code,
                        "matched_lines": matched_lines
                    })
            except Exception as e:
                continue
    
    return {
        "keyword": keyword,
        "total": len(matched_executions),
        "executions": matched_executions
    }


@router.get("/{task_id}/script")
def get_task_script(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务脚本内容"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    if not task.script_path or not os.path.exists(task.script_path):
        raise HTTPException(status_code=404, detail="脚本文件不存在")
    
    try:
        with open(task.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "path": task.script_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取脚本失败: {str(e)}")


@router.post("/{task_id}/script")
def save_task_script(
    task_id: int,
    script_data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存任务脚本内容"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此任务")
    
    content = script_data.get('content', '')
    if not content.strip():
        raise HTTPException(status_code=400, detail="脚本内容不能为空")
    
    # 获取is_active参数（用于新建任务时设置启用状态）
    is_active = script_data.get('is_active')
    
    # 确保任务脚本目录存在（使用与上传相同的目录结构）
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # 脚本文件路径
    script_filename = f"task_{task.id}_script.py"
    script_path = os.path.join(upload_dir, script_filename)
    
    try:
        # 保存脚本内容
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 更新任务记录
        task.script_path = script_path
        task.updated_at = datetime.now()
        
        # 如果传递了is_active参数，更新启用状态（用于新建任务）
        if is_active is not None:
            task.is_active = is_active
        
        db.commit()
        
        # 如果任务已启用，重新调度并更新下次执行时间
        if task.is_active:
            # 先移除旧任务，再添加新任务
            try:
                task_scheduler.remove_task(task.id)
            except:
                pass  # 如果任务不存在，忽略错误
            
            next_run = task_scheduler.add_task(task.id, task.cron_expression)
            if next_run:
                task.next_run_at = next_run
                db.commit()
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.TASK_UPDATE,
            resource_type=ResourceType.TASK,
            resource_id=task.id,
            status="success",
            details={
                "task_name": task.name,
                "action": "保存脚本",
                "script_lines": len(content.split('\n'))
            },
            ip_address=get_real_ip(request)
        )
        
        return {"message": "脚本保存成功", "path": script_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存脚本失败: {str(e)}")


@router.get("/{task_id}/script/download")
def download_task_script(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载任务脚本文件"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问此任务")
    
    if not task.script_path or not os.path.exists(task.script_path):
        raise HTTPException(status_code=404, detail="脚本文件不存在")
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_FILE_DOWNLOAD,
        resource_type=ResourceType.TASK,
        resource_id=task.id,
        status="success",
        details={
            "task_name": task.name,
            "action": "下载脚本"
        },
        ip_address=get_real_ip(request)
    )
    
    # 返回文件
    filename = f"task_{task.id}_{task.name}.py"
    return FileResponse(
        path=task.script_path,
        filename=filename,
        media_type='text/plain'
    )


@router.get("/{task_id}/executions/{execution_id}/log")
def get_execution_log(
    task_id: int,
    execution_id: int,
    full: bool = False,  # 是否返回全部日志
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务执行日志"""
    # 检查任务权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    # 获取执行记录
    execution = db.query(TaskExecution).filter(
        TaskExecution.id == execution_id,
        TaskExecution.task_id == task_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    # 读取日志文件
    if not execution.log_file or not os.path.exists(execution.log_file):
        return {
            "log": "日志文件不存在",
            "log_file": execution.log_file,
            "log_file_relative": None,
            "exists": False,
            "is_partial": False,
            "file_info": {"exists": False}
        }
    
    # 获取日志文件信息
    log_info = task_logger.get_log_info(execution.log_file)
    
    # 计算相对路径（从volumes/task_data开始）
    log_file_relative = execution.log_file.replace('/app/volumes/', '') if execution.log_file else None
    
    # 根据参数决定读取多少行
    if full:
        # 全部日志：读取所有内容（最多10000行避免过大）
        log_content = task_logger.read_log(execution.log_file, max_lines=10000)
        is_partial = False
    else:
        # 部分日志：只读取最后100行
        log_content = task_logger.read_log(execution.log_file, max_lines=100)
        # 判断是否有更多内容
        is_partial = log_info.get("line_count", 0) > 100 if log_info.get("line_count") else log_info.get("is_large", False)
    
    return {
        "log": log_content,
        "log_file": execution.log_file,
        "log_file_relative": log_file_relative,  # 相对路径
        "exists": True,
        "is_partial": is_partial,  # 是否只是部分日志
        "file_info": log_info
    }


@router.get("/{task_id}/next-run")
def get_next_run_time(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务下次执行时间"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    # 从调度器获取下次执行时间
    job_id = f"task_{task_id}"
    job = task_scheduler.scheduler.get_job(job_id)
    
    if not job or not task.is_active:
        return {
            "next_run_time": None,
            "countdown_seconds": None
        }
    
    next_run = job.next_run_time
    if next_run:
        # 计算倒计时（秒）
        now = datetime.now(next_run.tzinfo)
        countdown = (next_run - now).total_seconds()
        
        return {
            "next_run_time": next_run.isoformat(),
            "countdown_seconds": max(0, int(countdown))
        }
    
    return {
        "next_run_time": None,
        "countdown_seconds": None
    }


@router.get("/{task_id}/executions/{execution_id}/files")
def get_execution_files(
    task_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务执行产出的文件列表"""
    # 检查任务权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问此任务")
    
    # 获取执行记录
    execution = db.query(TaskExecution).filter(
        TaskExecution.id == execution_id,
        TaskExecution.task_id == task_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    # 解析文件列表
    files = []
    if execution.output_files:
        try:
            files = json.loads(execution.output_files)
        except:
            files = []
    
    return {
        "execution_id": execution_id,
        "task_id": task_id,
        "files": files,
        "total": len(files)
    }


@router.get("/{task_id}/executions/{execution_id}/preview-file/{filename:path}")
def preview_execution_file(
    task_id: int,
    execution_id: int,
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预览任务执行产出的文件内容（仅支持文本文件）"""
    # 检查任务权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问此任务")
    
    # 使用统一的路径工具构建文件路径
    filepath = get_execution_output_file(task_id, execution_id, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filepath}")
    
    # 检查文件大小（限制预览大小）
    file_size = os.path.getsize(filepath)
    if file_size > 1024 * 1024:  # 1MB
        raise HTTPException(status_code=400, detail="文件过大，无法预览（限制1MB）")
    
    # 尝试读取文件内容
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 记录审计日志
        create_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.TASK_FILE_VIEW,
            resource_type=ResourceType.TASK,
            resource_id=task_id,
            status="success",
            details={
                "task_name": task.name,
                "action": "预览执行产出文件",
                "execution_id": execution_id,
                "filename": filename
            },
            ip_address=get_real_ip(request)
        )
        
        return {
            "filename": filename,
            "size": file_size,
            "content": content
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="无法预览二进制文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.get("/{task_id}/executions/{execution_id}/files/{filename:path}")
def download_execution_file(
    task_id: int,
    execution_id: int,
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载任务执行产出的文件"""
    # 检查任务权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问此任务")
    
    # 使用统一的路径工具构建文件路径
    filepath = get_execution_output_file(task_id, execution_id, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filepath}")
    
    # 记录审计日志
    create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.TASK_FILE_DOWNLOAD,
        resource_type=ResourceType.TASK,
        resource_id=task_id,
        status="success",
        details={
            "task_name": task.name,
            "action": "下载执行产出文件",
            "execution_id": execution_id,
            "filename": filename
        },
        ip_address=get_real_ip(request)
    )
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/octet-stream'
    )
