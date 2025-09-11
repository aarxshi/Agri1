"""
Flask Application Configuration
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://agri_monitor:password@localhost/agriculture_monitoring'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'tiff', 'tif', 'hdr', 'bil', 'bsq', 'bip'},
        'data': {'csv', 'xlsx', 'json', 'txt'},
        'models': {'h5', 'pkl', 'joblib', 'mat'}
    }
    
    # CORS Configuration
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Mail Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@agrimonitor.com'
    
    # Redis Configuration (for Celery background tasks)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # API Keys and External Services
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
    WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5'
    
    # Firebase Configuration (for push notifications)
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    
    # MATLAB Engine Configuration
    MATLAB_ENGINE_ENABLED = os.environ.get('MATLAB_ENGINE_ENABLED', 'false').lower() == 'true'
    MATLAB_SCRIPTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'matlab-processing')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    
    # Hyperspectral Image Processing
    HYPERSPECTRAL_PROCESSING_PATH = os.path.join(UPLOAD_FOLDER, 'hyperspectral')
    SPECTRAL_INDICES_OUTPUT_PATH = os.path.join(UPLOAD_FOLDER, 'spectral_indices')
    
    # Model Storage Paths
    AI_MODELS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    TRAINED_MODELS_PATH = os.path.join(AI_MODELS_PATH, 'trained')
    MODEL_CACHE_PATH = os.path.join(AI_MODELS_PATH, 'cache')
    
    # Report Generation
    REPORTS_OUTPUT_PATH = os.path.join(UPLOAD_FOLDER, 'reports')
    TEMP_FILES_PATH = os.path.join(UPLOAD_FOLDER, 'temp')
    
    # Geospatial Configuration
    DEFAULT_COORDINATE_SYSTEM = 'EPSG:4326'  # WGS84
    GEOSPATIAL_BUFFER_METERS = 100  # Default buffer for spatial queries
    
    # Caching Configuration
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create upload directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.HYPERSPECTRAL_PROCESSING_PATH, exist_ok=True)
        os.makedirs(Config.SPECTRAL_INDICES_OUTPUT_PATH, exist_ok=True)
        os.makedirs(Config.AI_MODELS_PATH, exist_ok=True)
        os.makedirs(Config.TRAINED_MODELS_PATH, exist_ok=True)
        os.makedirs(Config.MODEL_CACHE_PATH, exist_ok=True)
        os.makedirs(Config.REPORTS_OUTPUT_PATH, exist_ok=True)
        os.makedirs(Config.TEMP_FILES_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Disable HTTPS requirements in development
    SESSION_COOKIE_SECURE = False
    
    # Less restrictive CORS in development
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]
    
    # Development database (can be SQLite for quick setup)
    if not Config.DATABASE_URL:
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agriculture_platform.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    # Enable all features in development
    MATLAB_ENGINE_ENABLED = True
    
    # Shorter token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = False
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False
    
    # Short token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # Disable external API calls in testing
    WEATHER_API_KEY = 'test-key'
    MATLAB_ENGINE_ENABLED = False
    
    # Use test paths
    UPLOAD_FOLDER = '/tmp/agri_test_uploads'
    LOG_FILE = '/tmp/agri_test.log'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Strict security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True
    
    # Enhanced database connection pooling for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 30,
        'pool_timeout': 30
    }
    
    # Production logging configuration
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production database must be provided
        if not Config.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required in production")
        
        # Require all API keys in production
        required_env_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'WEATHER_API_KEY'
        ]
        
        for var in required_env_vars:
            if not os.environ.get(var):
                raise ValueError(f"{var} environment variable is required in production")
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set up file logging with rotation
        file_handler = RotatingFileHandler(
            cls.LOG_FILE, 
            maxBytes=10000000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.WARNING)
        app.logger.info('Agriculture Monitoring Platform startup')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
