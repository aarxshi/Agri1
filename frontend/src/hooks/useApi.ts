/**
 * Custom React Hooks for API Data Fetching
 * Provides reusable hooks with loading states, error handling, and caching
 */

import { useState, useEffect, useCallback } from 'react';
import apiService, { DashboardSummary, Alert, TrendData, SensorDataResponse } from '../services/api';

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface ApiHook<T> extends ApiState<T> {
  refetch: () => void;
}

// Generic hook for API calls
function useApiCall<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
): ApiHook<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await apiCall();
      setState({ data: result, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : 'An error occurred'
      });
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Dashboard hooks
export function useDashboardSummary(): ApiHook<DashboardSummary> {
  return useApiCall(() => apiService.getDashboardSummary());
}

export function useAlerts(): ApiHook<{ alerts: Alert[] }> {
  return useApiCall(() => apiService.getAlerts());
}

export function useTrends(fieldId: number = 1): ApiHook<TrendData> {
  return useApiCall(() => apiService.getTrends(fieldId), [fieldId]);
}

// Sensor hooks
export function useSensorData(
  fieldId: number,
  sensorType?: string,
  hours: number = 24,
  limit: number = 100
): ApiHook<SensorDataResponse> {
  return useApiCall(
    () => apiService.getSensorData(fieldId, sensorType, hours, limit),
    [fieldId, sensorType, hours, limit]
  );
}

export function useSensorTypes(): ApiHook<{ sensor_types: Array<{
  type: string;
  description: string;
  unit: string;
}> }> {
  return useApiCall(() => apiService.getSensorTypes());
}

// Auto-refresh hook
export function useAutoRefresh<T>(
  apiHook: ApiHook<T>,
  intervalMs: number = 30000
): ApiHook<T> {
  useEffect(() => {
    if (intervalMs <= 0) return;

    const interval = setInterval(() => {
      apiHook.refetch();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [apiHook.refetch, intervalMs]);

  return apiHook;
}

// Real-time polling hooks
export function useRealTimeDashboard(intervalMs: number = 30000): ApiHook<DashboardSummary> {
  const apiHook = useDashboardSummary();
  return useAutoRefresh(apiHook, intervalMs);
}

export function useRealTimeTrends(fieldId: number = 1, intervalMs: number = 60000): ApiHook<TrendData> {
  const apiHook = useTrends(fieldId);
  return useAutoRefresh(apiHook, intervalMs);
}

// Authentication hook
export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('auth_token')
  );

  const login = async (username: string, password: string) => {
    try {
      const response = await apiService.login(username, password);
      apiService.setToken(response.access_token);
      setIsAuthenticated(true);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (userData: {
    username: string;
    password: string;
    email: string;
    full_name?: string;
  }) => {
    try {
      const response = await apiService.register(userData);
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    apiService.clearToken();
    setIsAuthenticated(false);
  };

  return {
    isAuthenticated,
    login,
    register,
    logout,
  };
}

// Image processing hooks
export function useImageUpload() {
  const [uploadState, setUploadState] = useState<{
    uploading: boolean;
    jobId: string | null;
    error: string | null;
  }>({
    uploading: false,
    jobId: null,
    error: null,
  });

  const uploadImage = async (file: File, fieldId: number) => {
    setUploadState({ uploading: true, jobId: null, error: null });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('field_id', fieldId.toString());

      const response = await apiService.uploadImage(formData);
      setUploadState({
        uploading: false,
        jobId: response.job_id,
        error: null
      });

      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadState({ uploading: false, jobId: null, error: errorMessage });
      throw error;
    }
  };

  return {
    ...uploadState,
    uploadImage,
    resetState: () => setUploadState({ uploading: false, jobId: null, error: null }),
  };
}

export function useImageProcessingStatus(jobId: string | null) {
  return useApiCall(
    () => {
      if (!jobId) throw new Error('No job ID provided');
      return apiService.getImageStatus(jobId);
    },
    [jobId]
  );
}

// Prediction hooks
export function useCropHealthPrediction(fieldId: number, trigger: boolean = false): ApiHook<{
  field_id: number;
  predictions: {
    health_score: number;
    disease_risk: string;
    pest_risk: string;
    yield_prediction: number;
    recommendations: string[];
  };
}> & { predict: () => void } {
  const [shouldFetch, setShouldFetch] = useState(trigger);

  const apiHook = useApiCall(
    () => {
      if (!shouldFetch) throw new Error('Prediction not triggered');
      return apiService.predictCropHealth(fieldId);
    },
    [fieldId, shouldFetch]
  );

  const predict = useCallback(() => {
    setShouldFetch(true);
  }, []);

  return {
    ...apiHook,
    predict,
  };
}

export function usePestPrediction(fieldId: number, trigger: boolean = false): ApiHook<{
  field_id: number;
  predictions: {
    pest_types: string[];
    risk_level: string;
    confidence: number;
    treatment_recommendations: string[];
  };
}> & { predict: () => void } {
  const [shouldFetch, setShouldFetch] = useState(trigger);

  const apiHook = useApiCall(
    () => {
      if (!shouldFetch) throw new Error('Prediction not triggered');
      return apiService.predictPests(fieldId);
    },
    [fieldId, shouldFetch]
  );

  const predict = useCallback(() => {
    setShouldFetch(true);
  }, []);

  return {
    ...apiHook,
    predict,
  };
}
