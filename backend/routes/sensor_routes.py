"""
Sensor Data API Routes
Handles environmental sensor data collection and retrieval
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.agriculture_models import SensorData, Field
from backend.app import db
from datetime import datetime, timedelta
import json

sensor_bp = Blueprint('sensors', __name__)

@sensor_bp.route('/data', methods=['POST'])
@jwt_required()
def add_sensor_data():
    """Add new sensor data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['field_id', 'sensor_type', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify field ownership
        field = Field.query.get(data['field_id'])
        if not field:
            return jsonify({'error': 'Field not found'}), 404
        
        current_user_id = get_jwt_identity()
        if field.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized access to field'}), 403
        
        # Create sensor data record
        sensor_data = SensorData(
            field_id=data['field_id'],
            sensor_type=data['sensor_type'],
            value=float(data['value']),
            unit=data.get('unit'),
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
            device_id=data.get('device_id'),
            quality_score=data.get('quality_score', 1.0),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.utcnow()
        )
        
        db.session.add(sensor_data)
        db.session.commit()
        
        return jsonify({
            'message': 'Sensor data added successfully',
            'data': {
                'id': sensor_data.id,
                'sensor_type': sensor_data.sensor_type,
                'value': sensor_data.value,
                'timestamp': sensor_data.timestamp.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/data/<int:field_id>', methods=['GET'])
@jwt_required()
def get_sensor_data(field_id):
    """Get sensor data for a specific field"""
    try:
        # Verify field ownership
        field = Field.query.get(field_id)
        if not field:
            return jsonify({'error': 'Field not found'}), 404
        
        current_user_id = get_jwt_identity()
        if field.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized access to field'}), 403
        
        # Parse query parameters
        sensor_type = request.args.get('sensor_type')
        hours = int(request.args.get('hours', 24))  # Default to last 24 hours
        limit = int(request.args.get('limit', 100))  # Default limit of 100 records
        
        # Build query
        query = SensorData.query.filter_by(field_id=field_id)
        
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        
        # Filter by time range
        if hours > 0:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(SensorData.timestamp >= start_time)
        
        # Order by timestamp (most recent first) and limit results
        sensor_data = query.order_by(SensorData.timestamp.desc()).limit(limit).all()
        
        # Format response
        data = []
        for record in sensor_data:
            data.append({
                'id': record.id,
                'sensor_type': record.sensor_type,
                'value': record.value,
                'unit': record.unit,
                'location_lat': record.location_lat,
                'location_lng': record.location_lng,
                'timestamp': record.timestamp.isoformat(),
                'device_id': record.device_id,
                'quality_score': record.quality_score
            })
        
        return jsonify({
            'field_id': field_id,
            'field_name': field.name,
            'data': data,
            'count': len(data),
            'filters': {
                'sensor_type': sensor_type,
                'hours': hours,
                'limit': limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/statistics/<int:field_id>', methods=['GET'])
@jwt_required()
def get_sensor_statistics(field_id):
    """Get statistical summary of sensor data"""
    try:
        # Verify field ownership
        field = Field.query.get(field_id)
        if not field:
            return jsonify({'error': 'Field not found'}), 404
        
        current_user_id = get_jwt_identity()
        if field.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized access to field'}), 403
        
        # Parse query parameters
        sensor_type = request.args.get('sensor_type')
        hours = int(request.args.get('hours', 24))
        
        # Build base query
        query = SensorData.query.filter_by(field_id=field_id)
        
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        
        if hours > 0:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(SensorData.timestamp >= start_time)
        
        # Calculate statistics
        from sqlalchemy import func
        stats = db.session.query(
            SensorData.sensor_type,
            func.avg(SensorData.value).label('avg_value'),
            func.min(SensorData.value).label('min_value'),
            func.max(SensorData.value).label('max_value'),
            func.count(SensorData.id).label('count'),
            func.max(SensorData.timestamp).label('last_reading')
        ).filter_by(field_id=field_id)
        
        if sensor_type:
            stats = stats.filter_by(sensor_type=sensor_type)
            
        if hours > 0:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            stats = stats.filter(SensorData.timestamp >= start_time)
        
        stats = stats.group_by(SensorData.sensor_type).all()
        
        # Format response
        statistics = []
        for stat in stats:
            statistics.append({
                'sensor_type': stat.sensor_type,
                'average': round(float(stat.avg_value), 2) if stat.avg_value else None,
                'minimum': float(stat.min_value) if stat.min_value else None,
                'maximum': float(stat.max_value) if stat.max_value else None,
                'count': stat.count,
                'last_reading': stat.last_reading.isoformat() if stat.last_reading else None
            })
        
        return jsonify({
            'field_id': field_id,
            'field_name': field.name,
            'statistics': statistics,
            'time_range_hours': hours
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/types', methods=['GET'])
@jwt_required()
def get_sensor_types():
    """Get available sensor types"""
    sensor_types = [
        {'type': 'soil_moisture', 'description': 'Soil Moisture Content (%)', 'unit': '%'},
        {'type': 'soil_temperature', 'description': 'Soil Temperature', 'unit': '°C'},
        {'type': 'air_temperature', 'description': 'Air Temperature', 'unit': '°C'},
        {'type': 'humidity', 'description': 'Relative Humidity', 'unit': '%'},
        {'type': 'leaf_wetness', 'description': 'Leaf Wetness Duration', 'unit': 'hours'},
        {'type': 'light_intensity', 'description': 'Light Intensity', 'unit': 'lux'},
        {'type': 'wind_speed', 'description': 'Wind Speed', 'unit': 'm/s'},
        {'type': 'rainfall', 'description': 'Rainfall', 'unit': 'mm'},
        {'type': 'ph', 'description': 'Soil pH Level', 'unit': 'pH'},
        {'type': 'ec', 'description': 'Electrical Conductivity', 'unit': 'dS/m'}
    ]
    
    return jsonify({'sensor_types': sensor_types}), 200
