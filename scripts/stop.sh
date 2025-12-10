#!/bin/bash

echo "🛑 停止 PySchedule v2.0 服务..."

docker-compose down

echo "✅ 服务已停止"
echo ""
echo "💡 提示："
echo "  - 数据已保存在 ./volumes 目录"
echo "  - 日志已保存在 ./logs 目录"
echo "  - 重启服务: bash scripts/start.sh"
