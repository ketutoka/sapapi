#!/usr/bin/env python3
"""
Script untuk menjalankan aplikasi SAP API
"""
import os
import sys
from app import app

if __name__ == '__main__':
    # Set environment
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"Starting SAP API server on {host}:{port}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=app.config.get('DEBUG', False)
    )