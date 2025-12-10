#!/bin/bash

# Python定时任务管理平台 - 重启脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "Python定时任务管理平台 - 重启服务"
echo "================================"
echo ""

# 停止服务
./stop.sh

echo ""
echo "等待服务完全停止..."
sleep 3

# 启动服务
./start.sh
