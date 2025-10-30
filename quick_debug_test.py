#!/usr/bin/env python3
"""
Quick test untuk memverifikasi debug output berfungsi
"""
import requests
import json

# Test endpoint
url = "http://localhost:8000/api/sales"

print("🧪 Testing debug output...")

# Test 1: Data tanpa vkorg (should trigger error 400)
print("\n📤 Sending request without 'vkorg' field...")
test_data = {
    "erdat": "2025-10-30",
    "matnr": "TEST001"
}

try:
    response = requests.post(url, json=test_data, headers={'Content-Type': 'application/json'})
    print(f"📨 Response Status: {response.status_code}")
    print(f"📨 Response Body: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50)

# Test 2: Empty data
print("\n📤 Sending empty request...")
try:
    response = requests.post(url, json=None, headers={'Content-Type': 'application/json'})
    print(f"📨 Response Status: {response.status_code}")
    print(f"📨 Response Body: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Test completed. Check server console for debug output!")