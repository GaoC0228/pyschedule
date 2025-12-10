# ========================================
# Stage 1: 基础环境
# ========================================
FROM python:3.10-slim as base

WORKDIR /app

# ⭐ 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org/debian-security|mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ========================================
# Stage 2: 依赖安装
# ========================================
FROM base as builder

# 复制依赖文件
COPY requirements.txt .

# ⭐ 使用阿里云pip镜像源加速
RUN pip install --no-cache-dir --user -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# ========================================
# Stage 3: 生产镜像
# ========================================
FROM python:3.10-slim

WORKDIR /app

# ⭐ 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org/debian-security|mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从builder复制Python包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs work uploads data/task_output

# 设置启动脚本权限
RUN chmod +x docker-entrypoint.sh

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8088/ || exit 1

# 暴露端口
EXPOSE 8088

# 使用启动脚本（会自动初始化管理员账户）
CMD ["./docker-entrypoint.sh"]
