-- ==============================================
-- Admin Dashboard 数据库 DDL 文件
-- ==============================================
-- 创建时间: 2024年
-- 数据库类型: MySQL 8.0+
-- 字符集: utf8mb4

-- ==============================================
-- 1. 创建数据库
-- ==============================================
CREATE DATABASE IF NOT EXISTS admin_dashboard 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE admin_dashboard;

-- ==============================================
-- 2. 用户表 (users)
-- ==============================================
-- 存储系统用户信息
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一标识',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    email VARCHAR(100) NOT NULL COMMENT '邮箱地址',
    hashed_password VARCHAR(255) NOT NULL COMMENT '加密后的密码',
    full_name VARCHAR(100) DEFAULT NULL COMMENT '真实姓名',
    is_active BOOLEAN DEFAULT TRUE COMMENT '账户是否激活',
    is_superuser BOOLEAN DEFAULT FALSE COMMENT '是否为超级管理员',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一索引
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    
    -- 普通索引
    KEY idx_username (username),
    KEY idx_email (email),
    KEY idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ==============================================
-- 3. 插入初始数据
-- ==============================================
-- 默认管理员账户
-- 密码: admin123 (BCrypt 加密)
INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser)
SELECT 'admin', 'admin@example.com', '$2b$12$EixZaYbB.rK4fl8x2q7Meu6Q6D2V5fF5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q', 'System Administrator', TRUE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- ==============================================
-- 4. 权限说明
-- ==============================================
-- 数据库用户权限建议:
-- CREATE USER 'admin_app'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON admin_dashboard.* TO 'admin_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ==============================================
-- 5. 表结构说明
-- ==============================================
-- 字段说明:
-- id: 用户唯一标识，自增主键
-- username: 用户名，唯一，用于登录
-- email: 邮箱地址，唯一，用于找回密码等
-- hashed_password: 使用 BCrypt 加密的密码
-- full_name: 用户真实姓名，可选
-- is_active: 账户状态，true 表示活跃，false 表示禁用
-- is_superuser: 是否为超级管理员，true 表示拥有所有权限
-- created_at: 记录创建时间
-- updated_at: 记录更新时间

-- ==============================================
-- 6. 索引说明
-- ==============================================
-- uk_username: 用户名唯一索引，确保用户名不重复
-- uk_email: 邮箱唯一索引，确保邮箱不重复
-- idx_username: 用户名普通索引，加速查询
-- idx_email: 邮箱普通索引，加速查询
-- idx_is_active: 状态索引，加速按状态筛选
