#!/bin/bash

echo "🔄 重启 PySchedule v2.0 服务..."

# 停止服务
docker-compose down

# 等待完全停止
sleep 3

# 启动服务
docker-compose up -d

# 等待启动
sleep 15

# 检查状态
docker-compose ps

echo "✅ 重启完成"
