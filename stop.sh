#!/bin/bash

# Python定时任务管理平台 - 停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "Python定时任务管理平台 - 停止服务"
echo "================================"

# 函数：杀死进程及其所有子进程
kill_process_tree() {
    local pid=$1
    local children=$(pgrep -P $pid)
    
    # 先杀死所有子进程
    for child in $children; do
        kill_process_tree $child
    done
    
    # 再杀死父进程
    if ps -p $pid > /dev/null 2>&1; then
        kill $pid 2>/dev/null || true
        sleep 0.5
        if ps -p $pid > /dev/null 2>&1; then
            kill -9 $pid 2>/dev/null || true
        fi
    fi
}

# 停止后端服务
echo "停止后端服务..."
BACKEND_COUNT=0

if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "  - 停止主进程 (PID: $PID)"
        kill_process_tree $PID
        BACKEND_COUNT=$((BACKEND_COUNT + 1))
    fi
    rm -f backend.pid
fi

# 查找并杀死所有uvicorn相关进程
UVICORN_PIDS=$(pgrep -f "uvicorn.*main:app" 2>/dev/null || true)
if [ ! -z "$UVICORN_PIDS" ]; then
    for pid in $UVICORN_PIDS; do
        echo "  - 清理残留的uvicorn进程 (PID: $pid)"
        kill_process_tree $pid
        BACKEND_COUNT=$((BACKEND_COUNT + 1))
    done
fi

if [ $BACKEND_COUNT -gt 0 ]; then
    echo "后端服务已停止 (共清理 $BACKEND_COUNT 个进程)"
else
    echo "后端服务未运行"
fi

# 停止前端服务
echo "停止前端服务..."
FRONTEND_COUNT=0

if [ -f "frontend.pid" ]; then
    PID=$(cat frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "  - 停止主进程 (PID: $PID)"
        kill_process_tree $PID
        FRONTEND_COUNT=$((FRONTEND_COUNT + 1))
    fi
    rm -f frontend.pid
fi

# 查找并杀死所有vite相关进程
VITE_PIDS=$(pgrep -f "node.*vite" 2>/dev/null || true)
if [ ! -z "$VITE_PIDS" ]; then
    for pid in $VITE_PIDS; do
        # 确保是我们项目的vite进程
        if ps -p $pid -o cmd= | grep -q "$SCRIPT_DIR"; then
            echo "  - 清理残留的vite进程 (PID: $pid)"
            kill_process_tree $pid
            FRONTEND_COUNT=$((FRONTEND_COUNT + 1))
        fi
    done
fi

# 查找并杀死所有esbuild相关进程
ESBUILD_PIDS=$(pgrep -f "esbuild.*--service" 2>/dev/null || true)
if [ ! -z "$ESBUILD_PIDS" ]; then
    for pid in $ESBUILD_PIDS; do
        if ps -p $pid -o cmd= | grep -q "$SCRIPT_DIR"; then
            echo "  - 清理残留的esbuild进程 (PID: $pid)"
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
            FRONTEND_COUNT=$((FRONTEND_COUNT + 1))
        fi
    done
fi

if [ $FRONTEND_COUNT -gt 0 ]; then
    echo "前端服务已停止 (共清理 $FRONTEND_COUNT 个进程)"
else
    echo "前端服务未运行"
fi

echo ""
echo "所有服务已停止"
echo ""
