# 数据库设计文档

## 概述

本系统使用 MySQL 作为数据库，通过 SQLAlchemy ORM 进行数据库操作，支持异步操作。

## 数据库配置

### 连接字符串格式

```
mysql+aiomysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4
```

### 默认配置

- **主机**: localhost
- **端口**: 3306
- **数据库名**: admin_dashboard
- **用户名**: root
- **密码**: 999888777
- **字符集**: utf8mb4

### 环境变量配置

可以通过设置 `DATABASE_URL` 环境变量来覆盖默认配置：

```bash
export DATABASE_URL="mysql+aiomysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4"
```

### 创建数据库

在连接 MySQL 后，需要先创建数据库：

```sql
CREATE DATABASE admin_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 用户表 (users)

### 表结构

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 用户唯一标识 |
| username | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | 邮箱 |
| hashed_password | VARCHAR(255) | NOT NULL | 加密后的密码 |
| full_name | VARCHAR(100) | NULL | 真实姓名 |
| is_active | BOOLEAN | DEFAULT TRUE | 账户是否激活 |
| is_superuser | BOOLEAN | DEFAULT FALSE | 是否为超级管理员 |
| created_at | DATETIME | SERVER DEFAULT | 创建时间 |
| updated_at | DATETIME | ON UPDATE | 更新时间 |

### 索引

- `idx_username`: username 字段索引
- `idx_email`: email 字段索引

### 初始数据

系统初始化时自动创建默认管理员账户：

- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@example.com
- **角色**: 超级管理员

## 安全说明

1. **密码存储**: 使用 BCrypt 算法加密，不可逆
2. **JWT Token**: HS256 算法签名，有效期 60 分钟
3. **敏感操作**: 删除用户、修改超级用户状态需要管理员权限
4. **连接池**: 配置了连接池（pool_size=10）和连接检测（pool_pre_ping=True）

## ER 图

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ email           │
│ hashed_password │
│ full_name       │
│ is_active       │
│ is_superuser    │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

## 数据类型映射

| Python 类型 | MySQL 类型 |
|------------|-------------|
| Integer | INT |
| String | VARCHAR |
| Boolean | BOOLEAN/TINYINT |
| DateTime | DATETIME |

## MySQL 特性

### utf8mb4 字符集

使用 `utf8mb4` 字符集支持完整的 Unicode 字符，包括 emoji 表情符号。

### 连接池配置

```python
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # 连接前检测
    pool_size=10         # 连接池大小
)
```

### 异步驱动

使用 `aiomysql` 作为异步 MySQL 驱动，配合 SQLAlchemy 的异步功能使用。

## 迁移说明

使用 Alembic 工具进行数据库版本管理。

### 安装 Alembic

```bash
pip install alembic
```

### 初始化

```bash
cd backend
alembic init alembic
```

### 创建迁移

```bash
alembic revision --autogenerate -m "Initial migration"
```

### 执行迁移

```bash
alembic upgrade head
```

### 回滚

```bash
alembic downgrade -1
```

## 备份和恢复

### 备份

```bash
mysqldump -u root -p admin_dashboard > backup.sql
```

### 恢复

```bash
mysql -u root -p admin_dashboard < backup.sql
```
