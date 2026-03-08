"""
University Gown Management System - Configuration
"""

import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Caching Configuration
    CACHE_TYPE = 'simple'  # Use SimpleCache for low CPU (use 'redis' for production)
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default cache
    CACHE_THRESHOLD = 500  # Max cached items
    
    # Performance
    JSON_SORT_KEYS = False  # Faster JSON serialization
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    
    # SQLite for development
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    
    # Create instance folder if it doesn't exist
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(instance_path, 'university_gowns.db')
    SQLALCHEMY_INSTANCE_PATH = instance_path
    
    # Development settings
    WTF_CSRF_ENABLED = False  # Disable for easier testing
    
    # Disable caching in development for easier debugging
    CACHE_TYPE = 'null'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    
    # SQLite with optimized settings for production (use MySQL/PostgreSQL for scale)
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(instance_path, 'university_gowns.db')
    
    # Production security
    SESSION_COOKIE_SECURE = True
    
    # Redis caching for production (if available)
    # CACHE_TYPE = 'redis'
    # CACHE_REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    # CACHE_REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # In-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    WTF_CSRF_ENABLED = False
    
    # Disable caching in tests
    CACHE_TYPE = 'null'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
