# Deploy toàn bộ thay đổi lên VPS (thay thế bản đang chạy)

Hướng dẫn đưa **toàn bộ code + config + data (users)** từ máy bạn lên VPS và thay thế bản đang chạy.

---

## Chuẩn bị trên máy bạn (Mac/Local)

### 1. Sửa cấu hình VPS (nếu cần)

Mở `deploy-to-vps.sh`, sửa các dòng đầu:

```bash
VPS_USER="${VPS_USER:-root}"           # user SSH (root hoặc user khác)
VPS_HOST="${VPS_HOST:-103.37.60.86}"  # IP hoặc hostname VPS
VPS_PATH="${VPS_PATH:-/srv/toolgetdata}"
SCP_PORT="${SCP_PORT:-22}"            # port SSH (22 hoặc 2222)
```

### 2. Build image linux/amd64 và save tar

```bash
chmod +x deploy-to-vps.sh
./deploy-to-vps.sh
```

Script sẽ:

- Build **api** và **crawler** cho **linux/amd64** (tránh lỗi exec format trên VPS x86).
- Save thành `api-image.tar` và `crawler-image.tar`.
- In ra lệnh **scp** và **ssh** để bạn chạy tiếp.

---

## Upload lên VPS

Chạy lần lượt (thay `root`, `103.37.60.86`, `22` nếu bạn đã đổi):

```bash
# 1. Upload images
scp -P 22 api-image.tar crawler-image.tar root@103.37.60.86:/srv/toolgetdata/

# 2. Upload compose + schema + seed
scp -P 22 docker-compose.vps.yml database_schema_complete.sql migrations_add_users_table.sql seed_users.sql run-crawler.sh root@103.37.60.86:/srv/toolgetdata/

# 3. Upload .env (có mật khẩu DB, cẩn thận)
scp -P 22 .env root@103.37.60.86:/srv/toolgetdata/
```

**Lưu ý:** Trên VPS cần dùng **DB trong Docker** (service `db`). Trong `.env` trên VPS phải có:

- `DB_HOST=db`
- `DB_PASSWORD=...`, `DB_USER=...`, `DB_NAME=...` (khớp với MySQL container)

Nếu bạn copy `.env` từ máy local, nhớ **sửa `DB_HOST=db`** (không dùng `localhost`).

---

## Trên VPS: dừng bản cũ, load image, chạy bản mới

SSH vào VPS:

```bash
ssh -p 22 root@103.37.60.86
cd /srv/toolgetdata
```

### 1. Load images

```bash
docker load -i api-image.tar
docker load -i crawler-image.tar
docker images | grep toolgetdata
```

### 2. Dừng bản cũ, chạy bản mới

Nếu trước đây dùng `docker-compose.yml` (có build):

```bash
docker-compose down
# Hoặc: docker compose down
```

Chạy bằng file VPS (chỉ image, không build):

```bash
docker-compose -f docker-compose.vps.yml up -d
# Hoặc: docker compose -f docker-compose.vps.yml up -d
```

Nếu VPS chỉ có `docker-compose` (có dấu gạch ngang):

```bash
docker-compose -f docker-compose.vps.yml up -d
```

### 3. Kiểm tra

```bash
docker-compose -f docker-compose.vps.yml ps
curl http://localhost:8000/health
```

Mở trình duyệt: **https://beta.gliacloud.online** (hoặc http://IP:8000 nếu chưa có domain).

### 4. Seed user (nếu DB mới hoặc chưa có user)

Chạy **1 lần** sau khi DB đã có bảng `users`:

```bash
cd /srv/toolgetdata
# Thay YOUR_DB_PASSWORD bằng mật khẩu DB trong .env
docker-compose -f docker-compose.vps.yml exec -T db mysql -u tooltinhreveneu_1 -pYOUR_DB_PASSWORD tooltinhreveneu_1 < seed_users.sql
```

Sau đó login: **admin** / **Admin@!321** hoặc **maxvaluemedia** / **Maxvalue@2026**.

### 5. Cron (cào 2 lần mỗi ngày)

```bash
crontab -e
```

Thêm dòng:

```
0 1,13 * * * cd /srv/toolgetdata && docker-compose -f docker-compose.vps.yml run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

Lưu và thoát. Cron sẽ chạy crawler full (không first-page-only) lúc 1:00 và 13:00 mỗi ngày.

---

## Nếu DB trên VPS đã có data và bạn muốn giữ

- **Không** xóa volume `db_data` khi chạy `down`.
- Chỉ cần `docker-compose -f docker-compose.vps.yml up -d` → api + crawler dùng image mới, DB giữ nguyên.
- Nếu đã có user thì **không** cần chạy lại `seed_users.sql`.

## Nếu muốn DB sạch (import lại schema)

1. Dừng và xóa volume: `docker-compose -f docker-compose.vps.yml down -v`
2. Chạy lại: `docker-compose -f docker-compose.vps.yml up -d` → MySQL sẽ chạy lại và import `database_schema_complete.sql` từ `init.sql`.
3. Nếu bảng `users` chưa có: `docker-compose -f docker-compose.vps.yml exec -T db mysql -u ... -p... DB < migrations_add_users_table.sql`
4. Seed user: `docker-compose -f docker-compose.vps.yml exec -T db mysql -u ... -p... DB < seed_users.sql`

---

## Tóm tắt file cần trên VPS

| File | Mục đích |
|------|----------|
| `docker-compose.vps.yml` | Chạy api + crawler + db (chỉ image, không build) |
| `api-image.tar`, `crawler-image.tar` | Image đã build sẵn linux/amd64 |
| `.env` | DB_HOST=db, DB_PASSWORD, SCRAPER_*, v.v. |
| `database_schema_complete.sql` | Schema DB (MySQL tự import lần đầu) |
| `migrations_add_users_table.sql` | Tạo bảng users (nếu DB cũ chưa có) |
| `seed_users.sql` | Tạo sẵn admin + maxvaluemedia |
| `run-crawler.sh` | (Tuỳ chọn) Wrapper cho cron |

Sau khi deploy xong, phiên bản đang chạy trên VPS sẽ là bản mới (tất cả thay đổi code + config + user seed bạn đã dùng ở local).
