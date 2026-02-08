#!/bin/bash
# Script tự động setup cron job

echo "=========================================="
echo "Setup Cron Job cho Data Fetching"
echo "=========================================="
echo ""

# Lấy đường dẫn hiện tại
CURRENT_DIR=$(pwd)
PROJECT_DIR="$CURRENT_DIR"

echo "Project directory: $PROJECT_DIR"
echo ""

# Tạo thư mục logs nếu chưa có
mkdir -p "$PROJECT_DIR/logs"
echo "✅ Created logs directory"

# Cập nhật đường dẫn trong cron_fetch.sh
if [ -f "$PROJECT_DIR/cron_fetch.sh" ]; then
    # macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|PROJECT_DIR=\"/Users/lequel/Downloads/toolgetdata\"|PROJECT_DIR=\"$PROJECT_DIR\"|g" "$PROJECT_DIR/cron_fetch.sh"
    else
        # Linux
        sed -i "s|PROJECT_DIR=\"/Users/lequel/Downloads/toolgetdata\"|PROJECT_DIR=\"$PROJECT_DIR\"|g" "$PROJECT_DIR/cron_fetch.sh"
    fi
    echo "✅ Updated PROJECT_DIR in cron_fetch.sh"
fi

# Chmod script
chmod +x "$PROJECT_DIR/cron_fetch.sh"
echo "✅ Made cron_fetch.sh executable"

# Kiểm tra xem cron job đã tồn tại chưa
CRON_JOB_1="0 8 * * * $PROJECT_DIR/cron_fetch.sh"
CRON_JOB_2="0 20 * * * $PROJECT_DIR/cron_fetch.sh"

if crontab -l 2>/dev/null | grep -q "cron_fetch.sh"; then
    echo ""
    echo "⚠️  Cron job đã tồn tại. Bạn có muốn thêm lại không? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "Bỏ qua việc thêm cron job."
        exit 0
    fi
fi

# Thêm cron job
(crontab -l 2>/dev/null; echo ""; echo "# Revenue Share Data Fetch - 8:00 AM"; echo "$CRON_JOB_1"; echo "# Revenue Share Data Fetch - 8:00 PM"; echo "$CRON_JOB_2") | crontab -

echo ""
echo "✅ Đã thêm cron job thành công!"
echo ""
echo "Cron jobs đã được setup:"
echo "  - 8:00 AM mỗi ngày"
echo "  - 8:00 PM mỗi ngày"
echo ""
echo "Để xem cron jobs hiện tại: crontab -l"
echo "Để xóa cron jobs: crontab -e (xóa các dòng liên quan)"
echo ""
echo "Logs sẽ được lưu tại: $PROJECT_DIR/logs/cron_fetch.log"
echo ""
