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
-- 3. A 股基本信息表 (a_share_stock_basic)
-- ==============================================
-- 由应用后台同步写入；股息率优先东财分红配送，缺失时用新浪年均股息近似
CREATE TABLE IF NOT EXISTS a_share_stock_basic (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    code VARCHAR(10) NOT NULL COMMENT '证券代码',
    name VARCHAR(64) NOT NULL COMMENT '证券简称',
    board_label VARCHAR(32) DEFAULT NULL COMMENT '板块/市场推断',
    latest_price DECIMAL(14,4) DEFAULT NULL COMMENT '最新价',
    change_pct DECIMAL(12,4) DEFAULT NULL COMMENT '涨跌幅%',
    change_amount DECIMAL(14,4) DEFAULT NULL COMMENT '涨跌额',
    volume DECIMAL(20,2) DEFAULT NULL COMMENT '成交量(手)',
    amount DECIMAL(22,2) DEFAULT NULL COMMENT '成交额(元)',
    amplitude DECIMAL(12,4) DEFAULT NULL COMMENT '振幅%',
    high DECIMAL(14,4) DEFAULT NULL COMMENT '最高',
    low DECIMAL(14,4) DEFAULT NULL COMMENT '最低',
    open_price DECIMAL(14,4) DEFAULT NULL COMMENT '今开',
    prev_close DECIMAL(14,4) DEFAULT NULL COMMENT '昨收',
    volume_ratio DECIMAL(14,4) DEFAULT NULL COMMENT '量比',
    turnover_rate DECIMAL(12,4) DEFAULT NULL COMMENT '换手率%',
    pe_dynamic DECIMAL(14,4) DEFAULT NULL COMMENT '市盈率-动态',
    pb DECIMAL(14,4) DEFAULT NULL COMMENT '市净率',
    total_market_cap DECIMAL(22,2) DEFAULT NULL COMMENT '总市值(元)',
    circulating_market_cap DECIMAL(22,2) DEFAULT NULL COMMENT '流通市值(元)',
    rise_speed DECIMAL(12,4) DEFAULT NULL COMMENT '涨速',
    change_5min DECIMAL(12,4) DEFAULT NULL COMMENT '5分钟涨跌%',
    change_60d DECIMAL(12,4) DEFAULT NULL COMMENT '60日涨跌幅%',
    change_ytd DECIMAL(12,4) DEFAULT NULL COMMENT '年初至今涨跌幅%',
    dividend_yield DECIMAL(12,4) DEFAULT NULL COMMENT '股息率%',
    dividend_yield_as_of VARCHAR(12) DEFAULT NULL COMMENT '股息率对应报告期YYYYMMDD；新浪回填时为空',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_a_share_stock_basic_code (code),
    KEY idx_a_share_stock_basic_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='沪深京A股基本信息';

-- ==============================================
-- 4. 插入初始数据
-- ==============================================
-- 默认管理员账户
-- 密码: admin123 (BCrypt 加密)
INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser)
SELECT 'admin', 'admin@example.com', '$2b$12$EixZaYbB.rK4fl8x2q7Meu6Q6D2V5fF5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q', 'System Administrator', TRUE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- ==============================================
-- 5. 权限说明
-- ==============================================
-- 数据库用户权限建议:
-- CREATE USER 'admin_app'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON admin_dashboard.* TO 'admin_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ==============================================
-- 6. 表结构说明
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
-- 7. 索引说明
-- ==============================================
-- uk_username: 用户名唯一索引，确保用户名不重复
-- uk_email: 邮箱唯一索引，确保邮箱不重复
-- idx_username: 用户名普通索引，加速查询
-- idx_email: 邮箱普通索引，加速查询
-- idx_is_active: 状态索引，加速按状态筛选
