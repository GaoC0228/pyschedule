#!/bin/bash

# Python定时任务管理平台 - 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "Python定时任务管理平台 - 启动服务"
echo "================================"

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未检测到conda"
    exit 1
fi

# 初始化conda
eval "$(conda shell.bash hook)"

# 检查环境是否存在
if ! conda env list | grep -q "^exec_python_web "; then
    echo "错误: conda环境 exec_python_web 不存在"
    echo "请先运行: ./setup.sh"
    exit 1
fi

# 激活环境
echo "激活conda环境: exec_python_web"
conda activate exec_python_web

# 检查PID文件
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "后端服务已在运行 (PID: $PID)"
    else
        echo "清理旧的PID文件"
        rm -f backend.pid
    fi
fi

if [ -f "frontend.pid" ]; then
    PID=$(cat frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "前端服务已在运行 (PID: $PID)"
    else
        echo "清理旧的PID文件"
        rm -f frontend.pid
    fi
fi

# 启动后端服务
if [ ! -f "backend.pid" ]; then
    echo "启动后端服务..."
    cd backend
    nohup python main.py > ../logs/backend.log 2>&1 &
    echo $! > ../backend.pid
    cd ..
    echo "后端服务已启动 (PID: $(cat backend.pid))"
    echo "后端地址: http://localhost:8088"
    echo "API文档: http://localhost:8088/docs"
fi

# 启动前端服务
if [ ! -f "frontend.pid" ]; then
    if command -v node &> /dev/null; then
        echo "启动前端服务..."
        cd frontend
        nohup npm run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        cd ..
        echo "前端服务已启动 (PID: $FRONTEND_PID)"
        echo "前端地址: http://localhost:3001"
    else
        echo "警告: 未检测到Node.js，跳过前端启动"
    fi
fi

echo ""
echo "================================"
echo "服务启动完成！"
echo "================================"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3001"
echo "  后端API: http://localhost:8088"
echo "  API文档: http://localhost:8088/docs"
echo ""
echo "查看日志:"
echo "  后端: tail -f logs/backend.log"
echo "  前端: tail -f logs/frontend.log"
echo ""
