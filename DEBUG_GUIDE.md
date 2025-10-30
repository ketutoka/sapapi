# Panduan Debugging Error 400 dari SAP Integration

## Setup Debug Mode

1. **Edit file .env:**
```
DEBUG=true
```

2. **Restart aplikasi:**
```bash
python app.py
```

## Melihat Log Debugging

Ketika ada request POST dari SAP yang error 400, Anda akan melihat log seperti ini:

```
📥 POST /api/sales - Content-Type: application/json
📥 Raw request data: b'{"vkorg":"1000","erdat":"2025-10-30"}'
📊 Parsed JSON data: {
  "vkorg": "1000",
  "erdat": "2025-10-30"
}
📋 Processing single record
✅ Successfully processed data: {'processed_records': 1, 'deleted_records': 0}
```

Jika ada error 400, Anda akan melihat:

```
❌ ValueError: vkorg dan erdat wajib diisi - Request data: {...data yang dikirim...}
```

## Testing dari SAP

1. **Jalankan aplikasi dalam debug mode:**
```bash
python app.py
```

2. **Kirim request dari SAP ke:**
```
POST http://your-server-ip:8000/api/sales
Content-Type: application/json
```

3. **Monitor log di console aplikasi untuk melihat:**
   - Raw data yang dikirim SAP
   - Parsed JSON data
   - Error messages dengan detail data

## Testing Manual

Jalankan test script:
```bash
python test_sap_integration.py
```

## Kemungkinan Penyebab Error 400:

1. **Missing required fields:** vkorg atau erdat tidak ada
2. **Invalid JSON format:** JSON tidak valid/corrupted
3. **Wrong Content-Type:** Bukan application/json
4. **Empty request body:** Tidak ada data yang dikirim
5. **Encoding issues:** Character encoding problems

## Solusi Production

Setelah selesai debugging, kembalikan:
```
DEBUG=false
```