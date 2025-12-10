#!/bin/bash

echo "⚠️  警告：此操作将删除所有容器、镜像和Docker数据！"
read -p "确认继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo "🧹 清理 PySchedule v2.0..."

# 停止并删除容器
docker-compose down -v

# 删除镜像
docker rmi pyschedule-backend:2.0 pyschedule-frontend:2.0 2>/dev/null || true

# 询问是否删除持久化数据
read -p "是否删除Docker持久化数据（volumes目录）？(yes/no): " delete_data

if [ "$delete_data" == "yes" ]; then
    echo "🗑️  删除Docker数据..."
    rm -rf volumes/mysql/*
    rm -rf volumes/uploads/*
    rm -rf volumes/work/*
    rm -rf volumes/task_output/*
    rm -rf logs/*
    echo "✅ Docker数据已删除"
    echo "💡 原有的data目录未受影响"
fi

echo "✅ 清理完成"
