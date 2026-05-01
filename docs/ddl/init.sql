-- ==============================================
-- 数据库初始化脚本
-- ==============================================
-- 此脚本用于初始化数据库和创建必要的表结构

-- 1. 创建数据库用户（可选）
-- CREATE USER 'admin_app'@'localhost' IDENTIFIED BY 'secure_password_here';

-- 2. 创建数据库
DROP DATABASE IF EXISTS stock_fund_analysis;
CREATE DATABASE stock_fund_analysis 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 3. 授予权限（可选）
-- GRANT ALL PRIVILEGES ON stock_fund_analysis.* TO 'admin_app'@'localhost';
-- FLUSH PRIVILEGES;

-- 4. 使用数据库
USE stock_fund_analysis;

-- 5. 创建表结构
SOURCE schema.sql;

-- 6. 插入初始数据
SOURCE data.sql;

-- ==============================================
-- 执行说明
-- ==============================================
-- 在 MySQL 命令行中执行:
-- mysql -u root -p < init.sql
-- 或
-- mysql> SOURCE /path/to/init.sql;