"""
Script untuk testing PostgreSQL connection dan table creation
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

def test_postgresql_connection():
    """Test koneksi ke PostgreSQL database"""
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/sapdwh')
    
    print(f"🔌 Testing PostgreSQL connection...")
    print(f"Database URL: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful!")
            print(f"📊 PostgreSQL version: {version[:50]}...")
            
            # Test basic database operations
            conn.execute(text('SELECT current_database(), current_user'))
            print(f"✅ Database operations working")
            
            return True, engine
            
    except OperationalError as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Please check:")
        print("   - PostgreSQL server is running")
        print("   - Database 'sapdwh' exists")
        print("   - Username/password are correct")
        print("   - Host and port are accessible")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def test_table_operations(engine):
    """Test table creation and operations"""
    if not engine:
        return False
    
    print(f"\n📦 Testing table operations...")
    
    try:
        # Check if table exists
        inspector = inspect(engine)
        table_exists = inspector.has_table('dwh_sales')
        
        print(f"📊 Table 'dwh_sales' exists: {table_exists}")
        
        if table_exists:
            # Get table info
            columns = inspector.get_columns('dwh_sales')
            indexes = inspector.get_indexes('dwh_sales')
            
            print(f"📋 Table columns: {len(columns)}")
            print(f"🔍 Table indexes: {len(indexes)}")
            
            # Test basic query
            with engine.connect() as conn:
                result = conn.execute(text('SELECT COUNT(*) FROM dwh_sales'))
                count = result.fetchone()[0]
                print(f"📊 Current records: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Table operations failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 PostgreSQL Database Testing for SAP API\n")
    
    # Test connection
    conn_success, engine = test_postgresql_connection()
    
    if conn_success:
        # Test table operations
        table_success = test_table_operations(engine)
        
        if table_success:
            print(f"\n🎉 All database tests passed!")
            print(f"✅ Ready to run: python app.py")
        else:
            print(f"\n⚠️ Connection OK but table operations failed")
            print(f"💡 The app will try to create tables automatically")
    else:
        print(f"\n❌ Database connection failed")
        print(f"💡 Please fix PostgreSQL connection before running the app")
        
    print(f"\n📖 After fixing issues, start the app with:")
    print(f"   python app.py")
    print(f"   Then check: http://localhost:8000/api/database/check")

if __name__ == "__main__":
    main()