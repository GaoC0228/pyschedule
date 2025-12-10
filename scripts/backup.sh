#!/bin/bash

set -e

BACKUP_DIR="./backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pyschedule_backup_${DATE}.sql"

echo "🗄️  开始备份MySQL数据库..."

# 加载环境变量
if [ -f .env ]; then
    source .env
else
    echo "❌ 未找到.env文件"
    exit 1
fi

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份MySQL数据库
docker exec pyschedule-database mysqldump \
  -u root \
  -p${DB_ROOT_PASSWORD} \
  --single-transaction \
  --quick \
  --lock-tables=false \
  --routines \
  --triggers \
  --events \
  ${DB_NAME} > ${BACKUP_DIR}/${BACKUP_FILE}

echo "✅ SQL备份完成: ${BACKUP_FILE}"

# 压缩备份
gzip ${BACKUP_DIR}/${BACKUP_FILE}
echo "✅ 压缩完成: ${BACKUP_FILE}.gz"

# 备份volumes目录中的文件
echo "📂 备份应用数据文件..."
tar -czf ${BACKUP_DIR}/volumes_${DATE}.tar.gz \
  volumes/uploads \
  volumes/work \
  volumes/task_output \
  2>/dev/null || true

echo "✅ 应用数据备份完成"

# 计算文件大小
SQL_SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE}.gz | cut -f1)
VOLUMES_SIZE=$(du -h ${BACKUP_DIR}/volumes_${DATE}.tar.gz 2>/dev/null | cut -f1 || echo "0")

echo ""
echo "📊 备份信息："
echo "  数据库备份: ${SQL_SIZE}"
echo "  应用数据备份: ${VOLUMES_SIZE}"

# 清理旧备份
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
find $BACKUP_DIR -name "*.gz" -mtime +${RETENTION_DAYS} -delete
echo "🧹 清理完成：删除${RETENTION_DAYS}天前的备份"

echo ""
echo "📊 当前备份列表:"
ls -lh $BACKUP_DIR/*.gz 2>/dev/null || echo "无备份文件"
