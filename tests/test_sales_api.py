import unittest
import json
from datetime import date
from app import app
from models import db, SalesData
from config import TestingConfig

class TestSalesAPI(unittest.TestCase):
    """Test cases untuk Sales API endpoints"""
    
    def setUp(self):
        """Setup untuk setiap test"""
        app.config.from_object(TestingConfig)
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Cleanup setelah setiap test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_post_sales_data_single_record(self):
        """Test POST single sales record"""
        sales_data = {
            'vkorg': '1000',
            'erdat': '2023-12-01',
            'audat': '2023-12-01',
            'matkl': 'MAT001',
            'wgbez': 'Material Group Description',
            'matnr': 'MATERIAL001',
            'maktx': 'Material Description',
            'route': 'R001',
            'bezei': 'Route Description',
            'kunnr': 'CUST001',
            'name1': 'Customer Name',
            'sorlt': 'SORT001',
            'mvgr1': 'MG1',
            'mvgtx': 'Material Group Desc',
            'meins': 'EA',
            'waerk': 'IDR',
            'kwmeng': 100.000,
            'netwr': 1000000.00
        }
        
        response = self.client.post(
            '/api/sales',
            data=json.dumps(sales_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['processed_records'], 1)
        
        # Verify data exists in database
        with self.app.app_context():
            record = SalesData.query.filter_by(vkorg='1000', matnr='MATERIAL001').first()
            self.assertIsNotNone(record)
            self.assertEqual(record.maktx, 'Material Description')
    
    def test_post_sales_data_multiple_records(self):
        """Test POST multiple sales records"""
        sales_data = [
            {
                'vkorg': '1000',
                'erdat': '2023-12-01',
                'matnr': 'MATERIAL001',
                'kwmeng': 100.000,
                'netwr': 1000000.00
            },
            {
                'vkorg': '1000',
                'erdat': '2023-12-01',
                'matnr': 'MATERIAL002',
                'kwmeng': 200.000,
                'netwr': 2000000.00
            }
        ]
        
        response = self.client.post(
            '/api/sales',
            data=json.dumps(sales_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['processed_records'], 2)
        
        # Verify both records exist in database
        with self.app.app_context():
            records = SalesData.query.filter_by(vkorg='1000').all()
            self.assertEqual(len(records), 2)
    
    def test_delete_insert_logic(self):
        """Test delete-insert logic"""
        # Insert initial data
        initial_data = {
            'vkorg': '1000',
            'erdat': '2023-12-01',
            'matnr': 'MATERIAL001',
            'kwmeng': 100.000,
            'netwr': 1000000.00
        }
        
        response = self.client.post(
            '/api/sales',
            data=json.dumps(initial_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Insert new data with same vkorg and erdat (should delete previous)
        new_data = {
            'vkorg': '1000',
            'erdat': '2023-12-01',  # Same date
            'matnr': 'MATERIAL002',  # Different material
            'kwmeng': 200.000,
            'netwr': 2000000.00
        }
        
        response = self.client.post(
            '/api/sales',
            data=json.dumps(new_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['processed_records'], 1)
        self.assertEqual(data['deleted_records'], 1)  # Previous record deleted
        
        # Verify only new record exists
        with self.app.app_context():
            records = SalesData.query.filter_by(vkorg='1000', erdat=date(2023, 12, 1)).all()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].matnr, 'MATERIAL002')
    
    def test_validation_missing_required_field(self):
        """Test validation for missing required fields"""
        sales_data = {
            'erdat': '2023-12-01',
            # Missing vkorg (required)
            'matnr': 'MATERIAL001'
        }
        
        response = self.client.post(
            '/api/sales',
            data=json.dumps(sales_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('vkorg', data['error'])
    
    def test_validation_invalid_date_format(self):
        """Test validation for invalid date format"""
        sales_data = {
            'vkorg': '1000',
            'erdat': '01-12-2023',  # Invalid format
            'matnr': 'MATERIAL001'
        }
        
        response = self.client.post(
            '/api/sales',
            data=json.dumps(sales_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('erdat', data['error'])
    
    def test_invalid_content_type(self):
        """Test invalid content type"""
        response = self.client.post(
            '/api/sales',
            data='invalid data',
            content_type='text/plain'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('application/json', data['error'])

if __name__ == '__main__':
    unittest.main()