-- 更新任务执行表结构，将日志从数据库改为文件存储
-- 执行时间: 2025-12-08

-- 1. 添加新字段
ALTER TABLE task_executions 
ADD COLUMN log_file VARCHAR(500) COMMENT '日志文件路径',
ADD COLUMN exit_code INT COMMENT '退出码';

-- 2. 删除旧字段（可选，如果要完全迁移）
-- ALTER TABLE task_executions 
-- DROP COLUMN output,
-- DROP COLUMN error;

-- 注意：如果要保留历史数据，可以不删除output和error字段
-- 新的执行记录将使用log_file字段

SELECT '任务执行表结构更新完成' AS status;
