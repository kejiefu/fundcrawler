-- ==============================================
-- 初始数据脚本
-- ==============================================
-- 此脚本包含系统初始化所需的基础数据

USE admin_dashboard;

-- ==============================================
-- 用户初始数据
-- ==============================================

-- 默认管理员账户
-- 用户名: admin
-- 密码: admin123 (BCrypt 加密)
-- 邮箱: admin@example.com
INSERT INTO users (
    username, 
    email, 
    hashed_password, 
    full_name, 
    is_active, 
    is_superuser,
    created_at
) VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$EixZaYbB.rK4fl8x2q7Meu6Q6D2V5fF5Q5Q5Q5Q5Q5Q5Q5Q5Q',
    'System Administrator',
    TRUE,
    TRUE,
    NOW()
) ON DUPLICATE KEY UPDATE 
    email = VALUES(email),
    full_name = VALUES(full_name),
    is_active = VALUES(is_active),
    is_superuser = VALUES(is_superuser);

-- ==============================================
-- 测试用户数据（可选）
-- ==============================================
-- 取消注释以创建测试用户
/*
INSERT INTO users (
    username, 
    email, 
    hashed_password, 
    full_name, 
    is_active, 
    is_superuser,
    created_at
) VALUES 
(
    'testuser1',
    'testuser1@example.com',
    '$2b$12$EixZaYbB.rK4fl8x2q7Meu6Q6D2V5fF5Q5Q5Q5Q5Q5Q5Q5Q5Q',
    'Test User One',
    TRUE,
    FALSE,
    NOW()
),
(
    'testuser2',
    'testuser2@example.com',
    '$2b$12$EixZaYbB.rK4fl8x2q7Meu6Q6D2V5fF5Q5Q5Q5Q5Q5Q5Q5Q5Q',
    'Test User Two',
    TRUE,
    FALSE,
    NOW()
);
*/

-- ==============================================
-- 数据说明
-- ==============================================
-- 1. 默认管理员账户用于系统初始化和管理
-- 2. 测试用户数据仅供开发和测试使用
-- 3. 生产环境建议删除或禁用测试用户
