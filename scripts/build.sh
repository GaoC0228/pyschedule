#!/bin/bash

echo "🔨 构建 PySchedule v2.0 Docker镜像..."

# 构建镜像
docker-compose build --no-cache

echo "✅ 镜像构建完成"
echo ""
echo "📊 镜像列表："
docker images | grep pyschedule
