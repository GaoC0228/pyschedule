# 数据库配置使用说明

## 快速开始

### 1. 在Web界面创建配置
访问 `http://localhost:3001/database-config` 创建数据库配置，例如：
- 配置名称：`mongo_test`
- 数据库类型：MongoDB
- 填写连接信息

### 2. 在Python脚本中使用

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from db_configs import mongo_test as mongos  # 只需这一行！

client = mongos.mongo_connect()
db = client['your_database']
collection = db['your_collection']

# 你的代码...

client.close()
```

## 切换环境

只需修改配置名：

```python
# 测试环境
from db_configs import mongo_test as mongos

# 生产环境  
from db_configs import mongo_prod as mongos

# 开发环境
from db_configs import mongo_dev as mongos
```

## 注意事项

1. **无需任何路径设置**，系统已通过 `.pth` 文件自动配置

2. **支持任意深度的子目录**，无论脚本在哪里都可以直接导入

3. **配置名必须在Web界面先创建**

4. **密码自动加密存储**，无需担心安全问题

## 技术说明

系统通过在Python site-packages目录创建 `db_configs.pth` 文件，自动将backend目录添加到Python路径中，因此无需在脚本中手动设置路径。
