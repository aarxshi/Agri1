"""
Sensor Data Fusion Module
Handles integration and fusion of multiple sensor data sources
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from scipy import interpolate
from scipy.stats import zscore
import logging

logger = logging.getLogger(__name__)

@dataclass
class SensorReading:
    """Data class for individual sensor readings"""
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    location: Optional[Tuple[float, float]] = None
    quality_score: float = 1.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SensorDataFusion:
    """
    Main class for fusing multiple sensor data streams
    """
    
    def __init__(self, field_id: int):
        self.field_id = field_id
        self.sensor_readings: List[SensorReading] = []
        self.fusion_weights: Dict[str, float] = {}
        self.calibration_factors: Dict[str, Dict[str, float]] = {}
        
    def add_reading(self, reading: SensorReading) -> None:
        """Add a new sensor reading"""
        self.sensor_readings.append(reading)
        
    def add_readings(self, readings: List[SensorReading]) -> None:
        """Add multiple sensor readings"""
        self.sensor_readings.extend(readings)
        
    def set_fusion_weights(self, weights: Dict[str, float]) -> None:
        """Set weights for different sensor types in fusion"""
        self.fusion_weights = weights
        
    def set_calibration_factors(self, factors: Dict[str, Dict[str, float]]) -> None:
        """Set calibration factors for sensor types"""
        self.calibration_factors = factors
        
    def clean_data(self, remove_outliers: bool = True, z_threshold: float = 3.0) -> List[SensorReading]:
        """
        Clean sensor data by removing outliers and applying quality filters
        """
        cleaned_readings = []
        
        # Group readings by sensor type
        sensor_groups = {}
        for reading in self.sensor_readings:
            if reading.sensor_type not in sensor_groups:
                sensor_groups[reading.sensor_type] = []
            sensor_groups[reading.sensor_type].append(reading)
        
        for sensor_type, readings in sensor_groups.items():
            if not readings:
                continue
                
            # Apply quality score filter (keep readings with quality >= 0.5)
            quality_filtered = [r for r in readings if r.quality_score >= 0.5]
            
            if remove_outliers and len(quality_filtered) > 3:
                # Remove statistical outliers using z-score
                values = [r.value for r in quality_filtered]
                z_scores = np.abs(zscore(values))
                outlier_filtered = [
                    reading for i, reading in enumerate(quality_filtered)
                    if z_scores[i] < z_threshold
                ]
                cleaned_readings.extend(outlier_filtered)
            else:
                cleaned_readings.extend(quality_filtered)
        
        logger.info(f"Cleaned {len(self.sensor_readings)} readings to {len(cleaned_readings)}")
        return cleaned_readings
    
    def interpolate_missing_data(self, 
                               readings: List[SensorReading], 
                               time_resolution: str = '1H') -> pd.DataFrame:
        """
        Interpolate missing data points using temporal interpolation
        """
        if not readings:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for reading in readings:
            data.append({
                'timestamp': reading.timestamp,
                'sensor_type': reading.sensor_type,
                'value': reading.value,
                'quality_score': reading.quality_score,
                'sensor_id': reading.sensor_id
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Pivot to have sensor types as columns
        pivot_df = df.pivot_table(
            index='timestamp',
            columns='sensor_type',
            values='value',
            aggfunc='mean'  # Average multiple readings at same time
        )
        
        # Create regular time index
        time_range = pd.date_range(
            start=pivot_df.index.min(),
            end=pivot_df.index.max(),
            freq=time_resolution
        )
        
        # Reindex and interpolate
        interpolated_df = pivot_df.reindex(time_range)
        interpolated_df = interpolated_df.interpolate(method='time', limit_direction='both')
        
        return interpolated_df
    
    def apply_calibration(self, readings: List[SensorReading]) -> List[SensorReading]:
        """
        Apply calibration factors to sensor readings
        """
        calibrated_readings = []
        
        for reading in readings:
            calibrated_reading = reading
            
            if reading.sensor_type in self.calibration_factors:
                factors = self.calibration_factors[reading.sensor_type]
                
                # Apply linear calibration: calibrated_value = slope * raw_value + offset
                slope = factors.get('slope', 1.0)
                offset = factors.get('offset', 0.0)
                
                calibrated_value = slope * reading.value + offset
                
                # Create new reading with calibrated value
                calibrated_reading = SensorReading(
                    sensor_id=reading.sensor_id,
                    sensor_type=reading.sensor_type,
                    value=calibrated_value,
                    unit=reading.unit,
                    timestamp=reading.timestamp,
                    location=reading.location,
                    quality_score=reading.quality_score,
                    metadata={**reading.metadata, 'calibrated': True}
                )
            
            calibrated_readings.append(calibrated_reading)
        
        return calibrated_readings
    
    def fuse_spatial_data(self, 
                         readings: List[SensorReading], 
                         grid_size: float = 10.0) -> Dict[str, np.ndarray]:
        """
        Fuse spatially distributed sensor data using spatial interpolation
        """
        if not readings:
            return {}
        
        # Group readings by sensor type
        sensor_groups = {}
        for reading in readings:
            if reading.location is None:
                continue
            if reading.sensor_type not in sensor_groups:
                sensor_groups[reading.sensor_type] = []
            sensor_groups[reading.sensor_type].append(reading)
        
        fused_grids = {}
        
        for sensor_type, type_readings in sensor_groups.items():
            if len(type_readings) < 3:  # Need at least 3 points for interpolation
                continue
            
            # Extract coordinates and values
            lats = [r.location[0] for r in type_readings]
            lons = [r.location[1] for r in type_readings]
            values = [r.value for r in type_readings]
            weights = [r.quality_score for r in type_readings]
            
            # Create interpolation grid
            lat_min, lat_max = min(lats), max(lats)
            lon_min, lon_max = min(lons), max(lons)
            
            # Create grid points
            grid_lats = np.arange(lat_min, lat_max, grid_size / 111000)  # Approximate degrees
            grid_lons = np.arange(lon_min, lon_max, grid_size / 111000)
            
            grid_lat, grid_lon = np.meshgrid(grid_lats, grid_lons)
            
            # Perform weighted spatial interpolation
            try:
                # Use Radial Basis Function interpolation
                from scipy.interpolate import Rbf
                
                rbf = Rbf(lats, lons, values, weights=weights, function='multiquadric')
                grid_values = rbf(grid_lat, grid_lon)
                
                fused_grids[sensor_type] = {
                    'grid_lat': grid_lat,
                    'grid_lon': grid_lon,
                    'values': grid_values,
                    'original_points': len(type_readings)
                }
                
            except Exception as e:
                logger.warning(f"Spatial interpolation failed for {sensor_type}: {e}")
                continue
        
        return fused_grids
    
    def temporal_fusion(self, 
                       readings: List[SensorReading], 
                       window_size: str = '1H') -> Dict[str, pd.Series]:
        """
        Perform temporal fusion using weighted averaging within time windows
        """
        if not readings:
            return {}
        
        # Convert to DataFrame
        df = self._readings_to_dataframe(readings)
        
        # Group by sensor type and apply temporal fusion
        fused_series = {}
        
        for sensor_type in df['sensor_type'].unique():
            sensor_df = df[df['sensor_type'] == sensor_type].copy()
            sensor_df = sensor_df.set_index('timestamp').sort_index()
            
            # Apply weights if available
            weight = self.fusion_weights.get(sensor_type, 1.0)
            
            # Resample using weighted average
            if 'quality_score' in sensor_df.columns:
                # Weighted average by quality score
                weighted_values = sensor_df['value'] * sensor_df['quality_score'] * weight
                weights_sum = sensor_df['quality_score'].resample(window_size).sum()
                fused_values = weighted_values.resample(window_size).sum() / weights_sum
            else:
                # Simple average
                fused_values = sensor_df['value'].resample(window_size).mean() * weight
            
            fused_series[sensor_type] = fused_values.dropna()
        
        return fused_series
    
    def multi_sensor_fusion(self, 
                          readings: List[SensorReading],
                          fusion_method: str = 'weighted_average') -> Dict[str, float]:
        """
        Fuse readings from multiple sensors of the same type
        """
        if not readings:
            return {}
        
        # Group by sensor type
        sensor_groups = {}
        for reading in readings:
            if reading.sensor_type not in sensor_groups:
                sensor_groups[reading.sensor_type] = []
            sensor_groups[reading.sensor_type].append(reading)
        
        fused_values = {}
        
        for sensor_type, type_readings in sensor_groups.items():
            if fusion_method == 'weighted_average':
                # Weighted average by quality score
                numerator = sum(r.value * r.quality_score for r in type_readings)
                denominator = sum(r.quality_score for r in type_readings)
                
                if denominator > 0:
                    fused_values[sensor_type] = numerator / denominator
                else:
                    fused_values[sensor_type] = np.mean([r.value for r in type_readings])
                    
            elif fusion_method == 'kalman_filter':
                # Simple Kalman filter implementation
                fused_values[sensor_type] = self._kalman_filter_fusion(type_readings)
                
            elif fusion_method == 'median':
                # Robust median fusion
                fused_values[sensor_type] = np.median([r.value for r in type_readings])
                
            else:  # Default to simple average
                fused_values[sensor_type] = np.mean([r.value for r in type_readings])
        
        return fused_values
    
    def detect_sensor_anomalies(self, 
                              readings: List[SensorReading],
                              threshold_factor: float = 2.0) -> List[SensorReading]:
        """
        Detect anomalous sensor readings using statistical methods
        """
        anomalies = []
        
        # Group by sensor type
        sensor_groups = {}
        for reading in readings:
            if reading.sensor_type not in sensor_groups:
                sensor_groups[reading.sensor_type] = []
            sensor_groups[reading.sensor_type].append(reading)
        
        for sensor_type, type_readings in sensor_groups.items():
            if len(type_readings) < 5:  # Need sufficient data for anomaly detection
                continue
            
            values = [r.value for r in type_readings]
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            for reading in type_readings:
                # Check if reading is more than threshold_factor standard deviations away
                if abs(reading.value - mean_val) > threshold_factor * std_val:
                    anomalies.append(reading)
        
        return anomalies
    
    def generate_fusion_report(self, 
                             readings: List[SensorReading]) -> Dict[str, any]:
        """
        Generate a comprehensive report on sensor data fusion
        """
        report = {
            'timestamp': datetime.now(),
            'field_id': self.field_id,
            'total_readings': len(readings),
            'sensor_types': {},
            'quality_summary': {},
            'temporal_coverage': {},
            'spatial_coverage': {},
            'anomalies': [],
            'fusion_summary': {}
        }
        
        if not readings:
            return report
        
        # Group by sensor type for analysis
        sensor_groups = {}
        for reading in readings:
            if reading.sensor_type not in sensor_groups:
                sensor_groups[reading.sensor_type] = []
            sensor_groups[reading.sensor_type].append(reading)
        
        # Analyze each sensor type
        for sensor_type, type_readings in sensor_groups.items():
            count = len(type_readings)
            values = [r.value for r in type_readings]
            quality_scores = [r.quality_score for r in type_readings]
            timestamps = [r.timestamp for r in type_readings]
            
            # Basic statistics
            report['sensor_types'][sensor_type] = {
                'count': count,
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'unit': type_readings[0].unit if type_readings else None
            }
            
            # Quality summary
            report['quality_summary'][sensor_type] = {
                'avg_quality': np.mean(quality_scores),
                'min_quality': np.min(quality_scores),
                'high_quality_percentage': len([q for q in quality_scores if q >= 0.8]) / count * 100
            }
            
            # Temporal coverage
            if timestamps:
                time_span = max(timestamps) - min(timestamps)
                report['temporal_coverage'][sensor_type] = {
                    'start_time': min(timestamps),
                    'end_time': max(timestamps),
                    'duration_hours': time_span.total_seconds() / 3600,
                    'reading_frequency_minutes': time_span.total_seconds() / 60 / count if count > 1 else 0
                }
        
        # Detect anomalies
        anomalies = self.detect_sensor_anomalies(readings)
        report['anomalies'] = [
            {
                'sensor_id': a.sensor_id,
                'sensor_type': a.sensor_type,
                'value': a.value,
                'timestamp': a.timestamp
            }
            for a in anomalies
        ]
        
        # Fusion summary
        fused_values = self.multi_sensor_fusion(readings)
        report['fusion_summary'] = fused_values
        
        return report
    
    def _readings_to_dataframe(self, readings: List[SensorReading]) -> pd.DataFrame:
        """Convert sensor readings to pandas DataFrame"""
        data = []
        for reading in readings:
            data.append({
                'timestamp': reading.timestamp,
                'sensor_type': reading.sensor_type,
                'sensor_id': reading.sensor_id,
                'value': reading.value,
                'unit': reading.unit,
                'quality_score': reading.quality_score,
                'location_lat': reading.location[0] if reading.location else None,
                'location_lng': reading.location[1] if reading.location else None
            })
        
        return pd.DataFrame(data)
    
    def _kalman_filter_fusion(self, readings: List[SensorReading]) -> float:
        """
        Simple Kalman filter implementation for sensor fusion
        """
        if not readings:
            return 0.0
        
        # Initialize with first reading
        estimate = readings[0].value
        estimate_error = 1.0
        
        for reading in readings[1:]:
            # Prediction step (assume no process noise for simplicity)
            predicted_estimate = estimate
            predicted_error = estimate_error + 0.1  # Small process noise
            
            # Update step
            measurement_noise = 1.0 / reading.quality_score  # Higher quality = lower noise
            kalman_gain = predicted_error / (predicted_error + measurement_noise)
            
            estimate = predicted_estimate + kalman_gain * (reading.value - predicted_estimate)
            estimate_error = (1 - kalman_gain) * predicted_error
        
        return estimate


class RealTimeFusion:
    """
    Real-time sensor data fusion for streaming data
    """
    
    def __init__(self, field_id: int, buffer_size: int = 1000):
        self.field_id = field_id
        self.buffer_size = buffer_size
        self.reading_buffer: Dict[str, List[SensorReading]] = {}
        self.fusion_engine = SensorDataFusion(field_id)
        
    def add_streaming_reading(self, reading: SensorReading) -> Dict[str, float]:
        """
        Add a new streaming reading and return fused values
        """
        # Add to buffer
        if reading.sensor_type not in self.reading_buffer:
            self.reading_buffer[reading.sensor_type] = []
        
        self.reading_buffer[reading.sensor_type].append(reading)
        
        # Maintain buffer size
        if len(self.reading_buffer[reading.sensor_type]) > self.buffer_size:
            self.reading_buffer[reading.sensor_type].pop(0)
        
        # Get recent readings for fusion
        recent_readings = []
        current_time = datetime.now()
        time_window = timedelta(hours=1)  # Consider last hour of data
        
        for sensor_type, readings in self.reading_buffer.items():
            recent_readings.extend([
                r for r in readings 
                if (current_time - r.timestamp) <= time_window
            ])
        
        # Perform real-time fusion
        if recent_readings:
            return self.fusion_engine.multi_sensor_fusion(recent_readings)
        else:
            return {}
    
    def get_buffer_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of reading buffers"""
        status = {}
        
        for sensor_type, readings in self.reading_buffer.items():
            if readings:
                latest_reading = max(readings, key=lambda x: x.timestamp)
                status[sensor_type] = {
                    'buffer_size': len(readings),
                    'latest_timestamp': latest_reading.timestamp,
                    'latest_value': latest_reading.value,
                    'avg_quality': np.mean([r.quality_score for r in readings])
                }
        
        return status
