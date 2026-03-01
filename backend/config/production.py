"""Production configuration for Flask app"""
import os
from dotenv import load_dotenv

load_dotenv('.env.production')

class ProductionConfig:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    DEBUG = False
    TESTING = False
    
    # CORS Configuration
    CORS_ORIGINS = [
        'https://your-domain.com',
        'https://www.your-domain.com'
    ]
    
    # Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/app/logs/production.log'
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Chrome/Selenium Configuration for Production
    CHROME_OPTIONS = [
        '--no-sandbox',
        '--headless',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080'
    ]