from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from database import engine, Base
from routers import auth, tasks, users, workspace, terminal_ws, audit_logs, audit_cleaner, system, web_terminal_ws, packages
from task_scheduler import task_scheduler
from config import settings
import logging

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("应用启动中...")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已创建")
    
    # 创建上传目录
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"上传目录已创建: {settings.UPLOAD_DIR}")
    
    # 加载定时任务
    task_scheduler.load_tasks_from_db()
    logger.info("定时任务已加载")
    
    yield
    
    # 关闭时
    logger.info("应用关闭中...")
    task_scheduler.shutdown()
    logger.info("任务调度器已关闭")


app = FastAPI(
    title="Python定时任务管理平台",
    description="多用户Python定时任务Web平台",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(users.router)
# app.include_router(audit.router)  # 旧的审计日志路由已禁用
app.include_router(audit_logs.router)  # 新的增强审计日志API
app.include_router(workspace.router)
app.include_router(terminal_ws.router)
app.include_router(system.router)  # 系统信息API

# 导入并注册数据库配置路由
from routers import database_config
app.include_router(database_config.router)

# 注册审计清理路由
app.include_router(audit_cleaner.router, prefix="/api/audit-cleaner", tags=["audit-cleaner"])

# 注册Web终端WebSocket路由
app.include_router(web_terminal_ws.router)

# 注册包管理路由
app.include_router(packages.router)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "Python定时任务管理平台API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)
