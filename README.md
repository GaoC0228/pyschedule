# PySchedule - Python任务调度平台

![Version](https://img.shields.io/badge/version-2.5.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

> 一个功能强大的Python任务调度和管理平台，支持定时任务、在线编辑、数据库配置、审计日志等企业级功能。

---

## 📑 文档导航

📄 **本文档** - 项目介绍、功能特性、技术栈、项目结构  
📄 **[DEPLOY.md](./DEPLOY.md)** - 🚀 **新服务器部署指南**（推荐从这里开始）  
📄 **[GIT_UPLOAD_GUIDE.md](./GIT_UPLOAD_GUIDE.md)** - Git仓库上传和分享指南

---

## 📖 目录

- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [功能模块](#功能模块)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

---

## ✨ 核心功能

### 🎯 任务管理
- ✅ **可视化任务调度** - 基于APScheduler的Cron表达式定时任务
- ✅ **在线代码编辑** - 内置Monaco Editor，支持Python语法高亮和智能提示
- ✅ **实时日志查看** - 任务执行日志实时显示，支持下载
- ✅ **多参数支持** - 支持JSON/YAML配置、环境变量、命令行参数
- ✅ **批量操作** - 批量启用/禁用/删除任务
- ✅ **任务筛选** - 管理员可按创建者筛选任务

### 🔧 工作区
- ✅ **文件管理** - 多用户隔离的Python脚本工作区
- ✅ **在线编辑器** - 支持Python、JSON、YAML、Text等多种文件类型
- ✅ **集成终端** - 内置Web终端，支持实时命令执行
- ✅ **输出文件** - 自动管理任务输出的CSV、Excel、图表等文件
- ✅ **Web SSH终端** - 完整的Shell访问权限（管理员专用）
- ✅ **预装常用包** - pandas、numpy、openpyxl、pymongo、redis等开箱即用

### 💾 数据库配置
- ✅ **多数据库支持** - MongoDB、MySQL、PostgreSQL、Redis
- ✅ **动态导入** - 通过`from db_configs import xxx`直接使用配置
- ✅ **密码加密** - AES-256加密存储数据库密码
- ✅ **配置管理** - Web界面可视化管理数据库连接
- ✅ **使用示例** - 自动生成Python代码示例

### 👥 用户管理
- ✅ **角色权限** - 管理员/普通用户角色分离
- ✅ **在线状态** - 实时显示用户在线/离线状态
- ✅ **个人设置** - 用户可修改密码
- ✅ **审计日志** - 详细记录用户操作行为

### 🔐 安全特性
- ✅ **JWT认证** - 基于Token的身份验证
- ✅ **验证码** - 赛博朋克风格的Canvas验证码
- ✅ **密码加密** - bcrypt哈希存储
- ✅ **权限控制** - 基于角色的访问控制
- ✅ **审计追踪** - IP地址、操作记录、时间追踪

### 🎨 界面设计
- ✅ **赛博朋克登录页** - 霓虹风格、动态背景、打字机效果
- ✅ **响应式设计** - 完美适配桌面和移动端
- ✅ **现代UI** - Ant Design + Tailwind CSS
- ✅ **流畅动画** - Framer Motion平滑过渡

---

## 🛠️ 技术栈

### 后端
| 技术 | 版本 | 用途 |
|-----|------|------|
| **Python** | 3.8+ | 核心语言 |
| **FastAPI** | 最新 | Web框架 |
| **SQLAlchemy** | 最新 | ORM框架 |
| **APScheduler** | 3.x | 任务调度 |
| **PyMongo** | 最新 | MongoDB驱动 |
| **SQLite** | 3.x | 默认数据库 |
| **Cryptography** | 最新 | 密码加密 |
| **Pydantic** | 最新 | 数据验证 |

### 前端
| 技术 | 版本 | 用途 |
|-----|------|------|
| **React** | 18.x | UI框架 |
| **TypeScript** | 5.x | 类型安全 |
| **Vite** | 6.x | 构建工具 |
| **Ant Design** | 5.x | 组件库 |
| **Tailwind CSS** | 3.x | 样式框架 |
| **Monaco Editor** | 最新 | 代码编辑器 |
| **Framer Motion** | 最新 | 动画库 |
| **Xterm.js** | 5.x | 终端模拟器 |
| **Lucide React** | 最新 | 图标库 |

---

## 🚀 快速开始

### 环境要求
```bash
- Docker 20.10+
- Docker Compose 2.0+
```

### 🐳 Docker部署（推荐）

#### 1. 克隆项目
```bash
git clone <repository-url>
cd exec_python_web/v2
```

#### 2. 配置环境变量（可选）
```bash
cp .env.example .env
# 编辑 .env 文件修改数据库密码等配置
```

#### 3. 一键启动
```bash
docker-compose up -d
```

服务会自动：
- ✅ 创建MySQL数据库并初始化表结构
- ✅ 创建管理员账户（admin/admin123）
- ✅ 安装所有Python依赖（包括预装的常用包）
- ✅ 构建并启动前后端服务
- ✅ 配置Nginx反向代理

#### 4. 访问系统
```
前端界面: http://localhost/python/
后端API文档: http://localhost/python/api/docs
```

#### 5. 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 6. 停止服务
```bash
docker-compose down
```

### 📁 数据持久化

所有重要数据都已挂载到主机：
```
volumes/
├── mysql/          # 数据库数据
├── work/           # 用户工作区（脚本文件）
├── uploads/        # 上传文件
└── task_data/      # 任务输入输出数据

logs/
├── backend/        # 后端日志
└── task_logs/      # 任务执行日志

backend/requirements.txt  # Python包列表（持久化）
```

### 🔧 容器重建

当需要更新代码或重建容器时：
```bash
# 重建所有服务
docker-compose down
docker-compose build
docker-compose up -d

# 重建单个服务
docker-compose build backend
docker-compose up -d backend
```

> 💡 **数据库会自动迁移**：容器启动时会自动检查并添加新增的表字段，无需手动操作。

### 默认账户
```
用户名: admin
密码: admin123
角色: 管理员
权限: 完全权限（包括包管理）
```

> ⚠️ **生产环境请立即修改默认密码！**

---

## 📦 功能模块

### 1. 仪表盘
- **统计概览** - 总任务数、运行中任务、已完成任务、任务成功率
- **近期任务** - 最近10个任务的执行状态
- **快捷入口** - 快速访问任务管理、工作区等功能

### 2. 任务管理

#### 创建任务
```python
# 支持三种参数方式

# 方式1：环境变量
import os
task_id = os.getenv('TASK_ID')
output_dir = os.getenv('OUTPUT_DIR')
exec_date = os.getenv('EXEC_DATE')

# 方式2：配置文件
import json
with open('config.json') as f:
    config = json.load(f)

# 方式3：命令行参数
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--start-date', required=True)
args = parser.parse_args()
```

#### Cron表达式示例
```bash
# 每分钟执行
* * * * *

# 每天凌晨2点执行
0 2 * * *

# 每周一上午9点执行
0 9 * * MON

# 每月1号凌晨1点执行
0 1 1 * *

# 每小时的第15分钟执行
15 * * * *
```

### 3. 工作区

#### 文件结构
```
work/
├── admin/          # 管理员工作目录
├── user1/          # 用户1工作目录
└── user2/          # 用户2工作目录
```

#### 支持的文件类型
- **Python** (.py) - 语法高亮、智能提示
- **JSON** (.json) - 格式化、验证
- **YAML** (.yaml, .yml) - 语法支持
- **Text** (.txt, .md, .log) - 纯文本编辑
- **CSV** (.csv) - 数据文件
- **Excel** (.xlsx) - 数据文件

### 4. 数据库配置

#### 创建配置
1. 访问 **数据库配置** 页面
2. 点击 **新增配置**
3. 填写连接信息
4. 点击 **测试连接**
5. 保存配置

#### 使用配置
```python
# 在Python脚本中使用
from db_configs import mongo_prod as mongos

# 获取数据库连接
client = mongos.client
db = client['your_database']
collection = db['your_collection']

# 查询示例
results = collection.find({'status': 'active'})
for doc in results:
    print(doc)

# 插入示例
collection.insert_one({'name': 'test', 'value': 123})

# 关闭连接
client.close()
```

#### 切换环境
```python
# 测试环境
from db_configs import mongo_test as mongos

# 生产环境
from db_configs import mongo_prod as mongos

# 开发环境
from db_configs import mongo_dev as mongos
```

### 5. 用户管理

#### 用户角色
- **管理员 (admin)** - 所有权限，可管理用户、查看所有任务
- **普通用户 (user)** - 只能管理自己创建的任务和文件

#### 功能权限
| 功能 | 管理员 | 普通用户 |
|-----|--------|---------|
| 创建任务 | ✅ | ✅ |
| 查看所有任务 | ✅ | ❌ |
| 用户管理 | ✅ | ❌ |
| 审计日志 | ✅ | ❌ |
| 数据库配置 | ✅ | ✅ |
| 个人工作区 | ✅ | ✅ |

### 6. 审计日志

#### 记录内容
- **用户操作** - 登录、登出、创建、修改、删除
- **IP地址** - 记录操作来源IP
- **时间戳** - 精确到秒的操作时间
- **详细信息** - JSON格式的操作详情

#### 日志清理
- **按日期范围清理** - 指定开始和结束日期
- **保留最新日志** - 自动保留指定条数的最新日志
- **批量删除** - 支持大量日志的高效删除

---

## 📁 项目结构

```
v1/
├── backend/                    # 后端代码
│   ├── routers/               # API路由
│   │   ├── auth.py           # 认证接口
│   │   ├── tasks.py          # 任务接口
│   │   ├── users.py          # 用户接口
│   │   ├── workspace.py      # 工作区接口
│   │   ├── database.py       # 数据库配置接口
│   │   ├── audit.py          # 审计日志接口
│   │   └── terminal.py       # 终端接口
│   ├── models.py              # 数据模型
│   ├── schemas.py             # Pydantic模型
│   ├── database.py            # 数据库连接
│   ├── auth.py                # 认证逻辑
│   ├── audit.py               # 审计日志
│   ├── config.py              # 配置文件
│   ├── scheduler.py           # 任务调度器
│   ├── db_configs/            # 数据库配置模块
│   │   ├── __init__.py       # 动态导入实现
│   │   └── README.md         # 使用说明
│   ├── utils/                 # 工具函数
│   │   ├── crypto.py         # 加密解密
│   │   └── ip_utils.py       # IP工具
│   ├── work/                  # 用户工作区
│   └── main.py                # 应用入口
│
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── components/        # React组件
│   │   │   ├── Layout.tsx    # 布局组件
│   │   │   ├── PrivateRoute.tsx  # 路由守卫
│   │   │   └── login/        # 登录页组件
│   │   │       ├── Background.tsx     # 背景动画
│   │   │       ├── Captcha.tsx        # 验证码组件
│   │   │       ├── Input.tsx          # 输入框组件
│   │   │       ├── Button.tsx         # 按钮组件
│   │   │       └── Typewriter.tsx     # 打字机效果
│   │   ├── pages/             # 页面组件
│   │   │   ├── LoginNew.tsx   # 登录页面
│   │   │   ├── Dashboard.tsx  # 仪表盘
│   │   │   ├── Tasks.tsx      # 任务管理
│   │   │   ├── Workspace.tsx  # 工作区
│   │   │   ├── DatabaseConfig.tsx  # 数据库配置
│   │   │   ├── Users.tsx      # 用户管理
│   │   │   ├── AuditLogs.tsx  # 审计日志
│   │   │   └── Profile.tsx    # 个人设置
│   │   ├── contexts/          # React Context
│   │   │   └── AuthContext.tsx
│   │   ├── api/               # API封装
│   │   │   └── axios.ts
│   │   └── App.tsx            # 应用入口
│   ├── public/                # 静态资源
│   ├── tailwind.config.js     # Tailwind配置
│   ├── postcss.config.js      # PostCSS配置
│   ├── vite.config.ts         # Vite配置
│   └── package.json           # 依赖配置
│
├── data/                       # 数据目录
│   ├── database.db            # SQLite数据库
│   └── task_output/           # 任务输出文件
│
├── logs/                       # 日志目录
│   ├── backend.log            # 后端日志
│   └── frontend.log           # 前端日志
│
├── setup.sh                    # 安装脚本
├── start.sh                    # 启动脚本
├── stop.sh                     # 停止脚本
├── restart.sh                  # 重启脚本
├── status.sh                   # 状态检查脚本
├── build_production.sh         # 生产构建脚本
├── nginx_production.conf       # Nginx配置
├── .gitignore                  # Git忽略文件
├── SECURITY.md                 # 安全说明
├── TESTING.md                  # 测试说明
└── PROJECT_README.md           # 项目文档（本文件）
```

---

## ⚙️ 配置说明

### 后端配置 (backend/config.py)
```python
DATABASE_URL = "sqlite:///./data/database.db"  # 数据库路径
SECRET_KEY = "your-secret-key-here"            # JWT密钥
ENCRYPTION_KEY = "your-encryption-key"         # 数据加密密钥
ACCESS_TOKEN_EXPIRE_MINUTES = 43200            # Token过期时间（30天）
WORK_DIR = "./work"                            # 工作区路径
OUTPUT_DIR = "./data/task_output"              # 输出文件路径
```

### 前端配置 (frontend/vite.config.ts)
```typescript
server: {
  port: 3001,                    # 前端端口
  proxy: {
    '/api': {
      target: 'http://localhost:8088',  # 后端地址
      changeOrigin: true,
    },
  },
}
```

### Nginx配置 (nginx_production.conf)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /python/ {
        alias /opt/soft/exec_python_web/v1/frontend/dist/;
        try_files $uri $uri/ /python/index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🐳 部署指南

### 开发环境
```bash
# 启动所有服务
bash start.sh

# 查看服务状态
bash status.sh

# 停止所有服务
bash stop.sh

# 重启服务
bash restart.sh
```

### 生产环境

#### 1. 构建前端
```bash
bash build_production.sh
```

#### 2. 配置Nginx
```bash
# 复制Nginx配置
sudo cp nginx_production.conf /etc/nginx/sites-available/pyschedule
sudo ln -s /etc/nginx/sites-available/pyschedule /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### 3. 配置Systemd服务

**后端服务 (/etc/systemd/system/pyschedule-backend.service)**
```ini
[Unit]
Description=PySchedule Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/soft/exec_python_web/v1/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8088
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务**
```bash
sudo systemctl daemon-reload
sudo systemctl enable pyschedule-backend
sudo systemctl start pyschedule-backend
```

---

## 🔐 安全说明

### 认证机制
- **JWT Token** - Bearer Token认证
- **过期时间** - 默认30天自动过期
- **自动刷新** - 前端自动处理Token刷新

### 密码安全
- **bcrypt哈希** - 密码加密存储
- **AES-256加密** - 数据库密码加密
- **长度要求** - 最少6位字符

### 验证码
- **Canvas验证码** - 前端防止简单脚本攻击
- **自动刷新** - 验证失败自动刷新
- **不区分大小写** - 提升用户体验

### 权限控制
- **角色分离** - 管理员/普通用户
- **路由守卫** - 前端路由权限检查
- **API鉴权** - 后端接口权限验证

### 审计追踪
- **操作记录** - 所有关键操作记录
- **IP追踪** - 记录操作来源IP
- **时间戳** - 精确到秒的时间记录

> 详细安全说明请查看 [SECURITY.md](./SECURITY.md)

---

## 🧪 测试说明

### 后端测试
```bash
cd backend
pytest tests/ -v
```

### 前端测试
```bash
cd frontend
npm run test
```

> 详细测试说明请查看 [TESTING.md](./TESTING.md)

---

## ❓ 常见问题

### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :3001  # 前端
lsof -i :8088  # 后端

# 杀死进程
kill -9 <PID>
```

### 2. 数据库初始化失败
```bash
# 删除旧数据库
rm data/database.db

# 重新运行安装脚本
bash setup.sh
```

### 3. 前端构建失败
```bash
# 清除缓存
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

### 4. 任务执行失败
- 检查Python脚本语法
- 查看任务日志定位错误
- 确认环境变量和参数配置正确

### 5. 数据库连接失败
- 检查数据库配置是否正确
- 测试网络连接
- 确认密码未过期
- 查看防火墙设置

---

## 📋 更新日志

### v2.5.0 (2025-12-09)
- ✅ 新增赛博朋克风格登录页面
- ✅ 新增Canvas验证码组件
- ✅ 新增个人设置功能
- ✅ 优化登录错误提示
- ✅ 修复个人设置按钮问题
- ✅ 更新数据库配置示例代码

### v2.0.0
- ✅ 全新UI设计
- ✅ 数据库配置管理
- ✅ 工作区文件管理
- ✅ 集成终端
- ✅ 审计日志
- ✅ 批量操作

### v1.0.0
- ✅ 基础任务调度
- ✅ 用户管理
- ✅ 在线编辑器

---

## 📞 支持

### 技术支持
- **文档**: 查看本README和相关MD文档
- **日志**: 查看 `logs/` 目录下的日志文件
- **API文档**: http://localhost:8088/docs

### 贡献指南
欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

Copyright (c) 2025 PySchedule

---

**Developed with ❤️ by PySchedule Team**
