-- 数据库会通过环境变量MYSQL_DATABASE自动创建
USE pyschedule;

-- 创建只读用户（用于远程查询）
CREATE USER IF NOT EXISTS 'pyschedule_readonly'@'%' IDENTIFIED BY 'readonly_password_change_me';
GRANT SELECT ON pyschedule.* TO 'pyschedule_readonly'@'%';

-- 创建备份用户
CREATE USER IF NOT EXISTS 'backup_user'@'%' IDENTIFIED BY 'backup_password_change_me';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER, RELOAD ON *.* TO 'backup_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 设置时区
SET time_zone = '+08:00';

-- 显示当前数据库信息
SELECT 
    'Database initialized successfully' AS status,
    DATABASE() AS current_database,
    NOW() AS current_datetime,
    @@time_zone AS timezone;
