#!/usr/bin/env python3
"""
Test script untuk memverifikasi apakah file .env terbaca dengan benar
"""
import os
from dotenv import load_dotenv

print("🔍 Testing Environment Variables...")
print("=" * 50)

# Load .env file
load_dotenv()

# Test variables
test_vars = [
    'DATABASE_URL',
    'HOST', 
    'PORT',
    'DEBUG',
    'SECRET_KEY',
    'FLASK_ENV',
    'LOG_LEVEL'
]

print("📁 Environment Variables dari .env file:")
for var in test_vars:
    value = os.environ.get(var, 'NOT SET')
    # Mask sensitive information
    if 'SECRET' in var or 'PASSWORD' in var or 'DATABASE_URL' in var:
        if value != 'NOT SET' and len(value) > 10:
            masked_value = value[:10] + '***' + value[-3:]
        else:
            masked_value = value
        print(f"  {var}: {masked_value}")
    else:
        print(f"  {var}: {value}")

print("\n" + "=" * 50)

# Test database URL specifically
db_url = os.environ.get('DATABASE_URL', 'NOT SET')
if db_url != 'NOT SET':
    print("✅ DATABASE_URL terbaca dari .env file")
    if 'localhost' in db_url:
        print("⚠️  Masih menggunakan localhost - pastikan untuk update ke production database")
    else:
        print("✅ Menggunakan database non-localhost")
else:
    print("❌ DATABASE_URL tidak terbaca dari .env file")

print("\n🚀 File .env configuration test completed!")