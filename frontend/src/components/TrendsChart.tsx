/**
 * TrendsChart Component
 * Interactive charts showing agricultural trends using Recharts
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  ComposedChart,
} from 'recharts';
import { TrendData } from '../services/api';

interface TrendsChartProps {
  trends?: TrendData | null;
  loading?: boolean;
  className?: string;
}

// Transform trend data for chart consumption
const transformTrendData = (trends: TrendData) => {
  if (!trends || !trends.trends) return [];

  // Get all unique timestamps
  const allTimestamps = new Set<string>();
  
  Object.values(trends.trends).forEach(series => {
    series.forEach(point => allTimestamps.add(point.timestamp));
  });

  const sortedTimestamps = Array.from(allTimestamps).sort();

  return sortedTimestamps.map(timestamp => {
    const dataPoint: any = {
      timestamp,
      time: new Date(timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      date: new Date(timestamp).toLocaleDateString(),
    };

    // Add values for each trend type
    Object.entries(trends.trends).forEach(([key, series]) => {
      const point = series.find(p => p.timestamp === timestamp);
      dataPoint[key] = point ? point.value : null;
    });

    return dataPoint;
  });
};

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-md">
        <p className="text-sm font-medium mb-2">{`Time: ${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            <span className="capitalize">{entry.dataKey.replace('_', ' ')}: </span>
            <span className="font-medium">
              {entry.value?.toFixed(2)}
              {entry.dataKey === 'soil_moisture' || entry.dataKey === 'humidity' ? '%' : ''}
              {entry.dataKey === 'air_temperature' ? '°C' : ''}
              {entry.dataKey === 'ndvi' ? '' : ''}
            </span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Multi-line chart for all trends
const MultiLineChart: React.FC<{ data: any[] }> = ({ data }) => (
  <ResponsiveContainer width="100%" height="100%">
    <LineChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
      <XAxis 
        dataKey="time" 
        tick={{ fontSize: 12 }} 
        stroke="#64748b"
      />
      <YAxis tick={{ fontSize: 12 }} stroke="#64748b" />
      <Tooltip content={<CustomTooltip />} />
      <Legend />
      <Line 
        type="monotone" 
        dataKey="soil_moisture" 
        stroke="#22c55e" 
        strokeWidth={2}
        dot={{ r: 3 }}
        name="Soil Moisture (%)"
      />
      <Line 
        type="monotone" 
        dataKey="air_temperature" 
        stroke="#3b82f6" 
        strokeWidth={2}
        dot={{ r: 3 }}
        name="Temperature (°C)"
      />
      <Line 
        type="monotone" 
        dataKey="humidity" 
        stroke="#8b5cf6" 
        strokeWidth={2}
        dot={{ r: 3 }}
        name="Humidity (%)"
      />
      <Line 
        type="monotone" 
        dataKey="ndvi" 
        stroke="#f59e0b" 
        strokeWidth={2}
        dot={{ r: 3 }}
        name="NDVI"
      />
    </LineChart>
  </ResponsiveContainer>
);

// Area chart for soil moisture
const SoilMoistureChart: React.FC<{ data: any[] }> = ({ data }) => (
  <ResponsiveContainer width="100%" height="100%">
    <AreaChart data={data}>
      <defs>
        <linearGradient id="soilMoistureGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
          <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1}/>
        </linearGradient>
      </defs>
      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
      <XAxis 
        dataKey="time" 
        tick={{ fontSize: 12 }} 
        stroke="#64748b"
      />
      <YAxis 
        tick={{ fontSize: 12 }} 
        stroke="#64748b"
        domain={[0, 100]}
      />
      <Tooltip 
        formatter={(value: number) => [`${value.toFixed(1)}%`, 'Soil Moisture']}
        labelFormatter={(label) => `Time: ${label}`}
      />
      <Area
        type="monotone"
        dataKey="soil_moisture"
        stroke="#22c55e"
        strokeWidth={2}
        fillOpacity={1}
        fill="url(#soilMoistureGradient)"
      />
    </AreaChart>
  </ResponsiveContainer>
);

// Composed chart showing temperature and NDVI
const TemperatureNdviChart: React.FC<{ data: any[] }> = ({ data }) => (
  <ResponsiveContainer width="100%" height="100%">
    <ComposedChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
      <XAxis 
        dataKey="time" 
        tick={{ fontSize: 12 }} 
        stroke="#64748b"
      />
      <YAxis 
        yAxisId="temp"
        orientation="left"
        tick={{ fontSize: 12 }} 
        stroke="#3b82f6"
      />
      <YAxis 
        yAxisId="ndvi"
        orientation="right"
        tick={{ fontSize: 12 }} 
        stroke="#f59e0b"
        domain={[0, 1]}
      />
      <Tooltip content={<CustomTooltip />} />
      <Legend />
      <Bar 
        yAxisId="temp"
        dataKey="air_temperature" 
        fill="#3b82f6" 
        fillOpacity={0.6}
        name="Temperature (°C)"
      />
      <Line 
        yAxisId="ndvi"
        type="monotone" 
        dataKey="ndvi" 
        stroke="#f59e0b" 
        strokeWidth={3}
        dot={{ r: 4 }}
        name="NDVI"
      />
    </ComposedChart>
  </ResponsiveContainer>
);

export const TrendsChart: React.FC<TrendsChartProps> = ({ 
  trends, 
  loading = false, 
  className = '' 
}) => {
  const chartData = React.useMemo(() => {
    return trends ? transformTrendData(trends) : [];
  }, [trends]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-agri-green mx-auto mb-2"></div>
          <p className="text-gray-500">Loading trends...</p>
        </div>
      </div>
    );
  }

  if (!trends || chartData.length === 0) {
    return (
      <div className={`flex items-center justify-center text-gray-400 ${className}`}>
        <div className="text-center">
          <p>No trend data available</p>
          <p className="text-sm mt-1">Data will appear here once sensors start collecting information</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overview chart with all metrics */}
      <div className="bg-white rounded-lg p-4 shadow-soft">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">All Metrics Overview</h3>
        <div className="h-80">
          <MultiLineChart data={chartData} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Soil Moisture Area Chart */}
        <div className="bg-white rounded-lg p-4 shadow-soft">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Soil Moisture Trend</h3>
          <div className="h-64">
            <SoilMoistureChart data={chartData} />
          </div>
        </div>

        {/* Temperature vs NDVI Composed Chart */}
        <div className="bg-white rounded-lg p-4 shadow-soft">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Temperature vs NDVI</h3>
          <div className="h-64">
            <TemperatureNdviChart data={chartData} />
          </div>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(trends.trends).map(([key, series]) => {
          if (!series.length) return null;
          
          const latestValue = series[series.length - 1]?.value || 0;
          const previousValue = series.length > 1 ? series[series.length - 2]?.value || 0 : latestValue;
          const change = latestValue - previousValue;
          const isPositive = change >= 0;
          
          return (
            <div key={key} className="bg-white rounded-lg p-4 shadow-soft">
              <h4 className="text-sm font-medium text-gray-600 capitalize">
                {key.replace('_', ' ')}
              </h4>
              <p className="text-2xl font-bold mt-1">
                {latestValue.toFixed(1)}
                {key.includes('moisture') || key.includes('humidity') ? '%' : ''}
                {key.includes('temperature') ? '°C' : ''}
              </p>
              {change !== 0 && (
                <p className={`text-sm mt-1 flex items-center ${
                  isPositive ? 'text-agri-green' : 'text-agri-red'
                }`}>
                  <span className="mr-1">
                    {isPositive ? '↗' : '↘'}
                  </span>
                  {Math.abs(change).toFixed(2)}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
