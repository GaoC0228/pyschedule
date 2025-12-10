#!/bin/bash
set -e

echo "🚀 启动 PySchedule Backend..."
echo ""

# 等待数据库就绪
echo "⏳ 等待数据库连接..."
for i in {1..30}; do
    if python -c "from database import engine; engine.connect()" 2>/dev/null; then
        echo "✅ 数据库连接成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 数据库连接超时"
        exit 1
    fi
    sleep 1
done

echo ""
echo "📊 初始化数据库..."
echo "🔄 升级数据库结构..."
python -c "from utils.db_migration import upgrade_database; upgrade_database()"
echo ""
echo "👤 初始化管理员账户..."
python init_admin.py

echo ""
echo "🎯 启动应用服务..."
exec python main.py
