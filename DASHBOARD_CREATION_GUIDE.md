# TCP Service Monitor - Dashboard Configuration Guide

## วิธีสร้าง Dashboard ใหม่แบบ User-Friendly

เนื่องจาก dashboard JSON ขนาดใหญ่และซับซ้อน แนะนำให้**สร้างใหม่ใน Grafana UI** โดยใช้คู่มือนี้

---

## ขั้นตอนการสร้าง

### 1. สร้าง Dashboard ใหม่
1. เข้า Grafana: http://10.1.55.29.nip.io:3000
2. คลิก **+ → New Dashboard**
3. ตั้งชื่อ: "TCP Service Monitor"

### 2. เพิ่ม Row #1: Overview (แถวบนสุด)

#### Panel 1.1: Service Manager (iframe)
- **Type**: Text panel (mode: HTML)
- **Size**: 10 units wide × 8 units tall
- **Content**:
```html
<iframe 
    src="http://10.1.55.29:5000" 
    width="100%" 
    height="100%" 
    frameborder="0" 
    style="border: none;">
</iframe>
```

#### Panel 1.2: Total Services
- **Type**: Stat
- **Query**: `count(max by (service) (probe_success))`
- **Options**: 
  - Color mode: Value
  - Graph mode: Area
  - Text size: Auto

#### Panel 1.3: Services UP
- **Type**: Stat  
- **Query**: `count((max by (service) (probe_success)) == 1)`
- **Thresholds**:
  - Base: Green
- **Color mode**: Background

#### Panel 1.4: Services DOWN
- **Type**: Stat
- **Query**: `count((max by (service) (probe_success)) == 0) or vector(0)`
- **Thresholds**:
  - 0: Green
  - 1: Red
- **Color mode**: Background

---

### 3. เพิ่ม Row #2: Quick Status View

#### Panel 2.1: Service Status Grid
- **Type**: Status History
- **Query**: `probe_success`
- **Legend**: `{{service}}`
- **Options**:
  - Show values: Never
  - Colors: Green (1), Red (0)
  - Row height: 0.8

#### Panel 2.2: Up vs Down Gauge
- **Type**: Gauge
- **Query A**: `count((max by (service) (probe_success)) == 1)` (Legend: UP)
- **Query B**: `count((max by (service) (probe_success)) == 0) or vector(0)` (Legend: DOWN)
- **Options**:
  - Min: 0
  - Max: 10
  - Thresholds: 
    - UP (Query A): Green
    - DOWN (Query B): Red

---

### 4. เพิ่ม Row #3: Availability & Performance

#### Panel 3.1: Service Availability Table
- **Type**: Table
- **Query**: 
```promql
avg_over_time(probe_success[5m]) * 100
```
- **Transformations**:
  1. **Organize fields**: Rename "Value" → "Availability %"
  2. **Group by**: service
- **Overrides**:
  - Availability %:
    - Unit: percent
    - Decimals: 2
    - Cell type: Color background
    - Thresholds: 0 (Red), 90 (Yellow), 99 (Green)

#### Panel 3.2: Response Time by Service
- **Type**: Bar gauge (Horizontal)
- **Query**: 
```promql
avg by (service) (rate(probe_duration_seconds[5m]))
```
- **Legend**: `{{service}}`
- **Options**:
  - Orientation: Horizontal
  - Display mode: Gradient
  - Unit: seconds (s)
  - Decimals: 3

---

### 5. เพิ่ม Row #4: Time Series Analysis

#### Panel 4.1: TCP Connection Success Rate
- **Type**: Time series
- **Query**: 
```promql
avg(probe_success) * 100
```
- **Legend**: Connection Success %
- **Options**:
  - Unit: percent
  - Min: 0
  - Max: 100
  - Fill opacity: 20
  - Line width: 2
  - Thresholds:
    - 0: Red
    - 90: Yellow
    - 99: Green

#### Panel 4.2: Connection Success by Service
- **Type**: Time series
- **Query**: 
```promql
probe_success
```
- **Legend**: `{{service}}`
- **Options**:
  - Line width: 1
  - Fill opacity: 5
  - Stacking: Normal

---

### 6. เพิ่ม Row #5: Detailed Metrics

#### Panel 5.1: DNS Lookup Time
- **Type**: Time series
- **Query**: 
```promql
avg by (service) (probe_dns_lookup_time_seconds)
```
- **Legend**: `{{service}}`
- **Options**:
  - Unit: seconds (s)
  - Decimals: 3

#### Panel 5.2: Connection Duration Heatmap
- **Type**: Heatmap
- **Query**: 
```promql
probe_duration_seconds
```
- **Options**:
  - Data format: Time series buckets
  - Y-axis: Service
  - Cell gap: 2
  - Color scheme: Spectral

---

## Tips สำหรับ UI ที่สวยงาม

### Colors & Themes
```
✅ Good:
- ใช้ Dark theme
- สี: Green=#73BF69, Red=#F2495C, Yellow=#FF9830
- ใช้ gradient และ opacity

❌ Avoid:
- สีจ้าเกินไป
- ใช้มากกว่า 3-4 สีหลัก
- Background ขาวจ้า
```

### Panel Organization
```
✅ Good:
- จัดกลุ่มตรรกะชัดเจน (Overview → Detail)
- ใช้ Row แบ่งหมวดหมู่
- Panel สำคัญอยู่ข้างบน
- ขนาด Panel สมดุล

❌ Avoid:
- วาง Panel สุ่มสี่สุ่มห้า
- ขนาดไม่สมดุล
- ข้อมูลเยอะเกินไปใน 1 Panel
```

### Visualization Types
```
สถานะ → Stat, Gauge, Status History
แนวโน้ม → Time Series, Line Chart
เปรียบเทียบ → Bar Gauge, Table
รูปแบบ → Heatmap, Status Map
```

---

## Dashboard Settings

### General
- **Name**: TCP Service Monitor
- **Tags**: monitoring, tcp, blackbox
- **Timezone**: Browser time
- **Auto-refresh**: 5s, 10s, 30s, 1m

### Variables (Optional - สำหรับ Filter)

#### service
- **Type**: Query
- **Query**: `label_values(probe_success, service)`
- **Multi-value**: Yes
- **Include All**: Yes

จากนั้นเพิ่ม `{service=~"$service"}` ใน query ที่ต้องการ filter

---

## Quick Copy-Paste Queries

```promql
# Total services
count(max by (service) (probe_success))

# Services UP
count((max by (service) (probe_success)) == 1)

# Services DOWN  
count((max by (service) (probe_success)) == 0) or vector(0)

# Overall success rate
avg(probe_success) * 100

# Availability by service (5 min avg)
avg_over_time(probe_success[5m]) * 100

# Response time by service
avg by (service) (rate(probe_duration_seconds[5m]))

# DNS lookup time
avg by (service) (probe_dns_lookup_time_seconds)

# Connection success over time
probe_success

# Duration heatmap
probe_duration_seconds
```

---

## หลังจากสร้างเสร็จ

1. **Save dashboard**
2. **Star** เพื่อให้เข้าถึงง่าย
3. **Set as home dashboard** (Optional)
4. **Export JSON** เก็บเป็น backup

---

## ตัวอย่าง Layout (Text Art)

```
┌──────────────────────────────────────────────────────────────┐
│ Row 1: Overview                                              │
├────────────────┬──────────┬──────────┬──────────┐
│ Service Mgr    │ Total: 6 │ UP: 5    │ DOWN: 1  │
│ (iframe)       │ (stat)   │ (stat)   │ (stat)   │
└────────────────┴──────────┴──────────┴──────────┘

┌──────────────────────────────┬──────────────────────────────┐
│ Row 2: Status                │                              │
├──────────────────────────────┼──────────────────────────────┤
│ Service Status Grid          │ Up vs Down                   │
│ (status history - timeline)  │ (gauge)                      │
└──────────────────────────────┴──────────────────────────────┘

┌──────────────────────────────┬──────────────────────────────┐
│ Row 3: Availability          │                              │
├──────────────────────────────┼──────────────────────────────┤
│ Availability Table           │ Response Time                │
│ (table with colors)          │ (bar gauge)                  │
└──────────────────────────────┴──────────────────────────────┘

┌──────────────────────────────┬──────────────────────────────┐
│ Row 4: Trends                │                              │
├──────────────────────────────┼──────────────────────────────┤
│ Success Rate Over Time       │ Success by Service           │
│ (time series - area)         │ (time series - stacked)      │
└──────────────────────────────┴──────────────────────────────┘

┌──────────────────────────────┬──────────────────────────────┐
│ Row 5: Details               │                              │
├──────────────────────────────┼──────────────────────────────┤
│ DNS Lookup Time              │ Duration Heatmap             │
│ (time series)                │ (heatmap)                    │
└──────────────────────────────┴──────────────────────────────┘
```

สวยงาม ดูง่าย มีประโยชน์! 🎨✨
