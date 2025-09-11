/**
 * FieldMap Component
 * Interactive Leaflet map showing field boundaries and sensor data
 */

import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { DashboardSummary } from '../services/api';

// Fix Leaflet default markers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface FieldMapProps {
  summary?: DashboardSummary | null;
  className?: string;
}

// Sample field boundary coordinates (you can replace with real data)
const SAMPLE_FIELD_COORDINATES: [number, number][] = [
  [40.7128, -74.0060],
  [40.7138, -74.0050],
  [40.7148, -74.0070],
  [40.7138, -74.0080],
  [40.7128, -74.0060]
];

// Sample sensor locations
const SAMPLE_SENSORS = [
  { id: 1, position: [40.7133, -74.0065] as [number, number], type: 'soil_moisture', value: 29.7, status: 'optimal' },
  { id: 2, position: [40.7143, -74.0055] as [number, number], type: 'temperature', value: 22.0, status: 'good' },
  { id: 3, position: [40.7138, -74.0075] as [number, number], type: 'ph', value: 6.8, status: 'optimal' },
];

// Component to fit map bounds
const FitBounds: React.FC<{ bounds: [number, number][] }> = ({ bounds }) => {
  const map = useMap();
  
  React.useEffect(() => {
    if (bounds.length > 0) {
      const latLngs = bounds.map(coord => [coord[0], coord[1]] as [number, number]);
      const leafletBounds = L.latLngBounds(latLngs);
      map.fitBounds(leafletBounds.pad(0.1));
    }
  }, [map, bounds]);
  
  return null;
};

export const FieldMap: React.FC<FieldMapProps> = ({ summary, className = '' }) => {
  // Calculate field center
  const fieldCenter = useMemo(() => {
    const latSum = SAMPLE_FIELD_COORDINATES.reduce((sum, coord) => sum + coord[0], 0);
    const lngSum = SAMPLE_FIELD_COORDINATES.reduce((sum, coord) => sum + coord[1], 0);
    return [
      latSum / SAMPLE_FIELD_COORDINATES.length,
      lngSum / SAMPLE_FIELD_COORDINATES.length
    ] as [number, number];
  }, []);

  // Determine field color based on health status
  const getFieldColor = () => {
    if (!summary) return '#22c55e'; // default green
    
    const status = summary.crop_health.status.toLowerCase();
    switch (status) {
      case 'poor':
      case 'critical':
        return '#ef4444'; // red
      case 'fair':
      case 'warning':
        return '#fbbf24'; // yellow
      case 'good':
      case 'excellent':
      default:
        return '#22c55e'; // green
    }
  };

  // Get sensor marker color based on status
  const getSensorColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'critical':
      case 'poor':
        return '#ef4444'; // red
      case 'warning':
      case 'fair':
        return '#fbbf24'; // yellow
      case 'optimal':
      case 'good':
      default:
        return '#22c55e'; // green
    }
  };

  return (
    <div className={`relative ${className}`}>
      <MapContainer
        center={fieldCenter}
        zoom={16}
        style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <FitBounds bounds={SAMPLE_FIELD_COORDINATES} />
        
        {/* Field boundary */}
        <Polygon
          positions={SAMPLE_FIELD_COORDINATES}
          pathOptions={{
            color: getFieldColor(),
            weight: 3,
            opacity: 0.8,
            fillColor: getFieldColor(),
            fillOpacity: 0.2,
          }}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-semibold text-lg">
                {summary?.field_info.name || 'Sample Field'}
              </h3>
              <p className="text-sm text-gray-600">
                Crop: {summary?.field_info.crop_type || 'Corn'}
              </p>
              <p className="text-sm text-gray-600">
                Area: {summary?.field_info.area_hectares || '25.5'} hectares
              </p>
              {summary && (
                <>
                  <p className={`text-sm font-medium mt-2 text-agri-${
                    summary.crop_health.status.toLowerCase() === 'good' ? 'green' : 
                    summary.crop_health.status.toLowerCase() === 'warning' ? 'yellow' : 'red'
                  }`}>
                    Health: {summary.crop_health.status}
                  </p>
                  <p className="text-sm">NDVI: {summary.crop_health.ndvi.toFixed(2)}</p>
                </>
              )}
            </div>
          </Popup>
        </Polygon>

        {/* Sensor markers */}
        {SAMPLE_SENSORS.map((sensor) => (
          <CircleMarker
            key={sensor.id}
            center={sensor.position}
            radius={8}
            pathOptions={{
              color: getSensorColor(sensor.status),
              weight: 2,
              opacity: 0.9,
              fillColor: getSensorColor(sensor.status),
              fillOpacity: 0.7,
            }}
          >
            <Popup>
              <div className="p-2">
                <h4 className="font-medium">Sensor {sensor.id}</h4>
                <p className="text-sm capitalize">Type: {sensor.type.replace('_', ' ')}</p>
                <p className="text-sm">Value: {sensor.value}</p>
                <p className={`text-sm font-medium capitalize text-agri-${
                  sensor.status === 'optimal' || sensor.status === 'good' ? 'green' :
                  sensor.status === 'warning' ? 'yellow' : 'red'
                }`}>
                  Status: {sensor.status}
                </p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      
      {/* Map legend */}
      <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-soft z-10">
        <h4 className="text-xs font-semibold mb-2">Legend</h4>
        <div className="space-y-1">
          <div className="flex items-center text-xs">
            <div className="w-3 h-3 bg-agri-green rounded mr-2"></div>
            <span>Healthy/Optimal</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-3 h-3 bg-agri-yellow rounded mr-2"></div>
            <span>Warning</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-3 h-3 bg-agri-red rounded mr-2"></div>
            <span>Critical</span>
          </div>
        </div>
      </div>
    </div>
  );
};
