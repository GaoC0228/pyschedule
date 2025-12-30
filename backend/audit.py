from sqlalchemy.orm import Session
from models import AuditLog, User
from typing import Optional
import json


def create_audit_log(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    script_path: Optional[str] = None,
    script_name: Optional[str] = None,
    status: Optional[str] = None,
    execution_duration: Optional[float] = None
):
    """创建审计日志"""
    audit_log = AuditLog(
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address,
        script_path=script_path,
        script_name=script_name,
        status=status,
        execution_duration=execution_duration
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


# 审计操作常量
class AuditAction:
    # 用户操作
    USER_LOGIN = "用户登录"
    USER_LOGOUT = "用户登出"
    USER_CREATE = "创建用户"
    USER_UPDATE = "更新用户"
    USER_DELETE = "删除用户"
    
    # 任务操作
    TASK_CREATE = "创建任务"
    TASK_UPDATE = "更新任务"
    TASK_DELETE = "删除任务"
    TASK_UPLOAD = "上传脚本"
    TASK_EXECUTE = "手动执行任务"
    TASK_PAUSE = "暂停任务"
    TASK_RESUME = "恢复任务"
    TASK_FILE_VIEW = "查看任务文件"
    TASK_FILE_DOWNLOAD = "下载任务文件"
    
    # 系统操作
    SYSTEM_CONFIG = "系统配置"
    
    # 数据库配置操作
    CONFIG_CREATE = "创建数据库配置"
    CONFIG_UPDATE = "更新数据库配置"
    CONFIG_DELETE = "删除数据库配置"
    CONFIG_TEST = "测试数据库连接"
    
    # 工作区文件操作
    WORKSPACE_UPLOAD = "上传文件"
    WORKSPACE_DOWNLOAD = "下载文件"
    WORKSPACE_DELETE = "删除文件"
    WORKSPACE_RENAME = "重命名文件"
    WORKSPACE_EXECUTE = "执行脚本"
    WORKSPACE_MOVE = "移动文件"
    WORKSPACE_COPY = "复制文件"
    WORKSPACE_READ = "读取文件"
    WORKSPACE_CREATE = "创建文件"
    WORKSPACE_UPDATE = "更新文件"
    
    # 用户认证失败
    USER_LOGIN_FAILED = "登录失败"


class ResourceType:
    USER = "用户"
    TASK = "任务"
    SCRIPT = "脚本"
    SYSTEM = "系统"
    CONFIG = "配置"
    WORKSPACE = "工作区"
    FILE = "文件"
