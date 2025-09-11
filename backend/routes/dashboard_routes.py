"""
Dashboard API Routes
Provides data for the main dashboard interface
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.agriculture_models import Field, SensorData, CropPrediction, CropImage, init_db
from backend.app import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """Get overall dashboard summary (accessible without auth for demo)"""
    try:
        # Get the first field (demo field)
        field = Field.query.first()
        if not field:
            return jsonify({'error': 'No fields found'}), 404
            
        # Get latest sensor readings
        latest_soil_moisture = SensorData.query.filter_by(
            field_id=field.id, 
            sensor_type='soil_moisture'
        ).order_by(desc(SensorData.timestamp)).first()
        
        latest_temperature = SensorData.query.filter_by(
            field_id=field.id, 
            sensor_type='air_temperature'
        ).order_by(desc(SensorData.timestamp)).first()
        
        latest_humidity = SensorData.query.filter_by(
            field_id=field.id, 
            sensor_type='humidity'
        ).order_by(desc(SensorData.timestamp)).first()
        
        # Get latest predictions
        health_prediction = CropPrediction.query.filter_by(
            field_id=field.id, 
            prediction_type='health'
        ).order_by(desc(CropPrediction.created_at)).first()
        
        pest_prediction = CropPrediction.query.filter_by(
            field_id=field.id, 
            prediction_type='pest'
        ).order_by(desc(CropPrediction.created_at)).first()
        
        # Calculate irrigation advice
        soil_moisture_value = latest_soil_moisture.value if latest_soil_moisture else 25.0
        if soil_moisture_value < 20:
            irrigation_advice = "Water Now"
            irrigation_status = "urgent"
        elif soil_moisture_value < 30:
            irrigation_advice = "Schedule Soon" 
            irrigation_status = "warning"
        else:
            irrigation_advice = "Optimal"
            irrigation_status = "good"
            
        # Determine weather-based irrigation delay
        if latest_humidity and latest_humidity.value > 80:
            irrigation_advice = "Delay - High Humidity"
            irrigation_status = "delayed"
        
        return jsonify({
            'field_info': {
                'id': field.id,
                'name': field.name,
                'crop_type': field.crop_type,
                'area_hectares': field.area_hectares
            },
            'crop_health': {
                'status': json.loads(health_prediction.result)['status'] if health_prediction and health_prediction.result else 'Good',
                'ndvi': json.loads(health_prediction.result).get('ndvi', 0.78) if health_prediction and health_prediction.result else 0.78,
                'confidence': health_prediction.confidence if health_prediction else 0.89
            },
            'soil_moisture': {
                'value': soil_moisture_value,
                'unit': '%',
                'status': 'optimal' if soil_moisture_value > 25 else 'low',
                'last_updated': latest_soil_moisture.timestamp.isoformat() if latest_soil_moisture else datetime.utcnow().isoformat()
            },
            'pest_risk': {
                'level': pest_prediction.risk_level if pest_prediction else 'high',
                'confidence': pest_prediction.confidence if pest_prediction else 0.76,
                'detected_pests': json.loads(pest_prediction.result).get('detected_pests', []) if pest_prediction and pest_prediction.result else ['Corn Borer', 'Aphids']
            },
            'irrigation_advice': {
                'recommendation': irrigation_advice,
                'status': irrigation_status,
                'reason': f"Soil moisture at {soil_moisture_value}%"
            },
            'weather': {
                'temperature': latest_temperature.value if latest_temperature else 24.5,
                'humidity': latest_humidity.value if latest_humidity else 65.2,
                'last_updated': latest_temperature.timestamp.isoformat() if latest_temperature else datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/summary/<int:field_id>', methods=['GET'])
@jwt_required()
def get_field_summary(field_id):
    """Get field summary for dashboard"""
    try:
        user_id = get_jwt_identity()
        field = Field.query.filter_by(id=field_id, user_id=user_id).first()
        
        if not field:
            return jsonify({'error': 'Field not found or access denied'}), 404
            
        # Get recent sensor data (last 24 hours)
        recent_data = SensorData.query.filter(
            SensorData.field_id == field_id,
            SensorData.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        # Get latest predictions
        predictions = CropPrediction.query.filter_by(field_id=field_id).order_by(
            desc(CropPrediction.created_at)
        ).limit(5).all()
        
        return jsonify({
            'field': field.to_dict(),
            'recent_sensor_data': [data.to_dict() for data in recent_data],
            'predictions': [pred.to_dict() for pred in predictions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/alerts', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts for dashboard (demo accessible)"""
    try:
        # Generate dynamic alerts based on sensor data and predictions
        field = Field.query.first()
        if not field:
            return jsonify({'alerts': []}), 200
            
        alerts = []
        
        # Check soil moisture
        latest_soil = SensorData.query.filter_by(
            field_id=field.id, 
            sensor_type='soil_moisture'
        ).order_by(desc(SensorData.timestamp)).first()
        
        if latest_soil and latest_soil.value < 20:
            alerts.append({
                'id': 1,
                'type': 'irrigation',
                'level': 'urgent',
                'title': 'Low Soil Moisture Detected',
                'message': f'Soil moisture is at {latest_soil.value}%. Immediate irrigation recommended.',
                'timestamp': latest_soil.timestamp.isoformat(),
                'field_id': field.id,
                'field_name': field.name
            })
        
        # Check pest predictions
        pest_pred = CropPrediction.query.filter_by(
            field_id=field.id, 
            prediction_type='pest'
        ).order_by(desc(CropPrediction.created_at)).first()
        
        if pest_pred and pest_pred.risk_level == 'high':
            alerts.append({
                'id': 2,
                'type': 'pest',
                'level': 'warning',
                'title': 'High Pest Risk Detected',
                'message': f'Pest detection model shows {pest_pred.confidence*100:.0f}% confidence of pest presence.',
                'timestamp': pest_pred.created_at.isoformat(),
                'field_id': field.id,
                'field_name': field.name
            })
        
        # Check temperature extremes
        latest_temp = SensorData.query.filter_by(
            field_id=field.id, 
            sensor_type='air_temperature'
        ).order_by(desc(SensorData.timestamp)).first()
        
        if latest_temp and latest_temp.value > 35:
            alerts.append({
                'id': 3,
                'type': 'weather',
                'level': 'warning',
                'title': 'High Temperature Alert',
                'message': f'Temperature reached {latest_temp.value}°C. Monitor crop stress indicators.',
                'timestamp': latest_temp.timestamp.isoformat(),
                'field_id': field.id,
                'field_name': field.name
            })
        
        return jsonify({'alerts': alerts}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/trends/<int:field_id>', methods=['GET'])
@jwt_required()
def get_trend_data(field_id):
    """Get trend data for charts"""
    try:
        user_id = get_jwt_identity()
        field = Field.query.filter_by(id=field_id, user_id=user_id).first()
        
        if not field:
            return jsonify({'error': 'Field not found or access denied'}), 404
        
        # Get sensor data for the last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)
        sensor_data = SensorData.query.filter(
            SensorData.field_id == field_id,
            SensorData.timestamp >= start_date
        ).order_by(SensorData.timestamp).all()
        
        # Organize data by sensor type
        trends = {}
        for data_point in sensor_data:
            sensor_type = data_point.sensor_type
            if sensor_type not in trends:
                trends[sensor_type] = []
            
            trends[sensor_type].append({
                'timestamp': data_point.timestamp.isoformat(),
                'value': data_point.value,
                'unit': data_point.unit
            })
        
        return jsonify({
            'field_id': field_id,
            'trends': trends
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/trends', methods=['GET'])
def get_demo_trends():
    """Get demo trend data for charts (public access)"""
    try:
        field = Field.query.first()
        if not field:
            return jsonify({'trends': {}}), 200
        
        # Get sensor data for the last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)
        sensor_data = SensorData.query.filter(
            SensorData.field_id == field.id,
            SensorData.timestamp >= start_date
        ).order_by(SensorData.timestamp).all()
        
        # Organize data by sensor type
        trends = {}
        for data_point in sensor_data:
            sensor_type = data_point.sensor_type
            if sensor_type not in trends:
                trends[sensor_type] = []
            
            trends[sensor_type].append({
                'timestamp': data_point.timestamp.isoformat(),
                'value': data_point.value,
                'unit': data_point.unit
            })
        
        return jsonify({
            'field_id': field.id,
            'trends': trends
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
