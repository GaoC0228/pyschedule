#!/bin/bash

set -e

echo "🔨 开始构建 PySchedule v2.0 Docker镜像"
echo "========================================"
echo ""

# 进入项目目录
cd "$(dirname "$0")/.."

# 显示构建信息
echo "📋 构建配置："
echo "  后端镜像: pyschedule-backend:2.0"
echo "  前端镜像: pyschedule-frontend:2.0"
echo ""

# 构建选项
BUILD_CACHE="--no-cache"
if [ "$1" == "--cache" ]; then
    BUILD_CACHE=""
    echo "✅ 使用缓存构建"
else
    echo "⚠️  无缓存构建（首次构建推荐）"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏗️  构建后端镜像..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker build $BUILD_CACHE -t pyschedule-backend:2.0 ./backend

if [ $? -eq 0 ]; then
    echo "✅ 后端镜像构建成功"
else
    echo "❌ 后端镜像构建失败"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 构建前端镜像..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker build $BUILD_CACHE -t pyschedule-frontend:2.0 ./frontend

if [ $? -eq 0 ]; then
    echo "✅ 前端镜像构建成功"
else
    echo "❌ 前端镜像构建失败"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 所有镜像构建完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 显示镜像列表
echo "📊 构建的镜像："
docker images | grep pyschedule

echo ""
echo "🧹 清理虚悬镜像（dangling images）..."
DANGLING=$(docker images -f "dangling=true" -q)
if [ -n "$DANGLING" ]; then
    docker rmi $DANGLING 2>/dev/null || true
    echo "✅ 已清理虚悬镜像"
else
    echo "✅ 无虚悬镜像需要清理"
fi

echo ""
echo "🎯 下一步操作："
echo "  1. 启动服务: bash scripts/start.sh"
echo "  2. 查看日志: docker-compose logs -f"
echo "  3. 访问系统: http://localhost:3001"
echo ""
