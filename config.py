import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # Database configuration
    # Default menggunakan SQLite untuk development
    # Untuk production, ganti dengan database yang sesuai (PostgreSQL, MySQL, SQL Server, etc.)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///sapapi.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # API Configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Pagination
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Pastikan menggunakan SQLite untuk development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sapapi_dev.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Contoh untuk PostgreSQL
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/sapapi'
    
    # Contoh untuk SQL Server
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}