#!/bin/bash
# Wrapper script để chạy crawler qua Docker
# Sử dụng trong cron job

cd "$(dirname "$0")"

# Log file
LOG_FILE="/var/log/revenue-crawler.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting crawler..." >> "$LOG_FILE"

# Chạy crawler
docker compose run --rm crawler >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Crawler completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] Crawler failed with exit code: $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
