#!/bin/bash

# Python定时任务管理平台 - 状态查看脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "Python定时任务管理平台 - 服务状态"
echo "================================"
echo ""

# 检查后端服务
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✓ 后端服务: 运行中 (PID: $PID)"
        echo "  地址: http://localhost:8088"
        echo "  API文档: http://localhost:8088/docs"
    else
        echo "✗ 后端服务: 已停止 (PID文件存在但进程不存在)"
    fi
else
    echo "✗ 后端服务: 未运行"
fi

echo ""

# 检查前端服务
if [ -f "frontend.pid" ]; then
    PID=$(cat frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✓ 前端服务: 运行中 (PID: $PID)"
        echo "  地址: http://localhost:3001"
    else
        echo "✗ 前端服务: 已停止 (PID文件存在但进程不存在)"
    fi
else
    echo "✗ 前端服务: 未运行"
fi

echo ""

# 检查端口占用
echo "端口占用情况:"
if command -v netstat &> /dev/null; then
    echo "  8088端口: $(netstat -tuln | grep ':8088 ' > /dev/null && echo '占用' || echo '空闲')"
    echo "  3001端口: $(netstat -tuln | grep ':3001 ' > /dev/null && echo '占用' || echo '空闲')"
elif command -v ss &> /dev/null; then
    echo "  8088端口: $(ss -tuln | grep ':8088 ' > /dev/null && echo '占用' || echo '空闲')"
    echo "  3001端口: $(ss -tuln | grep ':3001 ' > /dev/null && echo '占用' || echo '空闲')"
else
    echo "  无法检测端口状态 (需要netstat或ss命令)"
fi

echo ""

# 检查conda环境
if command -v conda &> /dev/null; then
    eval "$(conda shell.bash hook)"
    if conda env list | grep -q "^exec_python_web "; then
        echo "✓ Conda环境: exec_python_web 已创建"
    else
        echo "✗ Conda环境: exec_python_web 未创建"
    fi
else
    echo "✗ Conda: 未安装"
fi

echo ""
echo "================================"
