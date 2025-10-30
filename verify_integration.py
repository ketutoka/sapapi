"""
Verification script untuk aplikasi Flask dengan PostgreSQL dan dwh_sales table
"""
import os
import requests
import time

def check_files_cleaned():
    """Check apakah file yang tidak diperlukan sudah dihapus"""
    removed_files = [
        'app_with_docs.py',
        'test_docs_api.py', 
        'test_simple.py',
        'test_api.py',
        'simple_app.py',
        'simple_flask_app.py',
        'run.bat'
    ]
    
    existing_files = []
    for file in removed_files:
        if os.path.exists(file):
            existing_files.append(file)
    
    if existing_files:
        print(f"⚠️ Files that should be removed but still exist: {existing_files}")
        return False
    else:
        print("✅ All unnecessary files have been removed")
        return True

def check_main_files():
    """Check apakah file utama masih ada"""
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        'config.py',
        'models.py',
        'run.py',
        'test_postgresql.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files are present")
        return True

def test_postgresql_features():
    """Test PostgreSQL specific features"""
    try:
        # Test database check endpoint
        print("🔍 Testing PostgreSQL database endpoint...")
        response = requests.get("http://127.0.0.1:8000/api/database/check")
        if response.status_code == 200:
            db_info = response.json()
            print("✅ Database check endpoint working")
            print(f"   Database type: {db_info.get('database_info', {}).get('database_type', 'Unknown')}")
            print(f"   Table name: {db_info.get('database_info', {}).get('table_name', 'Unknown')}")
            
            # Check if dwh_sales table exists
            table_stats = db_info.get('table_statistics', {})
            if 'total_records' in table_stats:
                print(f"   Table records: {table_stats['total_records']}")
                print("✅ Table dwh_sales exists and accessible")
            else:
                print("⚠️ Table dwh_sales may not exist yet")
            
            return True
        else:
            print(f"❌ Database check failed: {response.status_code}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app for PostgreSQL testing")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL testing error: {e}")
        return False

def test_app_integration():
    """Test apakah aplikasi berjalan dengan benar"""
    try:
        # Test documentation access
        print("🔍 Testing documentation access...")
        response = requests.get("http://127.0.0.1:8000/docs/")
        if response.status_code == 200:
            print("✅ Documentation accessible at /docs/")
        else:
            print(f"❌ Documentation not accessible: {response.status_code}")
            return False
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8000/api/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test PostgreSQL features
        postgresql_ok = test_postgresql_features()
        
        # Test integrated testing endpoint
        print("🔍 Testing integrated testing endpoint...")
        response = requests.get("http://127.0.0.1:8000/api/test/run")
        if response.status_code == 200:
            print("✅ Integrated testing endpoint working")
            result = response.json()
            print(f"Test Results: {result['test_summary']}")
        else:
            print(f"❌ Integrated testing failed: {response.status_code}")
            return False
        
        return postgresql_ok
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Verifying PostgreSQL integration and dwh_sales table...\n")
    
    # Check file cleanup
    files_clean = check_files_cleaned()
    print()
    
    # Check required files
    files_present = check_main_files()
    print()
    
    # Test app (if running)
    app_working = test_app_integration()
    print()
    
    # Summary
    if files_clean and files_present and app_working:
        print("🎉 SUCCESS: PostgreSQL integration completed successfully!")
        print("📖 Access documentation: http://localhost:8000/docs/")
        print("🗄️ Check database: http://localhost:8000/api/database/check")
        print("🧪 Run integrated tests: http://localhost:8000/api/test/run")
        print("📊 Table: dwh_sales in PostgreSQL database")
    elif files_clean and files_present:
        print("✅ File integration completed successfully!")
        print("ℹ️ Start the application with: python app.py")
        print("📖 Then access documentation: http://localhost:8000/docs/")
        print("🗄️ Database check: http://localhost:8000/api/database/check")
    else:
        print("⚠️ Integration partially completed. Please check the issues above.")