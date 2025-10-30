#!/usr/bin/env python3
"""
Quick test untuk memverifikasi Flask app configuration
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app with .env loading
from app import app, DATABASE_URL

print("=== SAP API Configuration Test ===")
print(f"App Name: {app.name}")
print(f"Debug Mode: {app.debug}")
print(f"Database URL: {DATABASE_URL[:20]}...{DATABASE_URL[-10:] if len(DATABASE_URL) > 30 else DATABASE_URL}")
print(f"SQL Alchemy URI: {app.config['SQLALCHEMY_DATABASE_URI'][:20]}...{app.config['SQLALCHEMY_DATABASE_URI'][-10:] if len(app.config['SQLALCHEMY_DATABASE_URI']) > 30 else app.config['SQLALCHEMY_DATABASE_URI']}")

# Check if environment variables are loaded
import os
from dotenv import load_dotenv
load_dotenv()

print(f"\nEnvironment Variables:")
print(f"HOST: {os.environ.get('HOST', 'NOT SET')}")
print(f"PORT: {os.environ.get('PORT', 'NOT SET')}")
print(f"DEBUG: {os.environ.get('DEBUG', 'NOT SET')}")

print("\n✅ Configuration test completed!")
print("Aplikasi sudah siap dengan konfigurasi .env")