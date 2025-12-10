# 🚀 新服务器部署指南

## 📋 环境要求

```bash
- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 内存
- 至少 10GB 磁盘空间
```

## 🔧 快速部署（5分钟完成）

### 1️⃣ 安装Docker和Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose（如果没有）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2️⃣ 克隆项目

```bash
# 从Gitee克隆
git clone https://gitee.com/你的用户名/pyschedule.git
cd pyschedule

# 或从GitHub克隆
git clone https://github.com/你的用户名/pyschedule.git
cd pyschedule
```

### 3️⃣ 配置环境变量（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（可选，使用默认配置也可以）
vi .env
```

**推荐修改的配置：**
```bash
# 数据库root密码（强烈建议修改）
DB_ROOT_PASSWORD=你的安全密码

# 数据库用户密码
DB_PASSWORD=你的数据库密码

# JWT密钥（生产环境必须修改）
SECRET_KEY=$(openssl rand -hex 32)
```

### 4️⃣ 一键启动

```bash
# 启动所有服务（首次启动会自动构建镜像，需要5-10分钟）
docker-compose up -d

# 查看启动进度
docker-compose logs -f
```

> 💡 **不需要手动创建目录或执行初始化脚本！**  
> Docker Compose 会自动创建所需的目录结构（volumes/、logs/ 等）

**启动过程说明：**
1. ⏳ 构建后端镜像（安装Python依赖）
2. ⏳ 构建前端镜像（安装Node.js依赖并打包）
3. ⏳ 启动MySQL数据库
4. ⏳ 初始化数据库表结构
5. ⏳ 创建管理员账户
6. ✅ 服务启动完成

### 5️⃣ 访问系统

```bash
# 本地访问
http://localhost/python/

# 远程访问（将IP替换为你的服务器IP）
http://你的服务器IP/python/
```

**默认登录账户：**
```
用户名: admin
密码: admin123
```

> ⚠️ **首次登录后请立即修改密码！**

---

## 🎯 常用命令

### 查看服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 应该看到3个容器都是healthy状态：
# - pyschedule-database  (healthy)
# - pyschedule-backend   (healthy)
# - pyschedule-frontend  (healthy)
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database

# 查看最近100行日志
docker-compose logs --tail=100 backend
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
docker-compose restart frontend
```

### 停止服务

```bash
# 停止所有服务（保留数据）
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 完全清理（包括数据卷，谨慎使用！）
docker-compose down -v
```

### 更新代码

```bash
# 拉取最新代码
git pull

# 重建并重启服务
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 📁 数据持久化位置

所有数据都保存在宿主机，容器删除后数据不会丢失：

```bash
volumes/
├── mysql/          # MySQL数据库文件
├── work/           # 用户工作区（Python脚本）
├── uploads/        # 上传的文件
└── task_data/      # 任务输入输出数据

logs/
├── backend/        # 后端日志
├── task_logs/      # 任务执行日志
└── nginx/          # Nginx访问日志

backend/
└── requirements.txt  # Python包列表（包管理持久化）
```

---

## 🔧 高级配置

### 修改访问端口

编辑 `docker-compose.yml`：

```yaml
services:
  frontend:
    ports:
      - "80:80"      # 改为其他端口，如 "8080:80"
```

### 配置外部Nginx反向代理

如果你有外部Nginx，参考以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /python/ {
        proxy_pass http://localhost:80/python/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket支持（Web终端需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 配置HTTPS

1. 安装certbot获取SSL证书
2. 修改frontend的nginx配置添加SSL
3. 或使用外部Nginx处理SSL

---

## ❓ 常见问题

### 1. 端口被占用

```bash
# 检查端口占用
sudo netstat -tuln | grep -E ':80|:3306|:8088'

# 停止占用端口的服务
sudo systemctl stop apache2  # 如果是Apache占用80端口
sudo systemctl stop nginx    # 如果是Nginx占用80端口
```

### 2. 容器启动失败

```bash
# 查看具体错误
docker-compose logs backend
docker-compose logs database

# 常见原因：
# - 磁盘空间不足: df -h
# - 内存不足: free -h
# - 端口冲突: 参考上面端口检查
```

### 3. 数据库连接失败

```bash
# 检查数据库容器状态
docker-compose ps database

# 查看数据库日志
docker-compose logs database

# 手动测试数据库连接
docker exec pyschedule-database mysqladmin ping -h localhost
```

### 4. 前端访问404

```bash
# 检查前端容器状态
docker-compose ps frontend

# 查看Nginx日志
docker-compose logs frontend

# 检查前端构建是否成功
docker exec pyschedule-frontend ls -la /usr/share/nginx/html/
```

### 5. 权限问题

```bash
# 确保当前用户在docker组
sudo usermod -aG docker $USER
newgrp docker

# 或使用sudo运行
sudo docker-compose up -d
```

---

## 🔐 安全建议

### 生产环境必须配置

1. **修改默认密码**
   - 登录后立即修改admin密码
   - 修改 `.env` 中的数据库密码

2. **配置防火墙**
   ```bash
   # 只开放必要端口
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **定期备份数据**
   ```bash
   # 备份数据卷
   tar -czf backup-$(date +%Y%m%d).tar.gz volumes/
   ```

4. **限制SSH访问**
   - 禁用root登录
   - 使用密钥认证
   - 修改SSH默认端口

---

## 📊 性能优化

### 资源限制

编辑 `docker-compose.yml` 添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 日志清理

```bash
# 清理Docker日志
docker system prune -a --volumes

# 设置日志大小限制（在docker-compose.yml中）
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 🆘 获取帮助

遇到问题？

1. 查看日志：`docker-compose logs -f`
2. 检查服务状态：`docker-compose ps`
3. 查看本文档的常见问题部分
4. 提交Issue到项目仓库

---

## ✅ 部署检查清单

- [ ] Docker和Docker Compose已安装
- [ ] 项目已克隆到本地
- [ ] 环境变量已配置（.env文件）
- [ ] 端口未被占用（80, 3306, 8088）
- [ ] 防火墙已配置（生产环境）
- [ ] 执行 `docker-compose up -d`
- [ ] 访问 `http://服务器IP/python/` 能打开登录页
- [ ] 使用admin/admin123能成功登录
- [ ] 已修改默认管理员密码
- [ ] 数据持久化目录已备份

🎉 **部署完成！享受使用吧！**
