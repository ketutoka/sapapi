# SAP API - Change Data Capture (CDC) Documentation

## Overview
Change Data Capture (CDC) adalah proses yang memungkinkan SAP mengirim data untuk periode tertentu dan mengganti semua data yang ada pada periode tersebut.

## Perbedaan CDC vs Regular Process

### Regular Process (Legacy):
```
POST /api/sales
- Group data berdasarkan (vkorg, erdat)
- Delete data dengan vkorg dan erdat yang sama
- Insert data baru
```

### CDC Process (New):
```
POST /api/sales/cdc
- Terima parameter range (vkorg, start_date, end_date)
- Delete SEMUA data dalam range tersebut
- Insert SEMUA data baru
```

## Use Case CDC

### Scenario 1: Daily Refresh
SAP mengirim data sales untuk 1 bulan penuh setiap hari:
```json
{
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  },
  "data": [
    // Semua data untuk bulan Desember 2023
  ]
}
```

### Scenario 2: Correction Process
SAP mengirim koreksi data untuk periode tertentu:
```json
{
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-15",
    "end_date": "2023-12-20"
  },
  "data": [
    // Data yang sudah dikoreksi untuk 15-20 Desember
  ]
}
```

## API Endpoints

### 1. CDC Process
**Endpoint:** `POST /api/sales/cdc`

**Request Body:**
```json
{
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  },
  "data": [
    {
      "vkorg": "1000",
      "erdat": "2023-12-15",
      "matnr": "MATERIAL001",
      "kwmeng": 100.0,
      "netwr": 1000000.0
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "CDC process completed successfully",
  "processed_records": 150,
  "deleted_records": 120,
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  },
  "date_range_processed": "2023-12-01 to 2023-12-31"
}
```

### 2. CDC Statistics (Preview)
**Endpoint:** `POST /api/sales/cdc/statistics`

**Request Body:**
```json
{
  "vkorg": "1000",
  "start_date": "2023-12-01",
  "end_date": "2023-12-31"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "CDC statistics retrieved",
  "statistics": {
    "vkorg": "1000",
    "date_range": {
      "start_date": "2023-12-01",
      "end_date": "2023-12-31"
    },
    "existing_records_count": 120,
    "existing_date_range": {
      "first_date": "2023-12-05",
      "last_date": "2023-12-28"
    }
  }
}
```

### 3. CDC Sample
**Endpoint:** `GET /api/sales/cdc/sample`

Menampilkan contoh format request untuk CDC.

## Testing CDC Process

### Step 1: Check Statistics
```bash
curl -X POST http://localhost:8000/api/sales/cdc/statistics \
  -H "Content-Type: application/json" \
  -d '{
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  }'
```

### Step 2: Process CDC
```bash
curl -X POST http://localhost:8000/api/sales/cdc \
  -H "Content-Type: application/json" \
  -d '{
    "cdc_parameters": {
      "vkorg": "1000",
      "start_date": "2023-12-01",
      "end_date": "2023-12-31"
    },
    "data": [
      {
        "vkorg": "1000",
        "erdat": "2023-12-15",
        "matnr": "MATERIAL001",
        "kwmeng": 100.0,
        "netwr": 1000000.0
      }
    ]
  }'
```

## Advantages CDC vs Legacy

### CDC Advantages:
1. **Precise Control**: Exact date range control
2. **Efficient**: One operation untuk period refresh
3. **Predictable**: Clear what will be deleted
4. **Flexible**: Different range per request
5. **Safe**: Preview dengan statistics endpoint

### Legacy Advantages:
1. **Simple**: No need date range parameter
2. **Backward Compatible**: Existing integrations work
3. **Incremental**: Good for single-day updates

## Best Practices

### 1. Use Statistics Before CDC
Always check statistics sebelum melakukan CDC process:
```bash
# Check what will be deleted
POST /api/sales/cdc/statistics

# Then process
POST /api/sales/cdc
```

### 2. Date Range Validation
- start_date <= end_date
- Format: YYYY-MM-DD
- Reasonable range (tidak terlalu besar)

### 3. Error Handling
CDC process atomic - jika error, semua rollback:
```json
{
  "error": "Validation error in record 5: erdat must be in YYYY-MM-DD format"
}
```

### 4. Monitoring
Monitor CDC operations:
- Records deleted vs inserted
- Date range processed
- Processing time
- Error rates

## Migration Strategy

### Phase 1: Dual Support
- Keep legacy `/api/sales` endpoint
- Add new CDC endpoints
- Test CDC dengan existing data

### Phase 2: CDC Adoption
- SAP team test CDC endpoints
- Validate results vs legacy
- Performance comparison

### Phase 3: Migration
- Switch SAP integration to CDC
- Keep legacy for backward compatibility
- Monitor performance

## Performance Considerations

### CDC Performance Tips:
1. **Batch Size**: Optimal 1000-5000 records per request
2. **Date Range**: Reasonable ranges (tidak > 1 tahun)
3. **Indexing**: Ensure (vkorg, erdat) index exists
4. **Connection Pool**: Configure proper DB pool
5. **Monitoring**: Track processing time

### Database Impact:
- DELETE operations pada range besar bisa lambat
- INSERT batch operations umumnya cepat
- Index pada (vkorg, erdat) sangat penting

## Troubleshooting

### Common Issues:

1. **"start_date > end_date"**
   - Solution: Check date parameter order

2. **"No records found in range"**
   - Solution: Normal, range mungkin kosong

3. **"Database timeout"**
   - Solution: Reduce batch size atau date range

4. **"Validation error"**
   - Solution: Check data format, especially dates

### Debug Tips:
```bash
# Check existing data in range
SELECT COUNT(*) FROM dwh_sales 
WHERE vkorg = '1000' 
  AND erdat BETWEEN '2023-12-01' AND '2023-12-31';

# Check application logs
sudo journalctl -u sapapi -f

# Check database connections
SELECT count(*) FROM pg_stat_activity WHERE datname='sapdwh';
```