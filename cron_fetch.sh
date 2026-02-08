#!/bin/bash
# Cron script để fetch data 2 lần mỗi ngày
# Script này sẽ được gọi bởi cron job

# Đường dẫn đến project
PROJECT_DIR="/Users/lequel/Downloads/toolgetdata"
# Hoặc thay đổi thành đường dẫn tuyệt đối của bạn:
# PROJECT_DIR="/path/to/toolgetdata"

# Đường dẫn đến Python virtual environment
# Nếu không dùng venv, để trống hoặc comment dòng này
VENV_PATH="${PROJECT_DIR}/venv/bin/python3"

# Nếu không dùng venv, sử dụng python3 system
if [ ! -f "$VENV_PATH" ]; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="$VENV_PATH"
fi

# Chuyển đến thư mục project
cd "$PROJECT_DIR" || exit 1

# Load environment variables nếu có file .env
if [ -f "${PROJECT_DIR}/backend/.env" ]; then
    export $(cat "${PROJECT_DIR}/backend/.env" | grep -v '^#' | xargs)
fi

# Log file
LOG_FILE="${PROJECT_DIR}/logs/cron_fetch.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Chạy fetch (lấy dữ liệu hôm nay)
echo "[$TIMESTAMP] Starting data fetch..." >> "$LOG_FILE"
$PYTHON_CMD backend/data_fetcher.py --date $(date +%Y-%m-%d) >> "$LOG_FILE" 2>&1

# Kiểm tra kết quả
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Fetch completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] Fetch failed with exit code: $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
