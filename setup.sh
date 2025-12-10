#!/bin/bash

# Python定时任务管理平台 - 环境初始化脚本

set -e

echo "================================"
echo "Python定时任务管理平台 - 环境初始化"
echo "================================"

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未检测到conda，请先安装Anaconda或Miniconda"
    exit 1
fi

# 初始化conda
eval "$(conda shell.bash hook)"

# 检查环境是否存在
if conda env list | grep -q "^exec_python_web "; then
    echo "检测到已存在的conda环境: exec_python_web"
    read -p "是否删除并重新创建? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "删除现有环境..."
        conda env remove -n exec_python_web -y
    else
        echo "使用现有环境"
    fi
fi

# 创建conda环境
if ! conda env list | grep -q "^exec_python_web "; then
    echo "创建conda环境: exec_python_web (Python 3.10)"
    conda create -n exec_python_web python=3.10 -y
fi

# 激活环境
echo "激活conda环境..."
conda activate exec_python_web

# 安装后端依赖
echo "安装后端Python依赖..."
cd backend
pip install -r requirements.txt
cd ..

# 检查MySQL连接
echo ""
echo "请确保MySQL 8已安装并运行"
read -p "MySQL数据库地址 [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "MySQL端口 [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}

read -p "MySQL用户名 [root]: " DB_USER
DB_USER=${DB_USER:-root}

read -sp "MySQL密码: " DB_PASSWORD
echo

read -p "数据库名称 [python_task_platform]: " DB_NAME
DB_NAME=${DB_NAME:-python_task_platform}

# 创建.env文件
echo "创建后端配置文件..."
cat > backend/.env << EOF
DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760
LOG_LEVEL=INFO
EOF

# 创建数据库
echo "创建数据库..."
mysql -h${DB_HOST} -P${DB_PORT} -u${DB_USER} -p${DB_PASSWORD} -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || echo "数据库可能已存在或需要手动创建"

# 初始化数据库
echo "初始化数据库表和默认管理员账户..."
cd backend
python init_db.py
cd ..

# 安装前端依赖
echo ""
echo "安装前端依赖..."
if ! command -v node &> /dev/null; then
    echo "警告: 未检测到Node.js，请先安装Node.js"
    echo "跳过前端依赖安装"
else
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "================================"
echo "环境初始化完成！"
echo "================================"
echo ""
echo "默认管理员账户:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "使用以下命令启动服务:"
echo "  ./start.sh    # 启动服务"
echo "  ./stop.sh     # 停止服务"
echo "  ./restart.sh  # 重启服务"
echo "  ./status.sh   # 查看状态"
echo ""
