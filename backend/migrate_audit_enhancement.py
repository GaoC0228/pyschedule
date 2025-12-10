#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：审计日志模块增强
添加：
1. audit_log_files - 审计日志关联文件表
2. script_executions - 脚本执行详情表
3. 扩展 audit_logs 表字段
"""
from sqlalchemy import create_engine, text
from config import settings

def migrate():
    """执行迁移"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("=" * 60)
        print("开始审计日志模块增强迁移...")
        print("=" * 60)
        
        # 1. 扩展 audit_logs 表
        print("\n[1/3] 扩展 audit_logs 表...")
        try:
            # 添加脚本路径
            conn.execute(text("""
                ALTER TABLE audit_logs 
                ADD COLUMN script_path VARCHAR(500) NULL COMMENT '执行的脚本路径'
            """))
            print("  ✅ 添加 script_path 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("  ⚠️  script_path 字段已存在")
            else:
                raise
        
        try:
            # 添加脚本名称
            conn.execute(text("""
                ALTER TABLE audit_logs 
                ADD COLUMN script_name VARCHAR(255) NULL COMMENT '脚本名称'
            """))
            print("  ✅ 添加 script_name 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("  ⚠️  script_name 字段已存在")
            else:
                raise
        
        try:
            # 添加执行状态
            conn.execute(text("""
                ALTER TABLE audit_logs 
                ADD COLUMN status VARCHAR(20) NULL COMMENT '执行状态：success/failed/running'
            """))
            print("  ✅ 添加 status 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("  ⚠️  status 字段已存在")
            else:
                raise
        
        try:
            # 添加执行时长
            conn.execute(text("""
                ALTER TABLE audit_logs 
                ADD COLUMN execution_duration FLOAT NULL COMMENT '执行时长（秒）'
            """))
            print("  ✅ 添加 execution_duration 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("  ⚠️  execution_duration 字段已存在")
            else:
                raise
        
        # 2. 创建 audit_log_files 表
        print("\n[2/3] 创建 audit_log_files 表...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_log_files (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    audit_log_id INT NOT NULL COMMENT '关联审计日志ID',
                    file_type VARCHAR(50) NULL COMMENT '文件类型：output/log/csv/xlsx',
                    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
                    stored_filename VARCHAR(255) NOT NULL COMMENT '存储文件名（UUID）',
                    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
                    file_size BIGINT NULL COMMENT '文件大小（字节）',
                    mime_type VARCHAR(100) NULL COMMENT 'MIME类型',
                    is_deleted BOOLEAN DEFAULT FALSE COMMENT '逻辑删除标记',
                    deleted_at DATETIME NULL COMMENT '删除时间',
                    deleted_by INT NULL COMMENT '删除操作用户ID',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_audit_log_id (audit_log_id),
                    INDEX idx_is_deleted (is_deleted),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志关联文件表'
            """))
            print("  ✅ 创建 audit_log_files 表成功")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ⚠️  audit_log_files 表已存在")
            else:
                raise
        
        # 3. 创建 script_executions 表
        print("\n[3/3] 创建 script_executions 表...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS script_executions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    audit_log_id INT NOT NULL COMMENT '关联审计日志',
                    user_id INT NOT NULL COMMENT '执行用户',
                    script_path VARCHAR(500) NOT NULL COMMENT '脚本路径',
                    script_name VARCHAR(255) NOT NULL COMMENT '脚本名称',
                    execution_command TEXT NULL COMMENT '执行命令',
                    start_time DATETIME NOT NULL COMMENT '开始时间',
                    end_time DATETIME NULL COMMENT '结束时间',
                    duration FLOAT NULL COMMENT '执行时长（秒）',
                    status VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT 'success/failed/running',
                    exit_code INT NULL COMMENT '退出码',
                    stdout TEXT NULL COMMENT '标准输出',
                    stderr TEXT NULL COMMENT '标准错误',
                    pid INT NULL COMMENT '进程ID',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_audit_log_id (audit_log_id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status),
                    INDEX idx_start_time (start_time),
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='脚本执行详情表'
            """))
            print("  ✅ 创建 script_executions 表成功")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ⚠️  script_executions 表已存在")
            else:
                raise
        
        # 提交更改
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ 审计日志模块增强迁移完成！")
        print("=" * 60)
        print("\n新增功能:")
        print("  • 审计日志关联文件管理（支持逻辑删除）")
        print("  • 脚本执行详情记录（包含日志和状态）")
        print("  • 执行时长统计")
        print("  • 文件归档和下载功能")
        print("\n")

if __name__ == "__main__":
    migrate()
