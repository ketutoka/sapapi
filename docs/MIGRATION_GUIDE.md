# Migration Guide: Legacy ke CDC (Change Data Capture)

## Overview
Panduan migrasi dari endpoint legacy `/api/sales` ke endpoint CDC `/api/sales/cdc` yang lebih powerful dan tepat untuk use case SAP.

## Perbedaan Logic

### Before (Legacy): 
```
POST /api/sales
➜ Group by (vkorg, erdat)
➜ Delete each group individually  
➜ Insert new data per group
```

### After (CDC):
```
POST /api/sales/cdc
➜ Define date range (start_date, end_date)
➜ Delete ALL data in range
➜ Insert ALL new data
```

## Migration Scenarios

### Scenario 1: Daily Full Refresh
**Before:**
```bash
# SAP mengirim data per hari
curl -X POST /api/sales -d '[
  {"vkorg":"1000", "erdat":"2023-12-01", "matnr":"MAT001"},
  {"vkorg":"1000", "erdat":"2023-12-02", "matnr":"MAT002"}
]'
```

**After:**
```bash
# SAP mengirim data untuk periode tertentu
curl -X POST /api/sales/cdc -d '{
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-02"
  },
  "data": [
    {"vkorg":"1000", "erdat":"2023-12-01", "matnr":"MAT001"},
    {"vkorg":"1000", "erdat":"2023-12-02", "matnr":"MAT002"}
  ]
}'
```

### Scenario 2: Monthly Data Refresh
**Before:** Multiple requests per day
**After:** Single request per month

```bash
curl -X POST /api/sales/cdc -d '{
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  },
  "data": [
    // All December data in one request
  ]
}'
```

### Scenario 3: Data Correction
**Before:** Hard to correct specific date ranges
**After:** Easy correction for any date range

```bash
# Correct only specific date range
curl -X POST /api/sales/cdc -d '{
  "cdc_parameters": {
    "vkorg": "1000", 
    "start_date": "2023-12-15",
    "end_date": "2023-12-20"
  },
  "data": [
    // Corrected data for Dec 15-20 only
  ]
}'
```

## Step-by-Step Migration

### Phase 1: Analysis & Testing

#### Step 1: Analyze Current Data Patterns
```sql
-- Check current data distribution
SELECT 
    vkorg,
    DATE_TRUNC('month', erdat) as month,
    COUNT(*) as record_count,
    MIN(erdat) as first_date,
    MAX(erdat) as last_date
FROM dwh_sales 
GROUP BY vkorg, DATE_TRUNC('month', erdat)
ORDER BY vkorg, month;
```

#### Step 2: Test CDC Statistics
```bash
# Check what would be affected
curl -X POST /api/sales/cdc/statistics -d '{
  "vkorg": "1000",
  "start_date": "2023-12-01", 
  "end_date": "2023-12-31"
}'
```

#### Step 3: Test CDC Process with Sample Data
```bash
# Use test script
chmod +x tests/test_cdc.sh
./tests/test_cdc.sh
```

### Phase 2: SAP Integration Changes

#### Step 1: Update SAP Integration Code

**Before (Legacy Integration):**
```python
# Example SAP integration code
def send_daily_sales_data():
    for date in date_range:
        daily_data = get_sales_data_for_date(date)
        response = requests.post('/api/sales', json=daily_data)
```

**After (CDC Integration):**
```python
# New CDC integration code
def send_period_sales_data(start_date, end_date):
    period_data = get_sales_data_for_period(start_date, end_date)
    
    cdc_request = {
        "cdc_parameters": {
            "vkorg": "1000",
            "start_date": start_date,
            "end_date": end_date
        },
        "data": period_data
    }
    
    response = requests.post('/api/sales/cdc', json=cdc_request)
    return response
```

#### Step 2: Update SAP Scheduler

**Before:**
```
Daily Job:
- Extract yesterday's data
- Send to /api/sales
```

**After:**
```
Weekly/Monthly Job:
- Extract period data (e.g., current month)
- Send to /api/sales/cdc with date range
```

### Phase 3: Validation & Monitoring

#### Step 1: Parallel Run
Run both legacy and CDC in parallel for validation:

```python
def validate_cdc_vs_legacy():
    # Send via legacy
    legacy_response = send_legacy_data(data)
    
    # Send via CDC  
    cdc_response = send_cdc_data(cdc_params, data)
    
    # Compare results
    validate_results(legacy_response, cdc_response)
```

#### Step 2: Data Validation
```sql
-- Validate data consistency
SELECT 
    COUNT(*) as total_records,
    SUM(netwr) as total_amount,
    COUNT(DISTINCT erdat) as unique_dates
FROM dwh_sales 
WHERE vkorg = '1000' 
  AND erdat BETWEEN '2023-12-01' AND '2023-12-31';
```

#### Step 3: Performance Monitoring
```bash
# Monitor CDC performance
curl -w "Total time: %{time_total}s\n" \
  -X POST /api/sales/cdc \
  -H "Content-Type: application/json" \
  -d @large_cdc_request.json
```

### Phase 4: Full Migration

#### Step 1: Switch Primary Integration
- Update SAP job to use CDC endpoints
- Keep legacy as backup

#### Step 2: Update Documentation
- Update integration docs
- Train SAP team on new endpoints
- Update monitoring dashboards

#### Step 3: Cleanup Legacy (Optional)
After successful migration, optionally deprecate legacy endpoints.

## Best Practices for CDC

### 1. Batch Size Optimization
```json
{
  "cdc_parameters": {
    "vkorg": "1000",
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  },
  "data": [
    // Optimal: 1000-5000 records per request
  ]
}
```

### 2. Date Range Strategy
- **Daily refresh**: 1-day range
- **Weekly refresh**: 7-day range  
- **Monthly refresh**: 1-month range
- **Correction**: Specific affected dates only

### 3. Error Handling
```python
def safe_cdc_process(cdc_params, data):
    try:
        # Preview first
        stats = get_cdc_statistics(cdc_params)
        print(f"Will delete {stats['existing_records_count']} records")
        
        # Confirm before proceed
        if confirm_deletion():
            response = send_cdc_data(cdc_params, data)
            return response
    except Exception as e:
        handle_cdc_error(e)
```

### 4. Monitoring & Alerting
```python
def monitor_cdc_process():
    metrics = {
        'deleted_records': response['deleted_records'],
        'processed_records': response['processed_records'], 
        'processing_time': time_taken,
        'date_range': response['date_range_processed']
    }
    
    send_metrics_to_monitoring(metrics)
```

## Rollback Plan

If issues occur, rollback strategy:

### Emergency Rollback
1. Switch SAP integration back to legacy endpoints
2. Restore data from backup if needed
3. Investigate and fix issues

### Backup Strategy
```bash
# Before major CDC operations
sudo -u postgres pg_dump sapdwh | gzip > backup_before_cdc_$(date +%Y%m%d).sql.gz
```

## Testing Checklist

- [ ] CDC statistics endpoint works
- [ ] CDC process with small dataset works
- [ ] CDC process with large dataset works  
- [ ] Error handling for invalid parameters
- [ ] Performance acceptable for production volumes
- [ ] Data validation after CDC process
- [ ] Monitoring and alerting configured
- [ ] Backup and rollback procedures tested
- [ ] SAP team trained on new endpoints

## Support & Troubleshooting

### Common Issues
1. **Date range too large**: Reduce batch size
2. **Performance slow**: Check database indexes
3. **Memory issues**: Optimize batch size
4. **Connection timeout**: Increase timeout settings

### Getting Help
1. Check API logs: `sudo journalctl -u sapapi -f`
2. Database logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`
3. Performance monitoring: Use `/api/sales/cdc/statistics`
4. API documentation: Visit `/docs/` endpoint

### Contact
- Technical issues: Check troubleshooting guide
- Performance issues: Monitor with statistics endpoint
- Integration questions: Review CDC documentation