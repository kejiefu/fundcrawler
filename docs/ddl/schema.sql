-- ==============================================
-- Stock Fund Analysis 数据库 DDL 文件
-- ==============================================
-- 创建时间: 2024年
-- 数据库类型: MySQL 8.0+
-- 字符集: utf8mb4

-- ==============================================
-- 1. 创建数据库
-- ==============================================
CREATE DATABASE IF NOT EXISTS stock_fund_analysis 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE stock_fund_analysis;

-- ==============================================
-- 2. 用户表(users)
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
    code VARCHAR(10) NOT NULL COMMENT '证券代码（纯数字格式，不带市场前缀，如600519）',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='沪深京A股基本信息表';

-- ==============================================
-- 4. 菜单表 (menus)
-- ==============================================
CREATE TABLE IF NOT EXISTS menus (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '菜单唯一标识',
    name VARCHAR(50) NOT NULL COMMENT '菜单名称',
    path VARCHAR(100) DEFAULT NULL COMMENT '路由路径',
    icon VARCHAR(50) DEFAULT NULL COMMENT '菜单图标',
    parent_id INT DEFAULT NULL COMMENT '父菜单ID',
    `order` INT DEFAULT 0 COMMENT '排序序号',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    permission VARCHAR(100) DEFAULT NULL COMMENT '权限标识',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    KEY idx_menus_id (id),
    KEY fk_menus_parent_id (parent_id),
    CONSTRAINT fk_menus_parent_id FOREIGN KEY (parent_id) REFERENCES menus (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜单表';

-- ==============================================
-- 5. A股K线数据表 (a_share_kline)
-- ==============================================
-- 存储日线、周线、月线、年线数据
CREATE TABLE IF NOT EXISTS a_share_kline (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    code VARCHAR(10) NOT NULL COMMENT '证券代码（纯数字格式，不带市场前缀，如600519）',
    trade_date VARCHAR(8) NOT NULL COMMENT '交易日期(YYYYMMDD)',
    period TINYINT NOT NULL COMMENT '周期类型(1=日线,2=周线,3=月线,4=年线)',
    open_price DECIMAL(14,4) DEFAULT NULL COMMENT '开盘价',
    close_price DECIMAL(14,4) DEFAULT NULL COMMENT '收盘价',
    high_price DECIMAL(14,4) DEFAULT NULL COMMENT '最高价',
    low_price DECIMAL(14,4) DEFAULT NULL COMMENT '最低价',
    volume DECIMAL(20,2) DEFAULT NULL COMMENT '成交量(手)',
    amount DECIMAL(22,2) DEFAULT NULL COMMENT '成交额(元)',
    prev_close DECIMAL(14,4) DEFAULT NULL COMMENT '前收盘价',
    change_pct DECIMAL(12,4) DEFAULT NULL COMMENT '涨跌幅%',
    change_amount DECIMAL(14,4) DEFAULT NULL COMMENT '涨跌额',
    amplitude DECIMAL(12,4) DEFAULT NULL COMMENT '振幅%',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_a_share_kline_code_date_period (code, trade_date, period),
    KEY idx_a_share_kline_code (code),
    KEY idx_a_share_kline_period (period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A股K线数据表';

-- ==============================================
-- 6. A股分红详情表 (a_share_dividend_detail)
-- ==============================================
-- 存储股票详细分红历史数据，用于计算股息率
-- 数据来源：交易所官方公告
CREATE TABLE IF NOT EXISTS a_share_dividend_detail (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    code VARCHAR(10) NOT NULL COMMENT '证券代码（纯数字格式，不带市场前缀，如600519）',
    name VARCHAR(64) DEFAULT NULL COMMENT '证券简称',
    announcement_date VARCHAR(8) DEFAULT NULL COMMENT '公告日期(YYYYMMDD)',
    bonus_share DECIMAL(10,4) DEFAULT NULL COMMENT '送股(每10股)',
    transfer_share INT DEFAULT NULL COMMENT '转增(每10股)',
    dividend DECIMAL(10,4) DEFAULT NULL COMMENT '派息(每10股)',
    progress VARCHAR(32) DEFAULT NULL COMMENT '进度(预案/实施等)',
    ex_dividend_date VARCHAR(8) DEFAULT NULL COMMENT '除权除息日(YYYYMMDD)',
    record_date VARCHAR(8) DEFAULT NULL COMMENT '股权登记日(YYYYMMDD)',
    bonus_share_list_date VARCHAR(8) DEFAULT NULL COMMENT '红股上市日(YYYYMMDD)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_dividend_detail_code_date (code, announcement_date, dividend),
    KEY idx_dividend_detail_code (code),
    KEY idx_dividend_detail_ex_date (ex_dividend_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A股分红详情表';

-- ==============================================
-- 7. A股技术指标表 (a_share_indicator)
-- ==============================================
-- 存储KDJ、RSI等技术指标
CREATE TABLE IF NOT EXISTS a_share_indicator (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    code VARCHAR(10) NOT NULL COMMENT '证券代码（纯数字格式，不带市场前缀，如600519）',
    trade_date VARCHAR(8) NOT NULL COMMENT '交易日期(YYYYMMDD)',
    period TINYINT NOT NULL COMMENT '周期类型(1=日线,2=周线,3=月线,4=年线)',
    k_value DECIMAL(10,4) DEFAULT NULL COMMENT 'KDJ-K值',
    d_value DECIMAL(10,4) DEFAULT NULL COMMENT 'KDJ-D值',
    j_value DECIMAL(10,4) DEFAULT NULL COMMENT 'KDJ-J值',
    rsi_6 DECIMAL(10,4) DEFAULT NULL COMMENT 'RSI-6日',
    rsi_12 DECIMAL(10,4) DEFAULT NULL COMMENT 'RSI-12日',
    rsi_24 DECIMAL(10,4) DEFAULT NULL COMMENT 'RSI-24日',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_a_share_indicator_code_date_period (code, trade_date, period),
    KEY idx_a_share_indicator_code (code),
    KEY idx_a_share_indicator_period (period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A股技术指标表';

-- ==============================================
-- 9. 财务报表表 (a_share_financial_report)
-- ==============================================
-- 存储季度财务数据
CREATE TABLE IF NOT EXISTS a_share_financial_report (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    code VARCHAR(10) NOT NULL COMMENT '证券代码（纯数字格式，不带市场前缀，如600519）',
    name VARCHAR(64) DEFAULT NULL COMMENT '证券简称',
    report_period VARCHAR(8) NOT NULL COMMENT '报告期(YYYYMMDD)',
    report_type TINYINT NOT NULL COMMENT '报告类型(1=一季度,2=半年报,3=三季度,4=年报)',
    eps DECIMAL(10,4) DEFAULT NULL COMMENT '每股收益(元)',
    eps_yoy DECIMAL(10,4) DEFAULT NULL COMMENT '每股收益同比增长率(%)',
    net_profit DECIMAL(20,4) DEFAULT NULL COMMENT '净利润(元)',
    net_profit_yoy DECIMAL(10,4) DEFAULT NULL COMMENT '净利润同比增长率(%)',
    net_profit_deducted DECIMAL(20,4) DEFAULT NULL COMMENT '扣非净利润(元)',
    net_profit_deducted_yoy DECIMAL(10,4) DEFAULT NULL COMMENT '扣非净利润同比增长率(%)',
    revenue DECIMAL(22,4) DEFAULT NULL COMMENT '营业收入(元)',
    revenue_yoy DECIMAL(10,4) DEFAULT NULL COMMENT '营业收入同比增长率(%)',
    roe DECIMAL(10,4) DEFAULT NULL COMMENT '净资产收益率(%)',
    roa DECIMAL(10,4) DEFAULT NULL COMMENT '总资产收益率(%)',
    gross_margin DECIMAL(10,4) DEFAULT NULL COMMENT '毛利率(%)',
    operating_margin DECIMAL(10,4) DEFAULT NULL COMMENT '营业利润率(%)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_a_share_financial_report_code_period (code, report_period),
    KEY idx_a_share_financial_report_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A股财务报表表';

-- ==============================================
-- 9. 同步进度表 (sync_progress)
-- ==============================================
-- 用于断点续传
CREATE TABLE IF NOT EXISTS sync_progress (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    task_name VARCHAR(64) NOT NULL COMMENT '任务名称(如:financial_report, kline, stock_basic)',
    batch_id VARCHAR(36) NOT NULL COMMENT '批次ID(UUID)',
    current_index INT NOT NULL DEFAULT 0 COMMENT '当前处理到的索引',
    total_count INT NOT NULL DEFAULT 0 COMMENT '总数量',
    status VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT '状态(running/completed/failed)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_sync_progress_task_batch (task_name, batch_id),
    KEY idx_sync_progress_task_name (task_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步进度记录表';

-- ==============================================
-- 11. 权限说明
-- ==============================================
-- 数据库用户权限建议
-- CREATE USER 'admin_app'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON stock_fund_analysis.* TO 'admin_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ==============================================
-- 12. 表结构说明
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
-- 13. 索引说明
-- ==============================================
-- uk_username: 用户名唯一索引，确保用户名不重复
-- uk_email: 邮箱唯一索引，确保邮箱不重复
-- idx_username: 用户名普通索引，加速查询
-- idx_email: 邮箱普通索引，加速查询
-- idx_is_active: 状态索引，加速按状态筛选