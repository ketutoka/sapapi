#!/usr/bin/env python3

"""
Quick test script untuk CDC functionality
Test apakah CDC service bisa jalan tanpa Flask app context error
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cdc_import():
    """Test import CDC service"""
    try:
        from services.sales_service_cdc import SalesService as CDCSalesService
        from app import db, DwhSales
        
        # Initialize service dengan dependency injection
        cdc_service = CDCSalesService(db_instance=db, model_class=DwhSales)
        
        print("✅ CDC Service import successful")
        print(f"✅ Database instance: {type(cdc_service._get_db())}")
        print(f"✅ Model class: {cdc_service._get_model().__name__}")
        return True
        
    except Exception as e:
        print(f"❌ CDC Service import failed: {e}")
        return False

def test_cdc_validation():
    """Test CDC validation methods"""
    try:
        from services.sales_service_cdc import SalesService as CDCSalesService
        from app import db, DwhSales
        
        cdc_service = CDCSalesService(db_instance=db, model_class=DwhSales)
        
        # Test CDC parameters validation
        test_params = {
            'vkorg': '1000',
            'start_date': '2023-12-01',
            'end_date': '2023-12-31'
        }
        
        result = cdc_service.validate_cdc_parameters(test_params)
        print(f"✅ CDC parameters validation: {result}")
        
        # Test sales data validation
        test_data = {
            'vkorg': '1000',
            'erdat': '2023-12-15'
        }
        
        result = cdc_service.validate_sales_data(test_data)
        print(f"✅ Sales data validation: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ CDC validation test failed: {e}")
        return False

def test_flask_app_context():
    """Test dengan Flask app context"""
    try:
        from app import app, db, DwhSales
        from services.sales_service_cdc import SalesService as CDCSalesService
        
        with app.app_context():
            cdc_service = CDCSalesService(db_instance=db, model_class=DwhSales)
            
            # Test statistics method (read-only, tidak modify data)
            test_params = {
                'vkorg': '1000',
                'start_date': '2023-12-01',
                'end_date': '2023-12-31'
            }
            
            stats = cdc_service.get_cdc_statistics('1000', '2023-12-01', '2023-12-31')
            print(f"✅ CDC statistics test successful: {stats}")
            
        return True
        
    except Exception as e:
        print(f"❌ Flask app context test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing CDC Service Fixes...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_cdc_import),
        ("Validation Test", test_cdc_validation), 
        ("Flask Context Test", test_flask_app_context)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! CDC service should work correctly now.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print("\n💡 Next step: Test CDC endpoint via HTTP request")
    print("   curl -X POST http://localhost:8000/api/sales/cdc/sample")