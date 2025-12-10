#!/bin/bash

echo "📁 创建Docker持久化目录结构..."

# 创建volumes目录（Docker挂载卷）
mkdir -p volumes/mysql
mkdir -p volumes/uploads
mkdir -p volumes/work
mkdir -p volumes/task_output

# 创建日志目录
mkdir -p logs/mysql
mkdir -p logs/backend
mkdir -p logs/nginx

# 创建备份目录
mkdir -p backups/mysql

# 创建数据库初始化脚本目录
mkdir -p database/init-scripts

# 设置权限（MySQL需要）
chmod -R 777 volumes/mysql
chmod -R 777 logs/mysql

echo "✅ 目录创建完成"
echo ""
echo "📊 目录结构："
ls -lR volumes logs backups | head -50
