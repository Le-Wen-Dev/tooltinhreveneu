-- ============================================
-- Migration: Add slot_share_config and user_slots tables
-- Run this on existing DB to add Feature 1 (% share) and Feature 2 (slot assignment)
-- ============================================

-- ============================================
-- 1. SLOT SHARE CONFIG TABLE
-- Config % share per processed slot with effective date
-- Admin set share BEFORE crawler runs (~7h sáng)
-- Value carries forward until changed
-- ============================================
CREATE TABLE IF NOT EXISTS slot_share_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slot VARCHAR(255) NOT NULL,
    share_percent DECIMAL(5, 2) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    UNIQUE KEY uq_slot_effective_date (slot, effective_date),
    INDEX idx_slot (slot),
    INDEX idx_effective_date (effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. USER SLOTS TABLE
-- Assign processed slots to users
-- 1 slot = 1 user only (UNIQUE on slot)
-- Admin always sees all, no need to assign
-- User with no slots sees nothing
-- ============================================
CREATE TABLE IF NOT EXISTS user_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    slot VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

