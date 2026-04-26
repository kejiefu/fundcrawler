# Admin Dashboard - 管理后台项目

## 项目简介

这是一个完整的管理后台系统，包含前后端分离的架构设计。前端使用 Vue 3 + Vite 构建，后端使用 Python FastAPI 框架。

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
│   ├── database.py          # 数据库配置
│   ├── init_db.py          # 数据库初始化脚本
│   └── requirements.txt     # Python 依赖
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API 调用模块
│   │   ├── components/    # 公共组件
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
- **SQLAlchemy**: 异步 ORM 数据库操作
- **Pydantic**: 数据验证
- **Python-Jose**: JWT Token 生成和验证
- **Passlib**: 密码加密
- **SQLite**: 轻量级数据库

### 前端
- **Vue 3**: 最新版本的 Vue 框架
- **Vite**: 快速的开发服务器和构建工具
- **Vue Router**: 路由管理
- **Pinia**: 状态管理
- **Axios**: HTTP 请求库

## 功能特性

### 认证系统
- ✅ JWT Token 认证
- ✅ 用户登录/注册
- ✅ Token 自动刷新
- ✅ 密码加密存储

### 用户管理
- ✅ 用户列表查看
- ✅ 用户信息编辑
- ✅ 用户删除
- ✅ 用户状态管理

### 仪表盘
- ✅ 统计概览
- ✅ 用户统计
- ✅ 系统状态
- ✅ 最近活动

### 个人中心
- ✅ 查看个人信息
- ✅ 编辑个人资料
- ✅ 修改密码

## 快速开始

### 后端启动

1. 进入后端目录并安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 初始化数据库并创建管理员账户：
```bash
python init_db.py
```

3. 启动开发服务器：
```bash
python main.py
# 或者
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行

API 文档地址：http://localhost:8000/docs

### 前端启动

1. 进入前端目录并安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

前端服务将在 http://localhost:5173 运行

### 默认登录账户

- **用户名**: admin
- **密码**: admin123

## API 文档

### 认证接口

#### 登录
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 注册
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "full_name": "New User",
  "password": "password123"
}
```

#### 获取当前用户信息
```
GET /api/auth/me
Authorization: Bearer <token>
```

### 用户管理接口

#### 获取用户列表
```
GET /api/users/?skip=0&limit=100
Authorization: Bearer <token>
```

#### 获取单个用户
```
GET /api/users/{user_id}
Authorization: Bearer <token>
```

#### 更新用户
```
PUT /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "is_active": true
}
```

#### 删除用户
```
DELETE /api/users/{user_id}
Authorization: Bearer <token>
```

#### 获取用户统计
```
GET /api/users/stats/count
Authorization: Bearer <token>
```

### 仪表盘接口

#### 获取统计数据
```
GET /api/dashboard/stats
Authorization: Bearer <token>
```

#### 获取最近活动
```
GET /api/dashboard/activity
Authorization: Bearer <token>
```

## 前端页面说明

### 登录页面 (`/login`)
- 用户名密码输入
- 表单验证
- 错误提示
- 加载状态

### 仪表盘 (`/`)
- 统计卡片展示
- 用户统计
- 系统状态
- 最近活动列表

### 用户管理 (`/users`)
- 用户列表表格
- 用户状态显示
- 用户角色标识
- 编辑/删除操作
- 模态框编辑表单

### 个人中心 (`/profile`)
- 个人信息展示
- 头像显示
- 资料编辑
- 密码修改

## 项目特点

1. **现代化设计**: 采用当前流行的 UI 设计趋势
2. **响应式布局**: 支持不同屏幕尺寸
3. **状态管理**: 使用 Pinia 进行集中状态管理
4. **路由守卫**: 保护需要认证的页面
5. **异步处理**: 前后端均使用异步编程
6. **安全性**: JWT Token + 密码加密
7. **易扩展**: 模块化设计，便于功能扩展

## 开发指南

### 添加新的 API 接口

1. 在 `backend/api/` 目录创建新的路由文件
2. 定义数据模型（schemas）
3. 实现业务逻辑
4. 在 `main.py` 中注册路由

### 添加新的前端页面

1. 在 `views/` 创建新的 Vue 组件
2. 在 `router/index.js` 添加路由配置
3. 如需状态管理，在 `stores/` 创建 store

## 注意事项

- 生产环境请修改 `SECRET_KEY` 和数据库配置
- 建议使用 PostgreSQL 或 MySQL 替代 SQLite
- 前端代理配置仅适用于开发环境
- 定期备份数据库文件

## License

MIT License
