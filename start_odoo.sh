#!/bin/bash
# Tắt mọi tiến trình đang chiếm cổng 8069
fuser -k 8069/tcp 2>/dev/null

# Vào thư mục và kích hoạt virtualenv
cd /home/luc/odoo-fitdnu
source venv/bin/activate

# Chạy Odoo, ép nâng cấp module nhan_su
python3 odoo-bin -c odoo.conf -u nhan_su --stop-after-init

echo ""
echo "=== Nâng cấp xong! Khởi động server Odoo bình thường... ==="
# Bật lại server bình thường
python3 odoo-bin -c odoo.conf
