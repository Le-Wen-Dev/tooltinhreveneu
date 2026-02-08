# Giải Thích Các Công Thức (Formulas)

## 🎯 Nguyên Tắc: Focus vào Net Revenue

Hệ thống **chỉ tập trung vào Net Revenue**, không quan tâm Gross Revenue.

## 📊 Các Công Thức

### 1. RPM = Tổng Net Revenue (Mobile + Desktop)

**Tên formula**: `rpm_total_net_revenue`

**Công thức**: 
```
RPM = Tổng Net Revenue (cộng cả mobile và desktop)
```

**Giải thích**:
- Đây là **tổng net revenue** của tất cả slots (mobile + desktop)
- **KHÔNG chia cho impressions**
- Chỉ đơn giản là tổng của tất cả net revenue

**Ví dụ**:
- Desktop: Net Revenue = $28.58
- Mobile: Net Revenue = $87.88
- **RPM = $28.58 + $87.88 = $116.46**

---

### 2. RPM per 1000 Players

**Tên formula**: `rpm_per_1000_players`

**Công thức**:
```
RPM = (Net Revenue / Total Player Impressions) * 1000
```

**Giải thích**:
- Tính cho **từng row** (từng slot)
- Net Revenue chia cho Total Player Impressions, nhân 1000
- Đây là RPM chuẩn (Revenue Per Mille)

**Ví dụ**:
- Net Revenue = $28.58
- Total Player Impressions = 998
- **RPM = ($28.58 / 998) * 1000 = $28.64**

---

### 3. RPM Combined (Tổng hợp)

**Tên formula**: `rpm_combined`

**Công thức**:
```
RPM Combined = (Tổng Net Revenue / Tổng Player Impressions) * 1000
```

**Giải thích**:
- Tính **tổng hợp** cho tất cả rows (mobile + desktop)
- Tổng Net Revenue chia cho Tổng Player Impressions, nhân 1000
- Đây là RPM trung bình cho tất cả slots

**Ví dụ**:
- Tổng Net Revenue = $116.46 (Desktop $28.58 + Mobile $87.88)
- Tổng Player Impressions = 11,212 (998 + 10,214)
- **RPM Combined = ($116.46 / 11,212) * 1000 = $10.38**

---

### 4. Total Net Revenue

**Tên formula**: `total_net_revenue`

**Công thức**:
```
Total Net Revenue = Sum(net_revenue_usd)
```

**Giải thích**:
- Tổng tất cả net revenue
- Tương tự như `rpm_total_net_revenue` nhưng có thể filter theo điều kiện

---

## 📝 Lưu Ý Quan Trọng

### ⚠️ Không Sử Dụng Gross Revenue

- Hệ thống **KHÔNG tính toán** Gross Revenue
- Tất cả formulas đều dựa trên **Net Revenue**
- Công thức: `Tổng IRPM / 1000 * RPM = Tổng Gross Revenue` **KHÔNG được sử dụng**

### 🔄 Cập Nhật Dữ Liệu

Khi fetch data mới:
- Dữ liệu cũ sẽ được **ghi đè** (update)
- Formulas sẽ được **tự động tính lại** sau mỗi lần fetch

### 📈 Sử Dụng Trong API

Các metrics có thể truy cập qua API:
```bash
# Lấy RPM Total Net Revenue
GET /api/aggregated-metrics?metric_name=rpm_total_net_revenue

# Lấy RPM per 1000 Players (row-level)
GET /api/computed-metrics?metric_name=rpm_per_1000_players

# Lấy RPM Combined
GET /api/aggregated-metrics?metric_name=rpm_combined
```

## 🎯 Tóm Tắt

| Formula | Mô Tả | Loại |
|---------|-------|------|
| `rpm_total_net_revenue` | Tổng Net Revenue (Mobile + Desktop) | Aggregated |
| `rpm_per_1000_players` | Net Revenue / Player Impressions * 1000 | Row-level |
| `rpm_combined` | (Tổng Net Revenue / Tổng Player Impressions) * 1000 | Aggregated |
| `total_net_revenue` | Tổng Net Revenue | Aggregated |

**Tất cả đều dựa trên Net Revenue, không sử dụng Gross Revenue.**
