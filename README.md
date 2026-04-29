# Admin Dashboard - 股票基金管理后台项目

## 项目简介

这是一个股票基金管理后台系统，包含前后端分离的架构设计。前端使用 Vue 3 + Vite 构建，后端使用 Python FastAPI 框架。

## 项目结构

```
fundcrawler/
├── backend/                 # Python FastAPI 后端
│   ├── api/                 # API 路由
│   │   ├── auth.py         # 认证相关 API
│   │   ├── users.py        # 用户管理 API
│   │   └── dashboard.py    # 仪表盘 API
│   ├── core/               # 核心配置目录
│   ├── main.py             # FastAPI 应用入口
│   ├── models.py           # 数据库模型
│   ├── schemas.py          # Pydantic 数据模型
│   ├── auth.py             # 认证和授权
│   ├── database.py         # 数据库配置
│   ├── init_db.py          # 数据库初始化脚本
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API 调用模块
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面视图
│   │   ├── App.vue        # 根组件
│   │   └── main.js        # 应用入口
│   ├── package.json
│   └── vite.config.js
│
└── docs/                   # 项目文档
```

## 技术栈

### 后端
- **FastAPI**: 现代、高性能的 Python Web 框架
- **SQLAlchemy 2.0**: 异步 ORM 数据库操作
- **asyncmy**: MySQL 异步驱动程序
- **Pydantic 2.0**: 数据验证
- **Python-Jose**: JWT Token 生成和验证
- **Passlib**: 密码加密
- **MySQL**: 数据库

### 前端
- **Vue 3**: 最新版本的 Vue 框架
- **Vite**: 快速的开发服务器和构建工具
- **Vue Router**: 路由管理
- **Pinia**: 状态管理
- **Axios**: HTTP 请求库

## 环境要求

### 后端
- Python 3.11+
- MySQL 5.7+ 或 MySQL 8.0+

### 前端
- Node.js 16+
- npm 8+

## 快速开始

### 1. 环境配置

#### Python 环境
确认使用 Python 3.11：
```bash
python --version
# 应显示 Python 3.11.x
```

#### MySQL 数据库
确保 MySQL 服务已启动，并创建数据库：
```sql
CREATE DATABASE admin_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端启动

1. 进入后端目录：
```bash
cd d:\code\fundcrawler\backend
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. （可选）配置数据库连接：
编辑 `database.py` 中的 `DATABASE_URL`，或设置环境变量：
```bash
set DATABASE_URL=mysql+asyncmy://root:your_password@localhost:3306/admin_dashboard?charset=utf8mb4
```

4. 初始化数据库：
```bash
python init_db.py
```

5. 启动开发服务器：
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- 后端服务地址: http://localhost:8000
- API 文档地址: http://localhost:8000/docs

### 3. 前端启动

1. 进入前端目录：
```bash
cd d:\code\fundcrawler\frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
# 或
npx vite
```

- 前端服务地址: http://localhost:5173

### 4. 默认登录账户

- **用户名**: admin
- **密码**: admin123

## 项目配置文件

### 后端配置文件

| 文件 | 说明 |
|------|------|
| `backend/database.py` | 数据库连接配置 |
| `backend/core/config.py` | 核心配置（可配置数据库参数） |
| `backend/auth.py` | 认证配置（SECRET_KEY） |
| `backend/requirements.txt` | Python 依赖列表 |

### 前端配置文件

| 文件 | 说明 |
|------|------|
| `frontend/vite.config.js` | Vite 配置 |
| `frontend/package.json` | npm 依赖和脚本 |
| `frontend/src/api/index.js` | API 基础配置 |

## 数据库配置说明

数据库连接 URL 格式：
```
mysql+asyncmy://用户名:密码@主机:端口/数据库名?charset=utf8mb4
```

默认配置（开发环境）：
```
mysql+asyncmy://root:999888777@localhost:3306/admin_dashboard?charset=utf8mb4
```

### 环境变量配置

可以通过设置 `DATABASE_URL` 环境变量来覆盖默认配置：
```bash
set DATABASE_URL=mysql+asyncmy://user:password@host:port/database?charset=utf8mb4
```

## 启动脚本（可选）

为方便启动，可以创建批处理文件：

**启动后端.bat**
```batch
@echo off
cd /d %~dp0backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端.bat**
```batch
@echo off
cd /d %~dp0frontend
npm run dev
```

## API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的 API 文档（Swagger UI）。

### 主要 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/register | 用户注册 |
| GET | /api/auth/me | 获取当前用户信息 |
| GET | /api/users/ | 获取用户列表 |
| GET | /api/users/{id} | 获取单个用户 |
| PUT | /api/users/{id} | 更新用户 |
| DELETE | /api/users/{id} | 删除用户 |
| GET | /api/dashboard/stats | 获取统计数据 |
| GET | /api/dashboard/activity | 获取最近活动 |

## 常见问题

### 1. ModuleNotFoundError: No module named 'sqlalchemy'
确保使用正确的 Python 版本（3.11），并已安装依赖：
```bash
pip install -r requirements.txt
```

### 2. (1049, "Unknown database 'admin_dashboard'")
数据库不存在，需要先创建：
```bash
python init_db.py
```
或手动在 MySQL 中创建数据库。

### 3. aiomysql 连接错误
请确保已安装 `asyncmy` 而非 `aiomysql`：
```bash
pip install asyncmy==0.2.9
```

### 4. bcrypt 版本不兼容
如果遇到 bcrypt 相关错误，请使用 pbkdf2_sha256：
项目已配置使用 `pbkdf2_sha256` 作为默认密码哈希算法。

## 项目维护

### 更新依赖

后端：
```bash
pip install -r requirements.txt --upgrade
```

前端：
```bash
npm install
```

### 数据库迁移

如需修改数据库模型：
1. 修改 `models.py` 中的模型定义
2. 重新运行 `python init_db.py`（仅用于开发环境）
3. 生产环境请使用 Alembic 进行数据库迁移

## License

MIT License