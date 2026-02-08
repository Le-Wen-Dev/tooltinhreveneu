-- Tạo sẵn 2 user: admin (Admin) và maxvaluemedia (Khách). Chạy 1 lần sau khi đã có bảng users.
-- Dash Admin: admin / Admin@!321
-- Dash Khách: maxvaluemedia / Maxvalue@2026

INSERT INTO users (username, email, password_hash, role, can_view_data, api_key, is_active)
VALUES
  ('admin', 'admin@local', '$2b$12$pg/VEi3v2QLzch6PHhv8HeuYrl.Or1J9vs0N0lpxqKYxxCsFYXCGO', 'admin', 1, 'Q3tXb3Xt3lqs_pd1c5exIGhOiyIgnar5cBLzBjMg2RM', 1),
  ('maxvaluemedia', 'maxvaluemedia@local', '$2b$12$uQISfO3tcMNY.iuzeRHnuuuPhusL6hk0hXBjNU93uAGjY0PtNi9XC', 'user', 1, 'AGlX8MD4IcEzPGSnY3wmduxfrTyiDdiS7aPaWXCoyzc', 1)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  api_key = VALUES(api_key),
  role = VALUES(role),
  can_view_data = VALUES(can_view_data),
  is_active = VALUES(is_active);
