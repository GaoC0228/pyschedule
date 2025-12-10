#!/bin/bash

set -e

echo "🚀 启动 PySchedule v2.0 Docker服务..."

# 1. 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，从模板复制..."
    cp .env.example .env
    echo "❗ 请编辑.env文件，修改数据库密码等配置"
    echo "   vi .env"
    exit 1
fi

# 2. 创建必要目录
echo "📁 检查目录结构..."
bash scripts/init-directories.sh

# 3. 启动服务
echo "🐳 启动Docker容器..."
docker-compose up -d

# 4. 等待服务就绪
echo "⏳ 等待服务启动..."
sleep 15

# 5. 检查服务状态
echo ""
echo "📊 服务状态："
docker-compose ps

echo ""
echo "✅ 启动完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 访问地址："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  前端:    http://localhost:3001"
echo "  后端API: http://localhost:8088/docs"
echo "  MySQL:   localhost:3306"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 查看日志："
echo "  docker-compose logs -f"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f database"
