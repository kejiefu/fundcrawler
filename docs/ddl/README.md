# DDL 文件说明

## 概述

本目录包含数据库的 DDL (Data Definition Language) 文件，用于创建和管理数据库表结构。

## 文件结构

```
ddl/
├── init.sql       # 数据库初始化脚本
├── schema.sql     # 表结构定义
├── data.sql       # 初始数据
└── README.md      # 说明文档
```

## 文件说明

### 1. init.sql

数据库初始化脚本，用于：
- 创建数据库
- 设置字符集
- 执行表结构创建
- 插入初始数据

### 2. schema.sql

表结构定义文件，包含：
- 用户表 (users) 结构定义
- A 股基本信息表 (a_share_stock_basic)，含股息率字段
- 索引定义
- 表注释

### 3. data.sql

初始数据脚本，包含：
- 默认管理员账户
- 测试用户数据（可选）

## 使用方法

### 方法一：使用 init.sql 初始化

```bash
# 使用 root 用户执行
mysql -u root -p < init.sql

# 或指定数据库
mysql -u root -p stock_fund_analysis < schema.sql
mysql -u root -p stock_fund_analysis < data.sql
```

### 方法二：在 MySQL 命令行中执行

```sql
-- 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE stock_fund_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE stock_fund_analysis;

-- 导入表结构
SOURCE /path/to/schema.sql;

-- 导入初始数据
SOURCE /path/to/data.sql;
```

## 默认账户

| 用户名 | 密码 | 邮箱 | 角色 |
|--------|------|------|------|
| admin | admin123 | admin@example.com | 超级管理员 |

## 表结构

### users 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 用户唯一标识 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱 |
| hashed_password | VARCHAR(255) | NOT NULL | 加密密码 |
| full_name | VARCHAR(100) | NULL | 真实姓名 |
| is_active | BOOLEAN | DEFAULT TRUE | 账户状态 |
| is_superuser | BOOLEAN | DEFAULT FALSE | 超级管理员 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

## 索引

| 索引名 | 类型 | 字段 |
|--------|------|------|
| PRIMARY | 主键 | id |
| uk_username | 唯一 | username |
| uk_email | 唯一 | email |
| idx_username | 普通 | username |
| idx_email | 普通 | email |
| idx_is_active | 普通 | is_active |

## 注意事项

1. 确保 MySQL 版本 >= 8.0
2. 使用 utf8mb4 字符集支持完整 Unicode
3. 生产环境请修改默认密码
4. 定期备份数据库

## 数据库连接信息

- **数据库名**: stock_fund_analysis
- **主机**: localhost
- **端口**: 3306
- **字符集**: utf8mb4
