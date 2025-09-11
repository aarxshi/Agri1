"""
Agriculture Monitoring Platform - Database Models
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random

# This will be imported from the app
db = None

def init_db_models(database):
    """Initialize database models with the db instance"""
    global db
    db = database


class User(db.Model):
    """User authentication model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='farmer')
    farm_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fields = db.relationship('Field', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'farm_name': self.farm_name,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class Field(db.Model):
    """Field/Farm boundary model"""
    __tablename__ = 'fields'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    area_hectares = db.Column(db.Float, nullable=False)
    crop_type = db.Column(db.String(50), nullable=False)
    location_coordinates = db.Column(db.Text)  # JSON string of polygon coordinates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sensor_data = db.relationship('SensorData', backref='field', lazy=True)
    crop_images = db.relationship('CropImage', backref='field', lazy=True)
    predictions = db.relationship('CropPrediction', backref='field', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'area_hectares': self.area_hectares,
            'crop_type': self.crop_type,
            'location_coordinates': json.loads(self.location_coordinates) if self.location_coordinates else None,
            'created_at': self.created_at.isoformat()
        }


class SensorData(db.Model):
    """Sensor data readings model"""
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)  # soil_moisture, temperature, humidity, etc.
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    device_id = db.Column(db.String(100))
    quality_score = db.Column(db.Float, default=1.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'field_id': self.field_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'location_lat': self.location_lat,
            'location_lng': self.location_lng,
            'device_id': self.device_id,
            'quality_score': self.quality_score,
            'timestamp': self.timestamp.isoformat()
        }


class CropImage(db.Model):
    """Crop image analysis model"""
    __tablename__ = 'crop_images'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    image_type = db.Column(db.String(50), default='RGB')  # RGB, hyperspectral, etc.
    analysis_results = db.Column(db.Text)  # JSON string of analysis results
    ndvi = db.Column(db.Float)
    savi = db.Column(db.Float)
    evi = db.Column(db.Float)
    mcari = db.Column(db.Float)
    red_edge_position = db.Column(db.Float)
    processed = db.Column(db.Boolean, default=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'field_id': self.field_id,
            'filename': self.filename,
            'image_type': self.image_type,
            'analysis_results': json.loads(self.analysis_results) if self.analysis_results else None,
            'ndvi': self.ndvi,
            'savi': self.savi,
            'evi': self.evi,
            'mcari': self.mcari,
            'red_edge_position': self.red_edge_position,
            'processed': self.processed,
            'upload_time': self.upload_time.isoformat()
        }


class CropPrediction(db.Model):
    """AI-powered crop predictions model"""
    __tablename__ = 'crop_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False)  # health, pest, disease, yield
    confidence = db.Column(db.Float, nullable=False)
    result = db.Column(db.Text, nullable=False)  # JSON string of prediction results
    risk_level = db.Column(db.String(20))  # low, medium, high
    recommendations = db.Column(db.Text)  # JSON string of recommendations
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'field_id': self.field_id,
            'prediction_type': self.prediction_type,
            'confidence': self.confidence,
            'result': json.loads(self.result) if self.result else None,
            'risk_level': self.risk_level,
            'recommendations': json.loads(self.recommendations) if self.recommendations else None,
            'created_at': self.created_at.isoformat()
        }


class WeatherData(db.Model):
    """Weather information model"""
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    pressure = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'field_id': self.field_id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'precipitation': self.precipitation,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'pressure': self.pressure,
            'uv_index': self.uv_index,
            'timestamp': self.timestamp.isoformat()
        }


def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create default user
    if not User.query.first():
        default_user = User(
            username='farmer',
            email='farmer@agrimonitor.com',
            role='farmer',
            farm_name='Demo Farm',
            location='New York, USA'
        )
        default_user.set_password('password123')
        db.session.add(default_user)
        db.session.commit()
        
        # Create sample field
        sample_field = Field(
            user_id=default_user.id,
            name="North Field - Corn",
            area_hectares=25.5,
            crop_type="Corn",
            location_coordinates=json.dumps([
                [-74.0060, 40.7128],
                [-74.0050, 40.7128],
                [-74.0050, 40.7138],
                [-74.0060, 40.7138],
                [-74.0060, 40.7128]
            ])
        )
        db.session.add(sample_field)
        db.session.commit()
        
        # Generate sample sensor data
        field_id = sample_field.id
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i in range(168):  # 7 days of hourly data
            timestamp = base_time + timedelta(hours=i)
            
            # Soil moisture data
            soil_moisture = SensorData(
                field_id=field_id,
                sensor_type='soil_moisture',
                value=round(random.uniform(15, 35), 1),
                unit='%',
                location_lat=40.7128 + random.uniform(-0.001, 0.001),
                location_lng=-74.0055 + random.uniform(-0.001, 0.001),
                device_id=f'soil_sensor_{i % 3 + 1}',
                timestamp=timestamp
            )
            db.session.add(soil_moisture)
            
            # Temperature data
            temperature = SensorData(
                field_id=field_id,
                sensor_type='air_temperature',
                value=round(random.uniform(18, 32), 1),
                unit='°C',
                location_lat=40.7128 + random.uniform(-0.001, 0.001),
                location_lng=-74.0055 + random.uniform(-0.001, 0.001),
                device_id=f'temp_sensor_{i % 2 + 1}',
                timestamp=timestamp
            )
            db.session.add(temperature)
            
            # Humidity data
            humidity = SensorData(
                field_id=field_id,
                sensor_type='humidity',
                value=round(random.uniform(45, 85), 1),
                unit='%',
                location_lat=40.7128 + random.uniform(-0.001, 0.001),
                location_lng=-74.0055 + random.uniform(-0.001, 0.001),
                device_id=f'humidity_sensor_{i % 2 + 1}',
                timestamp=timestamp
            )
            db.session.add(humidity)
        
        # Create sample predictions
        health_prediction = CropPrediction(
            field_id=field_id,
            prediction_type='health',
            confidence=0.89,
            result=json.dumps({
                'status': 'Good',
                'ndvi': 0.78,
                'vegetation_coverage': '85%',
                'stress_indicators': 'Low'
            }),
            risk_level='low',
            recommendations=json.dumps([
                'Continue current irrigation schedule',
                'Monitor for early pest signs',
                'Consider nitrogen supplementation in 2 weeks'
            ])
        )
        db.session.add(health_prediction)
        
        pest_prediction = CropPrediction(
            field_id=field_id,
            prediction_type='pest',
            confidence=0.76,
            result=json.dumps({
                'pest_risk': 'High',
                'detected_pests': ['Corn Borer', 'Aphids'],
                'affected_area': '12%'
            }),
            risk_level='high',
            recommendations=json.dumps([
                'Apply targeted pesticide treatment',
                'Increase monitoring frequency',
                'Consider biological control methods'
            ])
        )
        db.session.add(pest_prediction)
        
        db.session.commit()

"""
Database Models for Agriculture Monitoring Platform
"""

from backend.app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='farmer')  # farmer, admin, technician
    farm_name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    fields = db.relationship('Field', backref='owner', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

class Field(db.Model):
    """Field model for farm field management"""
    __tablename__ = 'fields'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    area_hectares = db.Column(db.Float)
    crop_type = db.Column(db.String(50))
    planting_date = db.Column(db.Date)
    coordinates = db.Column(JSON)  # GeoJSON polygon
    soil_type = db.Column(db.String(50))
    irrigation_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sensor_data = db.relationship('SensorData', backref='field', lazy=True, cascade='all, delete-orphan')
    hyperspectral_images = db.relationship('HyperspectralImage', backref='field', lazy=True, cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='field', lazy=True, cascade='all, delete-orphan')

class SensorData(db.Model):
    """Sensor data model for environmental measurements"""
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)  # soil_moisture, temperature, humidity, etc.
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    device_id = db.Column(db.String(100))
    quality_score = db.Column(db.Float, default=1.0)  # Data quality indicator
    
    # Index for time-series queries
    __table_args__ = (
        db.Index('idx_sensor_data_timestamp', 'timestamp'),
        db.Index('idx_sensor_data_field_type', 'field_id', 'sensor_type'),
    )

class HyperspectralImage(db.Model):
    """Hyperspectral image data model"""
    __tablename__ = 'hyperspectral_images'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    capture_date = db.Column(db.DateTime, nullable=False)
    drone_id = db.Column(db.String(100))
    flight_altitude = db.Column(db.Float)
    weather_conditions = db.Column(JSON)
    spectral_bands = db.Column(db.Integer)
    spatial_resolution = db.Column(db.Float)  # meters per pixel
    coverage_area = db.Column(JSON)  # GeoJSON polygon
    processing_status = db.Column(db.String(20), default='pending')  # pending, processed, failed
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    spectral_indices = db.relationship('SpectralIndex', backref='image', lazy=True, cascade='all, delete-orphan')

class SpectralIndex(db.Model):
    """Calculated spectral indices from hyperspectral images"""
    __tablename__ = 'spectral_indices'
    
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('hyperspectral_images.id'), nullable=False)
    index_type = db.Column(db.String(20), nullable=False)  # NDVI, SAVI, EVI, etc.
    mean_value = db.Column(db.Float)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    std_value = db.Column(db.Float)
    histogram_data = db.Column(JSON)  # Histogram bins and counts
    spatial_map_path = db.Column(db.String(500))  # Path to spatial index map
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prediction(db.Model):
    """AI model predictions for crop health and pest risks"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False)  # stress, disease, pest, yield
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(20))
    confidence_score = db.Column(db.Float)
    prediction_value = db.Column(JSON)  # Flexible storage for different prediction types
    input_features = db.Column(JSON)  # Features used for prediction
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    # Relationships
    alerts = db.relationship('Alert', backref='prediction', lazy=True)

class Alert(db.Model):
    """Alert system for notifications"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'))
    alert_type = db.Column(db.String(50), nullable=False)  # stress, disease, pest, irrigation
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    notification_sent = db.Column(db.Boolean, default=False)

class Report(db.Model):
    """Generated reports model"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # field_summary, pest_analysis, etc.
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500))
    file_format = db.Column(db.String(10))  # pdf, csv, xlsx
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    parameters = db.Column(JSON)  # Report generation parameters
    status = db.Column(db.String(20), default='generating')  # generating, completed, failed

class SystemConfiguration(db.Model):
    """System configuration and settings"""
    __tablename__ = 'system_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(JSON)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

# Create all tables
def init_db():
    """Initialize database with tables"""
    db.create_all()
    
def seed_data():
    """Seed initial data"""
    # Create default admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@agrimonitor.com',
            role='admin',
            farm_name='System Admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created")
