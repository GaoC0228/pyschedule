from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models import UserRole, TaskStatus


# 用户相关Schema
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    can_manage_packages: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    can_manage_packages: bool = False
    last_activity: Optional[datetime] = None
    created_at: datetime
    is_online: bool = False  # 是否在线（前端计算或后端设置）
    
    class Config:
        from_attributes = True


# 认证相关Schema
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# 任务相关Schema
class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    cron_expression: str
    script_params: Optional[str] = None  # 脚本命令行参数


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    script_params: Optional[str] = None  # 脚本命令行参数
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    script_path: str
    status: TaskStatus
    is_active: bool
    owner_id: int
    owner_username: Optional[str] = None  # 创建者用户名
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 任务执行记录Schema
class TaskExecutionResponse(BaseModel):
    id: int
    task_id: int
    executed_by: Optional[int] = None  # 执行用户ID
    trigger_type: str = "scheduled"  # 触发方式
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    log_file: Optional[str] = None  # 日志文件路径
    exit_code: Optional[int] = None  # 退出码
    output_files: Optional[str] = None  # 产出文件列表（JSON字符串）
    # 保留旧字段兼容性（已弃用，使用log_file）
    output: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


# 审计日志Schema
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 分页响应
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List
