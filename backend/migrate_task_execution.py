"""
迁移脚本：更新任务执行表结构
添加log_file和exit_code字段
"""
from database import engine
from sqlalchemy import text

def migrate():
    """执行迁移"""
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'exec_python_web' 
            AND TABLE_NAME = 'task_executions' 
            AND COLUMN_NAME IN ('log_file', 'exit_code')
        """))
        
        existing_columns = [row[0] for row in result]
        
        # 添加log_file字段
        if 'log_file' not in existing_columns:
            print("添加log_file字段...")
            conn.execute(text("""
                ALTER TABLE task_executions 
                ADD COLUMN log_file VARCHAR(500) COMMENT '日志文件路径'
            """))
            conn.commit()
            print("✓ log_file字段添加成功")
        else:
            print("✓ log_file字段已存在")
        
        # 添加exit_code字段
        if 'exit_code' not in existing_columns:
            print("添加exit_code字段...")
            conn.execute(text("""
                ALTER TABLE task_executions 
                ADD COLUMN exit_code INT COMMENT '退出码'
            """))
            conn.commit()
            print("✓ exit_code字段添加成功")
        else:
            print("✓ exit_code字段已存在")
        
        print("\n迁移完成！")

if __name__ == "__main__":
    migrate()
