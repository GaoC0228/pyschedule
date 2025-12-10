# ========================================
# Stage 1: 构建阶段
# ========================================
FROM node:18-alpine as builder

WORKDIR /app

# ⭐ 使用淘宝npm镜像源加速
RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production || npm install

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# ========================================
# Stage 2: Nginx服务
# ========================================
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
