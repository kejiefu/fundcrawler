# FundCrawler - 股票基金系统

## 项目简介

FundCrawler 是一个股票基金系统，采用前后端分离架构，提供用户管理、菜单管理、A股数据同步等功能。系统支持定时同步沪深京A股实时行情数据，为投资分析提供数据支撑。

## 核心功能

### 用户管理
- 用户注册、登录、认证
- JWT Token 身份验证
- 用户权限管理（超级管理员/普通用户）
- 用户信息维护

### 菜单管理
- 动态菜单配置
- 多级菜单支持
- 菜单权限控制

### A股数据服务
- 沪深京A股基本信息实时同步
- 股票行情数据（价格、涨跌幅、成交量等）
- 财务指标数据（市盈率、市净率、股息率等）
- 定时自动同步，可配置同步间隔

### 仪表盘
- 数据概览展示
- 系统状态监控

## 项目结构

```
fundcrawler/
├── backend/                    # FastAPI 后端服务
│   ├── api/                    # API 路由模块
│   │   ├── auth.py            # 认证相关 API
│   │   ├── users.py           # 用户管理 API
│   │   ├── menus.py           # 菜单管理 API
│   │   ├── stocks.py          # 股票数据 API
│   │   └── dashboard.py       # 仪表盘 API
│   ├── core/                   # 核心配置
│   │   └── config.py          # 配置管理
│   ├── scripts/                # 脚本工具
│   │   └── sync_a_share_basic.py  # A股数据同步脚本
│   ├── main.py                 # 应用入口
│   ├── models.py               # 数据库模型
│   ├── schemas.py              # Pydantic 数据模型
│   ├── database.py             # 数据库连接配置
│   ├── init_db.py              # 数据库初始化
│   └── requirements.txt        # Python 依赖
│
├── frontend/                   # Vue 3 前端应用
│   ├── src/
│   │   ├── api/               # API 调用封装
│   │   ├── components/        # 公共组件
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── views/             # 页面视图
│   │   │   ├── DashboardView.vue    # 仪表盘页面
│   │   │   ├── FundListView.vue     # 基金列表页面
│   │   │   ├── LoginView.vue        # 登录页面
│   │   │   ├── MenuView.vue         # 菜单管理页面
│   │   │   ├── ProfileView.vue      # 个人中心页面
│   │   │   ├── StockListView.vue    # 股票列表页面
│   │   │   └── UsersView.vue        # 用户管理页面
│   │   ├── App.vue            # 根组件
│   │   └── main.js            # 应用入口
│   ├── package.json
│   └── vite.config.js
│
├── jobs/                       # 定时任务服务
│   ├── core/                   # 核心配置
│   │   └── config.py          # 任务配置
│   ├── db/                     # 数据库模块
│   │   ├── database.py        # 数据库连接
│   │   └── models.py          # 数据模型
│   ├── jobs/                   # 任务模块
│   │   └── a_share_basic_sync.py  # A股数据同步任务
│   ├── main.py                 # 任务服务入口
│   └── requirements.txt        # Python 依赖
│
└── docs/                       # 项目文档
    ├── ddl/                    # 数据库定义
    │   ├── init.sql           # 初始化脚本
    │   └── schema.sql         # 表结构
    ├── api.md                  # API 文档
    ├── database.md             # 数据库文档
    └── deployment.md           # 部署指南
```

## 技术栈

### 后端服务 (Backend)
| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.104.1 | 高性能 Web 框架 |
| SQLAlchemy | 2.0.23 | 异步 ORM |
| asyncmy | 0.2.9 | MySQL 异步驱动 |
| Pydantic | 2.5.0 | 数据验证 |
| python-jose | 3.3.0 | JWT Token 处理 |
| Passlib | 1.7.4 | 密码加密 |
| akshare | 1.14.0+ | A股数据源 |
| pandas | 2.0.0+ | 数据处理 |

### 前端应用 (Frontend)
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.3.8 | 渐进式框架 |
| Vite | 5.0.0 | 构建工具 |
| Vue Router | 4.2.5 | 路由管理 |
| Pinia | 2.1.7 | 状态管理 |
| Axios | 1.6.2 | HTTP 客户端 |

### 数据库
- MySQL 5.7+ 或 MySQL 8.0+

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | 3.11+ |
| Node.js | 16+ |
| npm | 8+ |
| MySQL | 5.7+ / 8.0+ |

## 快速开始

### 1. 数据库准备

创建数据库：
```sql
CREATE DATABASE admin_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端服务启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
# Windows
set DATABASE_URL=mysql+asyncmy://root:password@localhost:3306/admin_dashboard?charset=utf8mb4
# Linux/Mac
export DATABASE_URL=mysql+asyncmy://root:password@localhost:3306/admin_dashboard?charset=utf8mb4

# 初始化数据库
python init_db.py

# 启动服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务地址：
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 3. 前端应用启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址: http://localhost:5173

### 4. 定时任务服务启动（可选）

```bash
# 进入 jobs 目录
cd jobs

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# Windows
set DATABASE_URL=mysql+asyncmy://root:password@localhost:3306/admin_dashboard?charset=utf8mb4
# Linux/Mac
export DATABASE_URL=mysql+asyncmy://root:password@localhost:3306/admin_dashboard?charset=utf8mb4

# 启动任务服务
python main.py
```

任务服务配置项（在 `jobs/core/config.py` 中设置）：
- `a_share_basic_sync_enabled`: 是否启用 A股同步任务
- `a_share_basic_sync_interval_seconds`: 同步间隔（秒）

### 5. 默认登录账户

| 字段 | 值 |
|------|------|
| 用户名 | admin |
| 密码 | admin123 |

## 配置说明

### 后端配置

| 配置项 | 文件位置 | 说明 |
|--------|----------|------|
| 数据库连接 | `backend/database.py` | DATABASE_URL 环境变量 |
| 核心配置 | `backend/core/config.py` | 应用配置 |
| JWT 密钥 | `backend/auth.py` | SECRET_KEY |
| CORS 配置 | `backend/main.py` | 跨域设置 |

### 前端配置

| 配置项 | 文件位置 | 说明 |
|--------|----------|------|
| API 地址 | `frontend/src/api/index.js` | 后端 API 地址 |
| 构建配置 | `frontend/vite.config.js` | Vite 配置 |

### Jobs 配置

| 配置项 | 文件位置 | 说明 |
|--------|----------|------|
| 同步开关 | `jobs/core/config.py` | a_share_basic_sync_enabled |
| 同步间隔 | `jobs/core/config.py` | a_share_basic_sync_interval_seconds |

## 数据库模型

### 用户表 (users)
- 用户基本信息
- 认证信息
- 权限标识

### 菜单表 (menus)
- 菜单名称、路径、图标
- 层级关系
- 权限控制

### A股基本信息表 (a_share_stock_basic)
- 证券代码、名称
- 实时行情（价格、涨跌幅、成交量等）
- 财务指标（市盈率、市净率、股息率等）
- 市值信息

## API 概览

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| 认证 | `/auth` | 登录、注册、Token 刷新 |
| 用户 | `/users` | 用户 CRUD |
| 菜单 | `/menus` | 菜单 CRUD |
| 股票 | `/stocks` | A股数据查询 |
| 仪表盘 | `/dashboard` | 数据统计 |

完整 API 文档请访问: http://localhost:8000/docs

## 开发指南

### 代码规范
项目遵循以下编码规范：
- 避免不必要的对象复制
- 提前返回，减少嵌套
- 使用有意义的命名
- 函数职责单一

详细规范请参考 `.trae/rules/` 目录下的规范文档。

### 提交规范
- feat: 新功能
- fix: 修复 Bug
- docs: 文档更新
- refactor: 代码重构
- style: 代码格式调整

## 部署指南

详细的部署指南请参考 [docs/deployment.md](docs/deployment.md)，包含：
- 开发环境部署
- 生产环境部署
- Docker 部署
- Nginx 配置
- HTTPS 配置
- 性能优化

## 许可证

MIT License
