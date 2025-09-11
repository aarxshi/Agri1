import React from 'react';
import { useRealTimeDashboard, useRealTimeTrends } from '../hooks/useApi';
import { FieldMap } from '../components/FieldMap';
import { TrendsChart } from '../components/TrendsChart';

export const DashboardPage: React.FC = () => {
  const { data: summary, loading: loadingSummary, error: summaryError } = useRealTimeDashboard(30000);
  const { data: trends, loading: loadingTrends } = useRealTimeTrends(1, 60000);

  const statusColor = (status: string) => {
    switch (status) {
      case 'good':
      case 'optimal':
        return 'text-agri-green';
      case 'warning':
      case 'medium':
        return 'text-agri-yellow';
      case 'urgent':
      case 'high':
        return 'text-agri-red';
      default:
        return 'text-gray-900';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {summaryError && (
        <div className="p-4 rounded-lg bg-red-50 text-red-700">{summaryError}</div>
      )}

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <h3 className="text-sm text-gray-500">Crop Health</h3>
          {loadingSummary || !summary ? (
            <div className="mt-4 h-8 bg-gray-100 rounded animate-pulse" />
          ) : (
            <>
              <p className={`text-3xl font-heading font-semibold mt-2 ${statusColor(summary.crop_health.status.toLowerCase())}`}>
                {summary.crop_health.status}
              </p>
              <p className="text-sm text-gray-500 mt-1">NDVI: {summary.crop_health.ndvi.toFixed(2)}</p>
            </>
          )}
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500">Soil Moisture</h3>
          {loadingSummary || !summary ? (
            <div className="mt-4 h-8 bg-gray-100 rounded animate-pulse" />
          ) : (
            <>
              <p className="text-3xl font-heading font-semibold mt-2">{summary.soil_moisture.value}%</p>
              <p className={`text-sm mt-1 ${statusColor(summary.soil_moisture.status)}`}>
                {summary.soil_moisture.status === 'optimal' ? 'Optimal' : summary.soil_moisture.status}
              </p>
            </>
          )}
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500">Pest Risk</h3>
          {loadingSummary || !summary ? (
            <div className="mt-4 h-8 bg-gray-100 rounded animate-pulse" />
          ) : (
            <>
              <p className={`text-3xl font-heading font-semibold mt-2 ${statusColor(summary.pest_risk.level)}`}>
                {summary.pest_risk.level.charAt(0).toUpperCase() + summary.pest_risk.level.slice(1)}
              </p>
              <p className="text-sm text-gray-500 mt-1">{summary.pest_risk.detected_pests.join(', ')}</p>
            </>
          )}
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500">Irrigation Advice</h3>
          {loadingSummary || !summary ? (
            <div className="mt-4 h-8 bg-gray-100 rounded animate-pulse" />
          ) : (
            <>
              <p className={`text-3xl font-heading font-semibold mt-2 ${statusColor(summary.irrigation_advice.status)}`}>
                {summary.irrigation_advice.recommendation}
              </p>
              <p className="text-sm text-gray-500 mt-1">{summary.irrigation_advice.reason}</p>
            </>
          )}
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-heading font-semibold">Field Map</h2>
        <p className="text-sm text-gray-600 mt-2">Interactive map with field boundaries and sensor locations</p>
        <div className="mt-4 h-96">
          <FieldMap summary={summary} className="h-full" />
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-heading font-semibold">Agricultural Trends</h2>
            <p className="text-sm text-gray-600">Real-time monitoring of key agricultural metrics</p>
          </div>
        </div>
        <TrendsChart 
          trends={trends} 
          loading={loadingTrends} 
          className=""
        />
      </section>
    </div>
  );
};

