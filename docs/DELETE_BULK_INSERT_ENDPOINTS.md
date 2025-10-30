# DELETE & BULK INSERT ENDPOINTS DOCUMENTATION

## Overview
Berdasarkan permintaan untuk memisahkan logic delete dan insert, saya telah membuat endpoint khusus yang memberikan control lebih baik terhadap proses CDC (Change Data Capture).

## Endpoints Baru

### 1. Delete Sales Endpoint
**URL:** `POST /api/sales/delete`

**Purpose:** Delete data sales berdasarkan vkorg dan date range

**Request Format:**
```json
{
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
}
```

**Response Format:**
```json
{
    "status": "success",
    "message": "Successfully deleted 15 records for vkorg 1000 from 2023-12-01 to 2023-12-31",
    "deleted_count": 15,
    "vkorg": "1000",
    "date_range": {
        "start_date": "2023-12-01",
        "end_date": "2023-12-31"
    },
    "total_deleted_records": 15
}
```

**Features:**
- ✅ Detailed validation untuk parameter input
- ✅ Preview record yang akan dihapus (max 10 dalam response)
- ✅ Atomic operation dengan rollback jika error
- ✅ Logging untuk audit trail

### 2. Bulk Insert Endpoint
**URL:** `POST /api/sales/bulk-insert`

**Purpose:** Insert banyak data sales sekaligus dengan optimization

**Request Format:**
```json
[
    {
        "vkorg": "1000",
        "vtext": "Sales Organization",
        "erdat": "2023-12-05",
        "matnr": "MATERIAL001",
        "maktx": "Material Description",
        "kunnr": "CUSTOMER001",
        "name1": "Customer Name",
        "kwmeng": 100.0,
        "netwr": 1000000.0
    },
    {
        "vkorg": "1000",
        "vtext": "Sales Organization",
        "erdat": "2023-12-10",
        "matnr": "MATERIAL002",
        "maktx": "Material Description 2",
        "kunnr": "CUSTOMER002",
        "name1": "Customer Name 2",
        "kwmeng": 200.0,
        "netwr": 2000000.0
    }
]
```

**Response Format:**
```json
{
    "status": "success",
    "message": "Successfully inserted 4 sales records",
    "inserted_count": 4,
    "summary": {
        "by_vkorg": {
            "1000": 4
        },
        "by_date": {
            "2023-12-05": 1,
            "2023-12-10": 1,
            "2023-12-20": 1,
            "2023-12-25": 1
        },
        "total_records": 4,
        "total_amount": 12000000.0
    }
}
```

**Features:**
- ✅ Bulk insert optimization untuk performance
- ✅ Detailed statistics (by vkorg, by date, total amount)
- ✅ Validation semua record sebelum insert
- ✅ Atomic operation dengan rollback jika error

### 3. Enhanced Sample Endpoint
**URL:** `GET /api/sales/sample`

**Updated Response:** Sekarang termasuk examples untuk delete dan bulk insert:
```json
{
    "single_record": {...},
    "multiple_records": [...],
    "delete_request_example": {
        "vkorg": "1000",
        "start_date": "2023-12-01",
        "end_date": "2023-12-31"
    },
    "bulk_insert_example": [
        {
            "vkorg": "1000",
            "vtext": "PT. Sales Indonesia",
            "erdat": "2023-12-15",
            "matnr": "MATERIAL001",
            "maktx": "Product A",
            "kunnr": "CUST001",
            "name1": "Customer A",
            "kwmeng": 100.0,
            "netwr": 1000000.0
        },
        {
            "vkorg": "1000",
            "vtext": "PT. Sales Indonesia",
            "erdat": "2023-12-16",
            "matnr": "MATERIAL002",
            "maktx": "Product B",
            "kunnr": "CUST002",
            "name1": "Customer B",
            "kwmeng": 200.0,
            "netwr": 2000000.0
        }
    ]
}
```

## Service Layer Enhancements

### SalesService Class (CDC)
File: `services/sales_service_cdc.py`

**New Methods:**

1. **`delete_sales_by_range(vkorg, start_date, end_date)`**
   - Delete sales berdasarkan date range
   - Return detailed info tentang record yang dihapus
   - Include preview record yang dihapus

2. **`bulk_insert_sales(data_list)`**
   - Optimized bulk insert
   - Detailed statistics dan monitoring
   - Pre-validation semua data

3. **Enhanced `process_sales_data_cdc()`**
   - Improved error handling
   - Better logging dan audit trail

## Use Cases & Workflow

### Scenario 1: Manual Control (Recommended)
```
1. GET /api/sales/cdc/statistics  → Preview apa yang akan dihapus
2. POST /api/sales/delete         → Delete data lama
3. POST /api/sales/bulk-insert    → Insert data baru
```

**Advantages:**
- ✅ Full control setiap step
- ✅ Bisa preview sebelum delete
- ✅ Bisa monitor setiap operasi
- ✅ Rollback individual jika perlu

### Scenario 2: Automated CDC (Existing)
```
1. POST /api/sales/cdc           → Delete + Insert dalam satu call
```

**Advantages:**
- ✅ Single API call
- ✅ Atomic operation
- ✅ Backward compatibility

## Technical Features

### Error Handling
- ✅ Comprehensive validation
- ✅ Rollback pada error
- ✅ Detailed error messages
- ✅ Audit logging

### Performance Optimization
- ✅ Bulk operations untuk database
- ✅ Minimal round-trips
- ✅ Memory efficient processing
- ✅ Index optimization (PostgreSQL)

### Monitoring & Statistics
- ✅ Record counts dan summaries
- ✅ Processing time tracking
- ✅ Database operation metrics
- ✅ Date range statistics

## Testing

### Available Test Files
1. `test_delete_bulk_insert.py` - Comprehensive testing
2. `quick_test_endpoints.py` - Quick validation

### Manual Testing via Swagger
Access: `http://localhost:8000/docs/`

**Available Sections:**
- Sales Data Operations
  - POST /api/sales/delete
  - POST /api/sales/bulk-insert
  - POST /api/sales/cdc
  - GET /api/sales/sample
  - POST /api/sales/cdc/statistics

## API Documentation

All endpoints tersedia di Swagger UI dengan:
- ✅ Request/response models
- ✅ Validation schemas
- ✅ Example data
- ✅ Interactive testing

**Swagger URL:** `http://localhost:8000/docs/`

## Database Impact

### Table Structure
- Menggunakan existing `dwh_sales` table
- Index optimization untuk vkorg + erdat
- PostgreSQL specific optimizations

### Performance Considerations
- Bulk delete dengan `synchronize_session=False`
- Batch insert operations
- Transaction management dengan rollback
- Index usage untuk date range queries

## Migration Guide

### From Old Logic
**Before:**
```python
# Manual delete-insert per record
for record in data:
    delete_existing(vkorg, erdat)
    insert_new(record)
```

**After - Option 1 (Manual Control):**
```python
# Step by step dengan control penuh
delete_sales_by_range(vkorg, start_date, end_date)
bulk_insert_sales(all_data)
```

**After - Option 2 (Automated):**
```python
# Single call CDC
process_sales_data_cdc(cdc_params, data_list)
```

## Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:port/database
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### Gunicorn Configuration
```bash
gunicorn -w 4 -k gevent --bind 0.0.0.0:8000 app:app
```

### Monitoring Endpoints
- Health Check: `/api/health`
- Database Check: `/api/database/check`
- Test Runner: `/api/test/run`

## Security Features

- ✅ Input validation dan sanitization
- ✅ SQL injection prevention
- ✅ Transaction rollback pada error
- ✅ Audit logging untuk compliance

## Next Steps

1. **Testing** - Run comprehensive tests
2. **Performance** - Monitor dalam production load
3. **Monitoring** - Setup alerts untuk error rate
4. **Documentation** - Update deployment guides

---

**Author:** GitHub Copilot  
**Date:** October 30, 2025  
**Version:** 1.0  
**Status:** Ready for Production Testing