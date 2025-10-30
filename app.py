"""
SAP Sales Data API - Flask dengan Swagger Documentation dan Testing
Gabungan lengkap dengan dokumentasi, testing, dan PostgreSQL support
"""
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import json
import threading
import time
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError

# Inisialisasi Flask app
app = Flask(__name__)

# Konfigurasi Flask dengan PostgreSQL support
# Default ke PostgreSQL berdasarkan .env, fallback ke SQLite untuk development
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/sapdwh')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_ENV', 'development') == 'development'

# Inisialisasi Flask-RESTX untuk Swagger documentation
api = Api(
    app,
    version='1.0',
    title='SAP Sales Data API',
    description='API untuk menyimpan data sales dari SAP dengan logic delete-insert dan testing terintegrasi',
    doc='/docs/',  # Swagger UI akan tersedia di /docs/
    prefix='/api'
)

# Namespace untuk organisasi endpoints
sales_ns = api.namespace('sales', description='Sales data operations')
health_ns = api.namespace('health', description='Health check operations')
test_ns = api.namespace('test', description='API testing operations')
db_ns = api.namespace('database', description='Database management operations')

# Initialize database
db = SQLAlchemy(app)

# Model untuk request/response documentation
sales_model = api.model('SalesData', {
    'vkorg': fields.String(required=True, description='Sales Organization', example='1000'),
    'erdat': fields.String(required=True, description='Entry Date (YYYY-MM-DD)', example='2023-12-01'),
    'audat': fields.String(description='Document Date (YYYY-MM-DD)', example='2023-12-01'),
    'matkl': fields.String(description='Material Group', example='MAT001'),
    'wgbez': fields.String(description='Material Group Description', example='Material Group Description'),
    'matnr': fields.String(description='Material Number', example='MATERIAL001'),
    'maktx': fields.String(description='Material Description', example='Material Description'),
    'route': fields.String(description='Route', example='R001'),
    'bezei': fields.String(description='Route Description', example='Route Description'),
    'kunnr': fields.String(description='Customer', example='CUST001'),
    'name1': fields.String(description='Customer Name', example='Customer Name'),
    'sorlt': fields.String(description='Sort Customer Name', example='SORT001'),
    'mvgr1': fields.String(description='Material Group 1', example='MG1'),
    'mvgtx': fields.String(description='Material Group Description', example='Material Group Desc'),
    'meins': fields.String(description='Unit of Measure', example='EA'),
    'waerk': fields.String(description='Currency', example='IDR'),
    'kwmeng': fields.Float(description='Sales Quantity', example=100.000),
    'netwr': fields.Float(description='Sales Amount', example=1000000.00)
})

response_model = api.model('ApiResponse', {
    'status': fields.String(description='Response status', example='success'),
    'message': fields.String(description='Response message', example='Sales data saved successfully'),
    'processed_records': fields.Integer(description='Number of processed records', example=1),
    'deleted_records': fields.Integer(description='Number of deleted records', example=0)
})

health_model = api.model('HealthResponse', {
    'status': fields.String(description='Health status', example='healthy'),
    'message': fields.String(description='Health message', example='SAP API is running'),
    'timestamp': fields.String(description='Current timestamp', example='2023-12-01T10:00:00'),
    'version': fields.String(description='API version', example='1.0.0')
})

# PostgreSQL DWH Sales Data model
class DwhSales(db.Model):
    __tablename__ = 'dwh_sales'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vkorg = db.Column(db.String(4), nullable=False, comment='Sales Organization')
    erdat = db.Column(db.Date, nullable=False, comment='Entry Date')
    audat = db.Column(db.Date, nullable=True, comment='Document Date')
    matkl = db.Column(db.String(9), nullable=True, comment='Material Group')
    wgbez = db.Column(db.String(20), nullable=True, comment='Material Group Description')
    matnr = db.Column(db.String(18), nullable=True, comment='Material Number')
    maktx = db.Column(db.String(40), nullable=True, comment='Material Description')
    route = db.Column(db.String(6), nullable=True, comment='Route')
    bezei = db.Column(db.String(30), nullable=True, comment='Route Description')
    kunnr = db.Column(db.String(10), nullable=True, comment='Customer')
    name1 = db.Column(db.String(35), nullable=True, comment='Customer Name')
    sorlt = db.Column(db.String(10), nullable=True, comment='Sort Customer Name')
    mvgr1 = db.Column(db.String(3), nullable=True, comment='Material Group 1')
    mvgtx = db.Column(db.String(20), nullable=True, comment='Material Group Description')
    meins = db.Column(db.String(3), nullable=True, comment='Unit of Measure')
    waerk = db.Column(db.String(5), nullable=True, comment='Currency')
    kwmeng = db.Column(db.Numeric(13, 3), nullable=True, comment='Sales Quantity')
    netwr = db.Column(db.Numeric(15, 2), nullable=True, comment='Sales Amount')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='Record Creation Time')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Record Update Time')
    
    # Index untuk performance (PostgreSQL specific)
    __table_args__ = (
        db.Index('idx_dwh_sales_vkorg_erdat', 'vkorg', 'erdat'),
        db.Index('idx_dwh_sales_created_at', 'created_at'),
        db.Index('idx_dwh_sales_matnr', 'matnr'),
        db.Index('idx_dwh_sales_kunnr', 'kunnr'),
        {'comment': 'Data Warehouse Sales table untuk SAP integration'}
    )
    
    def __repr__(self):
        return f'<DwhSales {self.vkorg}-{self.erdat}-{self.matnr}>'
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'vkorg': self.vkorg,
            'erdat': self.erdat.isoformat() if self.erdat else None,
            'audat': self.audat.isoformat() if self.audat else None,
            'matkl': self.matkl,
            'wgbez': self.wgbez,
            'matnr': self.matnr,
            'maktx': self.maktx,
            'route': self.route,
            'bezei': self.bezei,
            'kunnr': self.kunnr,
            'name1': self.name1,
            'sorlt': self.sorlt,
            'mvgr1': self.mvgr1,
            'mvgtx': self.mvgtx,
            'meins': self.meins,
            'waerk': self.waerk,
            'kwmeng': float(self.kwmeng) if self.kwmeng else None,
            'netwr': float(self.netwr) if self.netwr else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Legacy SalesData model untuk backward compatibility (tetap menggunakan nama lama)
class SalesData(DwhSales):
    """Legacy alias untuk DwhSales - untuk backward compatibility"""
    __tablename__ = 'dwh_sales'  # Gunakan table yang sama

# Enhanced service class dengan PostgreSQL support
class SalesService:
    def __init__(self):
        self.model = DwhSales  # Menggunakan DwhSales sebagai model utama
    
    def process_sales_data_batch(self, data_list):
        """Process batch data sales dengan logic delete-insert untuk PostgreSQL"""
        if not data_list:
            raise ValueError("No data provided")
        
        # Group data by vkorg and erdat
        grouped_data = {}
        for data in data_list:
            key = (data['vkorg'], data['erdat'])
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(data)
        
        total_deleted = 0
        processed_records = []
        
        try:
            for (vkorg, erdat), records in grouped_data.items():
                # Delete existing records dengan PostgreSQL syntax
                deleted_count = db.session.query(self.model).filter(
                    self.model.vkorg == vkorg,
                    self.model.erdat == datetime.strptime(erdat, '%Y-%m-%d').date()
                ).delete(synchronize_session=False)
                total_deleted += deleted_count
                
                # Insert new records
                for record in records:
                    sales_record = self.model(
                        vkorg=record.get('vkorg'),
                        erdat=datetime.strptime(record['erdat'], '%Y-%m-%d').date() if isinstance(record['erdat'], str) else record['erdat'],
                        audat=datetime.strptime(record['audat'], '%Y-%m-%d').date() if record.get('audat') and isinstance(record['audat'], str) else record.get('audat'),
                        matkl=record.get('matkl'),
                        wgbez=record.get('wgbez'),
                        matnr=record.get('matnr'),
                        maktx=record.get('maktx'),
                        route=record.get('route'),
                        bezei=record.get('bezei'),
                        kunnr=record.get('kunnr'),
                        name1=record.get('name1'),
                        sorlt=record.get('sorlt'),
                        mvgr1=record.get('mvgr1'),
                        mvgtx=record.get('mvgtx'),
                        meins=record.get('meins'),
                        waerk=record.get('waerk'),
                        kwmeng=record.get('kwmeng'),
                        netwr=record.get('netwr')
                    )
                    db.session.add(sales_record)
                    processed_records.append(sales_record)
            
            # Commit dengan PostgreSQL optimization
            db.session.commit()
            
            return {
                'processed_records': len(processed_records),
                'deleted_records': total_deleted,
                'groups_processed': len(grouped_data)
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error processing sales data: {str(e)}")

# Database initialization functions
def check_database_connection():
    """Check PostgreSQL database connection"""
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def create_table_if_not_exists():
    """Create dwh_sales table if it doesn't exist in PostgreSQL"""
    try:
        with app.app_context():
            # Check if table exists using SQLAlchemy inspector
            inspector = inspect(db.engine)
            table_exists = inspector.has_table('dwh_sales')
            
            if not table_exists:
                print("📦 Table 'dwh_sales' not found. Creating...")
                
                # Create all tables defined in models
                db.create_all()
                
                # Verify table creation
                inspector = inspect(db.engine)
                if inspector.has_table('dwh_sales'):
                    print("✅ Table 'dwh_sales' created successfully in PostgreSQL")
                    
                    # Get table info
                    columns = inspector.get_columns('dwh_sales')
                    indexes = inspector.get_indexes('dwh_sales')
                    
                    print(f"📊 Table created with {len(columns)} columns and {len(indexes)} indexes")
                    return True, "Table created successfully"
                else:
                    return False, "Table creation failed"
            else:
                print("✅ Table 'dwh_sales' already exists")
                
                # Get table info
                columns = inspector.get_columns('dwh_sales')
                indexes = inspector.get_indexes('dwh_sales')
                print(f"📊 Existing table has {len(columns)} columns and {len(indexes)} indexes")
                
                return True, "Table already exists"
                
    except Exception as e:
        return False, f"Error creating table: {str(e)}"

# Initialize services
sales_service = SalesService()

# Testing Functions (Integrated)
def run_api_tests(base_url):
    """Run comprehensive API tests"""
    def test_health():
        try:
            response = requests.get(f"{base_url}/health")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)

    def test_sales_single():
        try:
            sales_data = {
                "vkorg": "1000",
                "erdat": "2023-12-01",
                "matnr": "MATERIAL001",
                "kwmeng": 100.0,
                "netwr": 1000000.0
            }
            response = requests.post(f"{base_url}/sales", json=sales_data, headers={'Content-Type': 'application/json'})
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)

    tests = {
        "health": test_health(),
        "sales_single": test_sales_single()
    }
    
    return tests

# API Endpoints dengan Flask-RESTX

# Health Check Endpoint
@health_ns.route('')
class HealthCheck(Resource):
    @api.doc('health_check')
    @api.marshal_with(health_model)
    def get(self):
        """Health check endpoint - Cek status API"""
        return {
            'status': 'healthy',
            'message': 'SAP API is running',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }, 200

# Sales Data Endpoints
@sales_ns.route('')
class SalesDataResource(Resource):
    @api.doc('save_sales_data')
    @api.expect([sales_model], validate=True)
    @api.marshal_with(response_model)
    def post(self):
        """
        Simpan data sales dari SAP
        
        Logic: Delete-Insert berdasarkan vkorg (Sales Organization) dan erdat (Entry Date)
        """
        try:
            data = request.get_json()
            
            if not data:
                api.abort(400, 'No data provided')
            
            # Validasi field required
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if 'vkorg' not in item or 'erdat' not in item:
                        api.abort(400, f'Record {i+1}: vkorg dan erdat wajib diisi')
            else:
                if 'vkorg' not in data or 'erdat' not in data:
                    api.abort(400, 'vkorg dan erdat wajib diisi')
            
            # Process data dengan SalesService
            if isinstance(data, list):
                result = sales_service.process_sales_data_batch(data)
            else:
                result = sales_service.process_sales_data_batch([data])
            
            return {
                'status': 'success',
                'message': 'Sales data saved successfully',
                'processed_records': result['processed_records'],
                'deleted_records': result['deleted_records']
            }, 200
            
        except ValueError as ve:
            api.abort(400, str(ve))
        except Exception as e:
            api.abort(500, f'Internal server error: {str(e)}')

@sales_ns.route('/sample')
class SampleData(Resource):
    @api.doc('get_sample_data')
    def get(self):
        """Contoh format data sales untuk testing"""
        return {
            "single_record": {
                "vkorg": "1000",
                "erdat": "2023-12-01",
                "audat": "2023-12-01",
                "matkl": "MAT001",
                "wgbez": "Material Group Description",
                "matnr": "MATERIAL001",
                "maktx": "Material Description",
                "kwmeng": 100.0,
                "netwr": 1000000.0
            },
            "multiple_records": [
                {
                    "vkorg": "1000",
                    "erdat": "2023-12-01",
                    "matnr": "MATERIAL001",
                    "kwmeng": 100.0,
                    "netwr": 1000000.0
                },
                {
                    "vkorg": "1000",
                    "erdat": "2023-12-01",
                    "matnr": "MATERIAL002",
                    "kwmeng": 200.0,
                    "netwr": 2000000.0
                }
            ]
        }, 200

# Database Management Endpoints
@db_ns.route('/check')
class DatabaseCheck(Resource):
    @api.doc('check_database')
    def get(self):
        """Check PostgreSQL database connection dan table status"""
        try:
            # Check connection
            conn_success, conn_message = check_database_connection()
            
            # Check table
            table_success, table_message = create_table_if_not_exists()
            
            # Get database info
            db_info = {
                'database_type': 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite',
                'database_url': app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'Local',
                'table_name': 'dwh_sales'
            }
            
            # Get table statistics jika koneksi berhasil
            table_stats = {}
            if conn_success and table_success:
                try:
                    with app.app_context():
                        total_records = db.session.query(DwhSales).count()
                        latest_record = db.session.query(DwhSales).order_by(DwhSales.created_at.desc()).first()
                        
                        table_stats = {
                            'total_records': total_records,
                            'latest_record_date': latest_record.created_at.isoformat() if latest_record else None,
                            'table_exists': True
                        }
                except Exception as e:
                    table_stats = {'error': f'Error getting table stats: {str(e)}'}
            
            return {
                'database_connection': {
                    'success': conn_success,
                    'message': conn_message
                },
                'table_status': {
                    'success': table_success,
                    'message': table_message
                },
                'database_info': db_info,
                'table_statistics': table_stats,
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            return {
                'error': f'Database check failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, 500

@db_ns.route('/create-table')
class CreateTable(Resource):
    @api.doc('create_table')
    def post(self):
        """Force create dwh_sales table (untuk troubleshooting)"""
        try:
            success, message = create_table_if_not_exists()
            
            return {
                'success': success,
                'message': message,
                'table_name': 'dwh_sales',
                'timestamp': datetime.now().isoformat()
            }, 200 if success else 500
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Table creation failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, 500

# Testing Endpoint
@test_ns.route('/run')
class TestRunner(Resource):
    @api.doc('run_tests')
    def get(self):
        """Jalankan automated testing untuk semua endpoints"""
        base_url = request.host_url.rstrip('/') + '/api'
        
        # Wait a moment for server to be ready
        time.sleep(1)
        
        test_results = run_api_tests(base_url)
        
        passed = sum(1 for success, _ in test_results.values() if success)
        total = len(test_results)
        
        return {
            'test_summary': {
                'passed': passed,
                'total': total,
                'success_rate': f"{(passed/total)*100:.1f}%"
            },
            'results': test_results,
            'message': 'All tests passed!' if passed == total else 'Some tests failed'
        }, 200

# Legacy endpoints untuk backward compatibility
@app.route('/api/sales', methods=['POST'])
def save_sales_data_legacy():
    """Legacy endpoint - gunakan /api/sales dari Swagger untuk dokumentasi lengkap"""
    return SalesDataResource().post()

@app.route('/api/health', methods=['GET'])
def health_check_legacy():
    """Legacy endpoint - gunakan /api/health dari Swagger untuk dokumentasi lengkap"""
    return HealthCheck().get()[0]

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'docs': '/docs/'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Get configuration
    host = os.environ.get('HOST', '127.0.0.1') 
    port = int(os.environ.get('PORT', 8000))  # Default port 8000 untuk konsistensi
    debug = app.config.get('DEBUG', True)
    
    print(f"🚀 Starting SAP API Flask Server with PostgreSQL DWH Support...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"🗄️ Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"📖 API Documentation: http://{host}:{port}/docs/")
    print(f"🌐 Base URL: http://{host}:{port}/api")
    
    # Check database connection and create table
    print("\n📊 Initializing Database...")
    with app.app_context():
        try:
            # Check database connection
            conn_success, conn_message = check_database_connection()
            print(f"🔌 Database Connection: {conn_message}")
            
            if conn_success:
                # Create table if not exists
                table_success, table_message = create_table_if_not_exists()
                print(f"📦 Table Status: {table_message}")
                
                if table_success:
                    # Get table info
                    try:
                        total_records = db.session.query(DwhSales).count()
                        print(f"📊 Current records in dwh_sales: {total_records}")
                    except Exception as e:
                        print(f"⚠️ Could not get record count: {e}")
                else:
                    print("❌ Table creation failed - API will still start but database operations may fail")
            else:
                print("❌ Database connection failed - API will start in limited mode")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            print("⚠️ API will start but database operations may fail")
    
    print(f"\n🌐 API Endpoints:")
    print(f"❤️ Health Check: http://{host}:{port}/api/health")
    print(f"📊 Sales Endpoint: http://{host}:{port}/api/sales")
    print(f"📋 Sample Data: http://{host}:{port}/api/sales/sample")
    print(f"🧪 Run Tests: http://{host}:{port}/api/test/run")
    print(f"🗄️ Database Check: http://{host}:{port}/api/database/check")
    print(f"📦 Create Table: http://{host}:{port}/api/database/create-table")
    
    # Run the app
    app.run(debug=debug, host=host, port=port)