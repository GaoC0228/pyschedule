from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

# 使用本地时间作为默认值（而不是UTC时间）
def get_current_time():
    """获取当前本地时间"""
    return datetime.now()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    can_manage_packages = Column(Boolean, default=False, nullable=False)  # 包管理权限
    last_activity = Column(DateTime, nullable=True)  # 最后活动时间（用于判断在线状态）
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    updated_at = Column(DateTime, default=get_current_time, onupdate=get_current_time, nullable=False)
    
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    script_path = Column(String(255), nullable=False)
    script_params = Column(Text, nullable=True)  # 脚本命令行参数
    cron_expression = Column(String(100), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    updated_at = Column(DateTime, default=get_current_time, onupdate=get_current_time, nullable=False)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    
    owner = relationship("User", back_populates="tasks")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")


class TaskExecution(Base):
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    executed_by = Column(Integer, ForeignKey("users.id"))  # 执行用户ID
    trigger_type = Column(String(20), default="scheduled")  # scheduled/manual
    status = Column(Enum(TaskStatus), nullable=False)
    start_time = Column(DateTime, default=get_current_time, nullable=False)
    end_time = Column(DateTime)
    log_file = Column(String(500))  # 日志文件路径（替代output和error）
    exit_code = Column(Integer)  # 退出码
    output_files = Column(Text)  # 产出文件列表（JSON格式）
    
    task = relationship("Task", back_populates="executions")
    executor = relationship("User", foreign_keys=[executed_by])


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(45))
    script_path = Column(String(500))  # 执行的脚本路径
    script_name = Column(String(255))  # 脚本名称
    status = Column(String(20))  # 执行状态：success/failed/running
    execution_duration = Column(Float)  # 执行时长（秒）
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    
    user = relationship("User", back_populates="audit_logs")
    files = relationship("AuditLogFile", back_populates="audit_log", cascade="all, delete-orphan")
    execution = relationship("ScriptExecution", back_populates="audit_log", uselist=False, cascade="all, delete-orphan")


class DatabaseConfig(Base):
    """数据库配置表"""
    __tablename__ = "database_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    db_type = Column(String(20), nullable=False)
    environment = Column(String(20), nullable=False)
    
    # 连接信息
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    database = Column(String(100), nullable=True)
    
    # MongoDB特有
    connection_string = Column(String(500), nullable=True)
    replica_set = Column(String(100), nullable=True)
    auth_source = Column(String(100), nullable=True)
    
    # 其他配置
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 权限控制
    created_by = Column(String(50), nullable=True)  # 创建者用户名
    is_public = Column(Boolean, default=False)  # 是否公开（所有用户可见）
    
    # 时间戳
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    updated_at = Column(DateTime, default=get_current_time, onupdate=get_current_time)


class AuditLogFile(Base):
    """审计日志关联文件表"""
    __tablename__ = "audit_log_files"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=False)
    file_type = Column(String(50))  # output/log/csv/xlsx/json/text
    original_filename = Column(String(255))
    stored_filename = Column(String(255))
    file_name = Column(String(255))  # 文件名（用于快照）
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # 字节
    mime_type = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer, ForeignKey("users.id"))
    
    # 内容快照字段
    content_before = Column(Text)  # 修改前的文件内容
    content_after = Column(Text)  # 修改后的文件内容
    content_diff = Column(Text)  # 内容差异（Diff格式）
    lines_added = Column(Integer, default=0)  # 新增行数
    lines_deleted = Column(Integer, default=0)  # 删除行数
    
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    
    audit_log = relationship("AuditLog", back_populates="files")
    deleter = relationship("User", foreign_keys=[deleted_by])


class ScriptExecution(Base):
    """脚本执行详情表"""
    __tablename__ = "script_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    script_path = Column(String(500), nullable=False)
    script_name = Column(String(255), nullable=False)
    execution_command = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)  # 秒
    status = Column(String(20), default="running")  # success/failed/running
    exit_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)
    pid = Column(Integer)
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    
    audit_log = relationship("AuditLog", back_populates="execution")
    user = relationship("User", foreign_keys=[user_id])
