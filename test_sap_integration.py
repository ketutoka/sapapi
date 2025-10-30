#!/usr/bin/env python3
"""
Test script untuk simulasi POST request dari SAP ke API
Untuk troubleshooting error 400
"""
import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"
SALES_ENDPOINT = f"{BASE_URL}/api/sales"

def test_valid_request():
    """Test dengan data yang valid"""
    print("🧪 Test 1: Valid request")
    data = [
        {
            "vkorg": "1000",
            "vtext": "PT. Sales",
            "erdat": "2025-10-30",
            "audat": "2025-10-30",
            "matkl": "MAT001",
            "wgbez": "Material Group 1",
            "matnr": "MATERIAL001",
            "maktx": "Sample Material",
            "route": "R001",
            "bezei": "Route 1",
            "kunnr": "CUST001",
            "name1": "Customer 1",
            "sorlt": "SORT001",
            "mvgr1": "MG1",
            "mvgtx": "Material Group Text",
            "meins": "PC",
            "waerk": "IDR",
            "kwmeng": 100.000,
            "netwr": 1000000.00
        }
    ]
    
    response = requests.post(SALES_ENDPOINT, json=data, headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_missing_required_fields():
    """Test dengan field required yang hilang"""
    print("🧪 Test 2: Missing required fields (vkorg)")
    data = [
        {
            "erdat": "2025-10-30",
            "matnr": "MATERIAL001"
        }
    ]
    
    response = requests.post(SALES_ENDPOINT, json=data, headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_invalid_json():
    """Test dengan JSON yang tidak valid"""
    print("🧪 Test 3: Invalid JSON format")
    invalid_data = '{"vkorg": "1000", "erdat": "2025-10-30"'  # Missing closing brace
    
    response = requests.post(SALES_ENDPOINT, data=invalid_data, headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_empty_request():
    """Test dengan request kosong"""
    print("🧪 Test 4: Empty request")
    
    response = requests.post(SALES_ENDPOINT, json=None, headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_wrong_content_type():
    """Test dengan content-type yang salah"""
    print("🧪 Test 5: Wrong content-type")
    data = {"vkorg": "1000", "erdat": "2025-10-30"}
    
    response = requests.post(SALES_ENDPOINT, data=json.dumps(data), headers={'Content-Type': 'text/plain'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

if __name__ == "__main__":
    print("🚀 Testing SAP API Error 400 scenarios...")
    print("=" * 60)
    
    try:
        # Test health check first
        health_response = requests.get(f"{BASE_URL}/api/health")
        if health_response.status_code == 200:
            print("✅ API server is running")
            print()
            
            # Run tests
            test_valid_request()
            test_missing_required_fields()
            test_invalid_json()
            test_empty_request()
            test_wrong_content_type()
            
        else:
            print("❌ API server is not responding")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on localhost:8000")
        print("   Run: python app.py")