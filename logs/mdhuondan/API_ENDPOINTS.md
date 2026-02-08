# API Endpoints - Trả Về Computed Metrics

## 📊 Endpoints Chính

### 1. Lấy Computed Metrics (Kết quả tính toán)

**GET** `/api/computed-metrics`

**Query Parameters**:
- `raw_data_id` (optional): Filter theo raw data ID
- `formula_id` (optional): Filter theo formula ID
- `metric_name` (optional): Filter theo tên metric
- `limit` (optional, default: 100): Số lượng records

**Ví dụ**:
```bash
# Lấy tất cả computed metrics
GET /api/computed-metrics

# Lấy RPM per 1000 players
GET /api/computed-metrics?metric_name=rpm_per_1000_players

# Lấy metrics của một raw data cụ thể
GET /api/computed-metrics?raw_data_id=123
```

**Response**:
```json
[
  {
    "id": 1,
    "raw_data_id": 123,
    "formula_id": 2,
    "metric_name": "rpm_per_1000_players",
    "metric_value": 28.64,
    "computed_at": "2026-01-28T10:30:00"
  }
]
```

---

### 2. Lấy Aggregated Metrics (Tổng hợp)

**GET** `/api/aggregated-metrics`

**Query Parameters**:
- `channel` (optional): Filter theo channel
- `time_unit` (optional): Filter theo time unit
- `fetch_date` (optional): Filter theo ngày fetch (YYYY-MM-DD)
- `metric_name` (optional): Filter theo tên metric

**Ví dụ**:
```bash
# Lấy RPM Total Net Revenue
GET /api/aggregated-metrics?metric_name=rpm_total_net_revenue

# Lấy metrics theo channel và ngày
GET /api/aggregated-metrics?channel=maxvaluemedia_spotpariz&fetch_date=2026-01-26

# Lấy RPM Combined
GET /api/aggregated-metrics?metric_name=rpm_combined
```

**Response**:
```json
[
  {
    "id": 1,
    "channel": "maxvaluemedia_spotpariz",
    "time_unit": "2026/01",
    "fetch_date": "2026-01-26",
    "metric_name": "rpm_total_net_revenue",
    "metric_value": 116.46,
    "formula_id": 1,
    "computed_at": "2026-01-28T10:30:00"
  }
]
```

---

### 3. Lấy Raw Data (Dữ liệu gốc)

**GET** `/api/raw-data`

**Query Parameters**:
- `fetch_date` (optional): Filter theo ngày fetch
- `channel` (optional): Filter theo channel
- `limit` (optional, default: 100)
- `offset` (optional, default: 0)

**Ví dụ**:
```bash
# Lấy data hôm nay
GET /api/raw-data?fetch_date=2026-01-26

# Lấy data theo channel
GET /api/raw-data?channel=maxvaluemedia_spotpariz
```

---

### 4. Lấy Fetch History (Lịch sử fetch)

**GET** `/api/fetch-logs`

**Query Parameters**:
- `fetch_date` (optional): Filter theo ngày
- `status` (optional): Filter theo status (success, failed, partial)
- `limit` (optional, default: 100)

**Ví dụ**:
```bash
# Lấy lịch sử fetch
GET /api/fetch-logs

# Lấy lịch sử theo ngày
GET /api/fetch-logs?fetch_date=2026-01-26

# Lấy các lần fetch thành công
GET /api/fetch-logs?status=success
```

**Response**:
```json
[
  {
    "id": 1,
    "fetch_date": "2026-01-26",
    "status": "success",
    "records_fetched": 6,
    "pages_fetched": 1,
    "started_at": "2026-01-26T08:00:00",
    "completed_at": "2026-01-26T08:05:00",
    "duration_seconds": 300
  }
]
```

---

### 5. Trigger Computation (Tính lại formulas)

**POST** `/api/compute/{formula_id}`

**Ví dụ**:
```bash
# Tính lại formula ID 1
POST /api/compute/1
```

**Response**:
```json
{
  "message": "Computation triggered",
  "results": {
    "formula_id": 1,
    "formula_name": "rpm_total_net_revenue",
    "computed_metrics": 0,
    "aggregated_metrics": 1
  }
}
```

---

## 🔄 Workflow Sử Dụng

### 1. Lấy Metrics Mới Nhất

```bash
# Lấy RPM Total Net Revenue mới nhất
GET /api/aggregated-metrics?metric_name=rpm_total_net_revenue&fetch_date=2026-01-26

# Lấy RPM per 1000 Players cho tất cả slots
GET /api/computed-metrics?metric_name=rpm_per_1000_players
```

### 2. Lấy Lịch Sử Theo Ngày

```bash
# Xem lịch sử fetch
GET /api/fetch-logs?fetch_date=2026-01-26

# Xem raw data của ngày đó
GET /api/raw-data?fetch_date=2026-01-26

# Xem computed metrics của ngày đó
GET /api/aggregated-metrics?fetch_date=2026-01-26
```

### 3. So Sánh Giữa Các Ngày

```bash
# Lấy metrics của nhiều ngày
GET /api/aggregated-metrics?metric_name=rpm_total_net_revenue
# Response sẽ có fetch_date để filter client-side
```

---

## 📝 Lưu Ý

1. **Tự động tính toán**: Sau mỗi lần fetch, formulas sẽ tự động được tính
2. **Lịch sử**: Mỗi lần fetch được lưu vào `fetch_logs` với `fetch_date`
3. **Real-time**: API trả về data real-time từ database
4. **Filter**: Có thể filter theo `fetch_date` để xem data của ngày cụ thể

---

## 🧪 Test API

```bash
# Health check
curl http://localhost:8000/health

# Lấy computed metrics
curl http://localhost:8000/api/computed-metrics

# Lấy aggregated metrics
curl http://localhost:8000/api/aggregated-metrics?metric_name=rpm_total_net_revenue

# Xem Swagger UI
# Mở browser: http://localhost:8000/docs
```
