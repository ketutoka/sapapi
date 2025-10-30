# SAP API - Python Web API with Swagger Documentation & Integrated Testing

Aplikasi Web API Python untuk integrasi data SAP dengan documentation lengkap dan testing terintegrasi.

## Features

- **🚀 Flask-RESTX** dengan Swagger UI Documentation di `/docs/`
- **📊 POST Endpoint** untuk menyimpan data sales dari SAP
- **🔄 Delete-Insert Logic** berdasarkan `vkorg` (Sales Organization) dan `erdat` (Entry Date)  
- **📈 CDC (Change Data Capture)** dengan date range parameters untuk bulk data refresh
- **✅ Data Validation** untuk memastikan integritas data
- **🗄️ Database Support** untuk SQLite (development), PostgreSQL, MySQL, SQL Server
- **🧪 Integrated Testing** endpoint di `/api/test/run`
- **❤️ Health Check** endpoint
- **📋 Sample Data** endpoint untuk testing

## Quick Start

### 1. Installation
```bash
cd "c:\Users\oka wirasatha\project\sapapi"
pip install -r requirements.txt
```

### 2. Run Application
```bash
python app.py
```

### 3. Access Documentation
- **Swagger UI**: http://localhost:8000/docs/
- **API Base URL**: http://localhost:8000/api
- **Health Check**: http://localhost:8000/api/health
- **Run Tests**: http://localhost:8000/api/test/run

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs/` | GET | **Swagger UI Documentation** 📖 |
| `/api/health` | GET | Health check status |
| `/api/sales` | POST | Submit sales data (legacy delete-insert logic) |
| `/api/sales/cdc` | POST | **CDC Process** - Delete by date range, then insert all data |
| `/api/sales/cdc/statistics` | POST | **CDC Preview** - Show what will be deleted |
| `/api/sales/cdc/sample` | GET | CDC request format examples |
| `/api/sales/sample` | GET | Legacy sales data format |
| `/api/test/run` | GET | **Run integrated API tests** 🧪 |

### POST /api/sales/cdc (NEW - Recommended)
**Change Data Capture** endpoint untuk bulk data refresh dengan date range control.

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
      "kwmeng": 100.000,
      "netwr": 1000000.00
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

**Process:**
1. Delete semua records untuk vkorg="1000" dari 2023-12-01 sampai 2023-12-31
2. Insert semua data baru yang dikirim

### POST /api/sales (Legacy)
Endpoint untuk menyimpan data sales dari SAP dengan logic delete-insert per tanggal.

**Request Body (Single Record):**
```json
{
  "vkorg": "1000",
  "vtext": "PT. Sales",
  "erdat": "2023-12-01",
  "audat": "2023-12-01",
  "matkl": "MAT001",
  "wgbez": "Material Group Description",
  "matnr": "MATERIAL001",
  "maktx": "Material Description",
  "route": "R001",
  "bezei": "Route Description",
  "kunnr": "CUST001",
  "name1": "Customer Name",
  "sorlt": "SORT001",
  "mvgr1": "MG1",
  "mvgtx": "Material Group Desc",
  "meins": "EA",
  "waerk": "IDR",
  "kwmeng": 100.000,
  "netwr": 1000000.00
}
```

**Request Body (Multiple Records):**
```json
[
  {
    "vkorg": "1000",
    "erdat": "2023-12-01",
    "matnr": "MATERIAL001",
    "kwmeng": 100.000,
    "netwr": 1000000.00
  },
  {
    "vkorg": "1000", 
    "erdat": "2023-12-01",
    "matnr": "MATERIAL002",
    "kwmeng": 200.000,
    "netwr": 2000000.00
  }
]
```

**Response:**
```json
{
  "status": "success",
  "message": "Sales data saved successfully",
  "processed_records": 2,
  "deleted_records": 1
}
```

## Testing

### Integrated Testing (Recommended)
1. Start aplikasi: `python app.py`
2. Buka browser: http://localhost:8000/api/test/run
3. Lihat hasil testing otomatis

### Manual Testing via Swagger
1. Buka: http://localhost:8000/docs/
2. Expand endpoint yang ingin ditest
3. Klik "Try it out"
4. Input data dan klik "Execute"

### PowerShell Testing
```powershell
# Health Check
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET

# Post Sales Data
$body = @{
    vkorg = "1000"
    erdat = "2023-12-01"
    matnr = "MATERIAL001"
    kwmeng = 100.0
    netwr = 1000000.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/sales" -Method POST -Body $body -ContentType "application/json"
```

## Database Configuration

### SQLite (Default - Development)
```python
SQLALCHEMY_DATABASE_URI = "sqlite:///sapapi.db"
```

### PostgreSQL (Production)
```python
SQLALCHEMY_DATABASE_URI = "postgresql://user:password@localhost/sapapi"
```

### SQL Server
```python
SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"
```

## Data Model

Table: `sales_data`

| Field | Type | Description |
|-------|------|-------------|
| vkorg | String(4) | Sales Organization ⭐ Required |
| vtext | String(20) | Sales Org Description|
| erdat | Date | Entry Date ⭐ Required |
| audat | Date | Document Date |
| matkl | String(9) | Material Group |
| wgbez | String(20) | Material Group Description |
| matnr | String(40) | Material Number |
| maktx | String(40) | Material Description |
| route | String(6) | Route |
| bezei | String(40) | Route Description |
| kunnr | String(10) | Customer |
| name1 | String(35) | Customer Name |
| sorlt | String(10) | Sort Customer Name |
| mvgr1 | String(3) | Material Group 1 |
| mvgtx | String(40) | Material Group Description |
| meins | String(3) | Unit of Measure |
| waerk | String(5) | Currency |
| kwmeng | Numeric(13,3) | Sales Quantity |
| netwr | Numeric(15,2) | Sales Amount |

## Project Structure

```
sapapi/
├── app.py                      # 🎯 Main Flask application (All-in-One)
├── requirements.txt            # 📦 Dependencies
├── README.md                   # 📖 Documentation
├── config.py                   # ⚙️ Configuration settings
├── models.py                   # 🗄️ Database models
├── run.py                      # 🚀 Alternative runner
├── verify_integration.py       # ✅ Integration verification
├── services/
│   └── sales_service.py        # 💼 Business logic
└── tests/
    └── test_sales_api.py       # 🧪 Unit tests
```

## Environment Variables

Copy `.env.example` to `.env` dan sesuaikan:

```bash
# Flask configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=development

# Database configuration
DATABASE_URL=sqlite:///sapapi.db
# DATABASE_URL=postgresql://postgres:admin@localhost:5432/sapdwh

# Server configuration
HOST=127.0.0.1
PORT=8000
```

## Production Deployment

### Using Gunicorn
```bash
# Install gunicorn
pip install gunicorn

# Run production server
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Environment Setup
```bash
export FLASK_ENV=production
export DATABASE_URL="your-production-database-url"
export HOST="0.0.0.0"
export PORT="8000"
```

## Key Features Summary

✅ **Flask-RESTX Integration** - Swagger UI documentation  
✅ **Delete-Insert Logic** - Data consistency by vkorg + erdat  
✅ **Integrated Testing** - Built-in API testing endpoint  
✅ **Data Validation** - Request validation dengan error handling  
✅ **Sample Data** - Ready-to-use examples  
✅ **Health Monitoring** - Health check endpoint  
✅ **Database Ready** - SQLite default, production database support  
✅ **Clean Architecture** - Organized codebase  

## License

MIT License