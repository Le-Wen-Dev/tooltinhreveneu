-- ============================================
-- Database Schema Complete - MySQL
-- Import file này 1 lần để tạo toàn bộ database
-- Database: tooltinhreveneu_1
-- ============================================

-- ============================================
-- 1. RAW DATA TABLE
-- Lưu dữ liệu scrape với fetch_date để track lịch sử mỗi ngày
-- ============================================
CREATE TABLE IF NOT EXISTS raw_revenue_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    channel VARCHAR(255) NOT NULL,
    slot VARCHAR(255) NOT NULL,
    time_unit VARCHAR(50) NOT NULL,
    total_player_impr VARCHAR(50),  -- Stored as string to handle commas
    total_ad_impr VARCHAR(50),      -- Stored as string to handle commas and "-"
    rpm VARCHAR(50),
    gross_revenue_usd VARCHAR(50),
    net_revenue_usd VARCHAR(50),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fetch_date DATE NOT NULL,  -- Date when data was fetched (lịch sử mỗi ngày)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_record (channel, slot, time_unit, fetch_date),
    INDEX idx_fetch_date (fetch_date),
    INDEX idx_channel (channel),
    INDEX idx_time_unit (time_unit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. FORMULA DEFINITIONS TABLE
-- Định nghĩa các công thức tính toán
-- ============================================
CREATE TABLE IF NOT EXISTS formulas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    formula_expression TEXT NOT NULL,  -- Python expression or formula string
    formula_type VARCHAR(50) NOT NULL,  -- 'rpm', 'irpm', 'custom', etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    formula_metadata JSON  -- MySQL JSON type (renamed from 'metadata' - reserved word)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. COMPUTED METRICS TABLE
-- Kết quả tính toán cho từng row (row-level metrics)
-- ============================================
CREATE TABLE IF NOT EXISTS computed_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_data_id INT NOT NULL,
    formula_id INT NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(20, 6),
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_computed (raw_data_id, formula_id, metric_name),
    INDEX idx_raw_data (raw_data_id),
    INDEX idx_formula (formula_id),
    INDEX idx_metric_name (metric_name),
    FOREIGN KEY (raw_data_id) REFERENCES raw_revenue_data(id) ON DELETE CASCADE,
    FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. AGGREGATED METRICS TABLE
-- Kết quả tính toán tổng hợp (aggregated metrics)
-- ============================================
CREATE TABLE IF NOT EXISTS aggregated_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    channel VARCHAR(255),
    time_unit VARCHAR(50),
    fetch_date DATE NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(20, 6),
    formula_id INT,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_aggregated (channel, time_unit, fetch_date, metric_name, formula_id),
    INDEX idx_channel_date (channel, fetch_date),
    INDEX idx_time_unit (time_unit),
    FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. FETCH LOGS TABLE
-- Lưu lịch sử mỗi lần fetch data
-- ============================================
CREATE TABLE IF NOT EXISTS fetch_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fetch_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'success', 'failed', 'partial'
    records_fetched INT DEFAULT 0,
    records_created INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    pages_fetched INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    duration_seconds INT,
    INDEX idx_fetch_date (fetch_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. USERS TABLE (login, roles, permissions, API key)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',  -- 'admin' | 'user'
    can_view_data BOOLEAN DEFAULT FALSE,       -- admin grants this to allow data/API access
    api_key VARCHAR(64) NULL UNIQUE,            -- for API access (X-API-Key header)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_role (role),
    INDEX idx_api_key (api_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. CRAWL RUNS TABLE (Lock table)
-- Tránh chạy trùng crawler
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fetch_date DATE NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL,  -- 'running', 'completed', 'failed'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    pid INT,  -- Process ID
    INDEX idx_fetch_date (fetch_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- INITIAL DATA: Default Formulas
-- Focus: Net Revenue only (không quan tâm Gross Revenue)
-- ============================================
INSERT INTO formulas (name, description, formula_expression, formula_type) VALUES
-- RPM = Tổng Net Revenue (cộng cả mobile và desktop)
-- Đây là tổng net revenue, KHÔNG chia cho impressions
('rpm_total_net_revenue', 'RPM = Tổng Net Revenue (Mobile + Desktop)', 
 'sum(net_revenue_usd for all rows)', 
 'rpm'),

-- RPM sau = Net Revenue / Total Player * 1000
-- Tính cho từng row (per 1000 players)
('rpm_per_1000_players', 'RPM per 1000 Players = Net Revenue / Total Player * 1000', 
 '(net_revenue_usd / total_player_impr) * 1000', 
 'rpm'),

-- Tổng Net Revenue (tổng hợp)
('total_net_revenue', 'Total Net Revenue (Sum)', 
 'sum(net_revenue_usd)', 
 'revenue'),

-- RPM Combined = Tổng Net Revenue / Tổng Player Impressions * 1000
-- Tính tổng hợp cho tất cả rows (mobile + desktop)
('rpm_combined', 'RPM Combined = (Tổng Net Revenue / Tổng Player Impressions) * 1000', 
 'sum(net_revenue_usd for all rows) / sum(total_player_impr for all rows) * 1000', 
 'rpm')
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    formula_expression = VALUES(formula_expression),
    formula_type = VALUES(formula_type),
    updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- 7. PROCESSED REVENUE DATA TABLE
-- Bảng lưu dữ liệu đã xử lý (tổng hợp desktop + mobile)
-- ============================================
CREATE TABLE IF NOT EXISTS processed_revenue_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slot VARCHAR(255) NOT NULL,
    time_unit VARCHAR(50) NOT NULL,
    total_player_impr DECIMAL(20, 2),
    revenue DECIMAL(20, 2),
    rpm DECIMAL(10, 2),
    share DECIMAL(5, 2) DEFAULT 50.00,
    total_player_impr_2 DECIMAL(20, 2),
    revenue_2 DECIMAL(20, 2),
    rpm_2 DECIMAL(10, 2),
    fetch_date DATE NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_processed (slot, time_unit, fetch_date),
    INDEX idx_fetch_date (fetch_date),
    INDEX idx_slot (slot),
    INDEX idx_time_unit (time_unit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- END OF SCHEMA
-- ============================================
-- 
-- Cách import:
-- mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
-- 
-- Hoặc qua phpMyAdmin:
-- 1. Chọn database: tooltinhreveneu_1
-- 2. Import -> Chọn file database_schema_complete.sql
-- 3. Execute
--
-- ============================================
