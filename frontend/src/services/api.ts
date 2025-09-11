/**
 * API Service Layer
 * Centralized API client for communicating with the Flask backend
 */

export interface DashboardSummary {
  crop_health: {
    status: string;
    ndvi: number;
    confidence: number;
  };
  soil_moisture: {
    value: number;
    unit: string;
    status: string;
    last_updated: string;
  };
  pest_risk: {
    level: string;
    confidence: number;
    detected_pests: string[];
  };
  irrigation_advice: {
    recommendation: string;
    status: string;
    reason: string;
  };
  weather: {
    temperature: number;
    humidity: number;
    last_updated: string;
  };
  field_info: {
    id: number;
    name: string;
    crop_type: string;
    area_hectares: number;
  };
}

export interface Alert {
  id: number;
  field_id: number;
  field_name: string;
  level: string;
  message: string;
  created_at: string;
  resolved: boolean;
}

export interface TrendData {
  field_id: number;
  trends: {
    soil_moisture: Array<{ timestamp: string; value: number }>;
    air_temperature: Array<{ timestamp: string; value: number }>;
    humidity: Array<{ timestamp: string; value: number }>;
    ndvi: Array<{ timestamp: string; value: number }>;
  };
}

export interface SensorData {
  id: number;
  sensor_type: string;
  value: number;
  unit: string;
  location_lat?: number;
  location_lng?: number;
  timestamp: string;
  device_id?: string;
  quality_score: number;
}

export interface SensorDataResponse {
  field_id: number;
  field_name: string;
  data: SensorData[];
  count: number;
  filters: {
    sensor_type?: string;
    hours: number;
    limit: number;
  };
}

class ApiService {
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
    this.token = localStorage.getItem('auth_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token might be expired, remove it
          this.clearToken();
          throw new Error('Authentication required');
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  async login(username: string, password: string): Promise<{ access_token: string; user: any }> {
    // For now, use mock authentication since our backend auth might not be fully set up
    if (username === 'admin' && password === 'admin123') {
      const mockToken = 'mock_jwt_token_' + Date.now();
      this.setToken(mockToken);
      return {
        access_token: mockToken,
        user: { id: 1, username: 'admin', name: 'Administrator' }
      };
    }
    
    // Try actual backend login as fallback
    try {
      return this.request<{ access_token: string; user: any }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
    } catch (error) {
      throw new Error('Invalid username or password');
    }
  }

  async register(userData: {
    username: string;
    password: string;
    email: string;
    full_name?: string;
  }): Promise<{ message: string; user: any }> {
    return this.request<{ message: string; user: any }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // Dashboard APIs
  async getDashboardSummary(): Promise<DashboardSummary> {
    // Dashboard summary doesn't require auth in our current backend
    return this.requestWithoutAuth<DashboardSummary>('/dashboard/summary');
  }

  async getAlerts(): Promise<{ alerts: Alert[] }> {
    return this.requestWithoutAuth<{ alerts: Alert[] }>('/dashboard/alerts');
  }

  async getTrends(fieldId: number = 1): Promise<TrendData> {
    return this.requestWithoutAuth<TrendData>(`/dashboard/trends?field_id=${fieldId}`);
  }

  // Request method without authentication headers
  private async requestWithoutAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Sensor APIs
  async getSensorData(
    fieldId: number,
    sensorType?: string,
    hours: number = 24,
    limit: number = 100
  ): Promise<SensorDataResponse> {
    const params = new URLSearchParams({
      ...(sensorType && { sensor_type: sensorType }),
      hours: hours.toString(),
      limit: limit.toString(),
    });
    
    return this.request<SensorDataResponse>(`/sensors/data/${fieldId}?${params}`);
  }

  async addSensorData(data: {
    field_id: number;
    sensor_type: string;
    value: number;
    unit?: string;
    location_lat?: number;
    location_lng?: number;
    device_id?: string;
    quality_score?: number;
    timestamp?: string;
  }): Promise<{ message: string; data: any }> {
    return this.request<{ message: string; data: any }>('/sensors/data', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSensorTypes(): Promise<{ sensor_types: Array<{
    type: string;
    description: string;
    unit: string;
  }> }> {
    return this.request<{ sensor_types: Array<{
      type: string;
      description: string;
      unit: string;
    }> }>('/sensors/types');
  }

  // Image Processing APIs
  async uploadImage(formData: FormData): Promise<{ 
    message: string; 
    job_id: string; 
    estimated_processing_time: number;
  }> {
    return this.request<{ 
      message: string; 
      job_id: string; 
      estimated_processing_time: number;
    }>('/images/upload', {
      method: 'POST',
      headers: {
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        // Don't set Content-Type for FormData, let browser set it with boundary
      },
      body: formData,
    });
  }

  async getImageStatus(jobId: string): Promise<{
    job_id: string;
    status: string;
    progress: number;
    result?: any;
    error?: string;
  }> {
    return this.request<{
      job_id: string;
      status: string;
      progress: number;
      result?: any;
      error?: string;
    }>(`/images/status/${jobId}`);
  }

  async getSpectralIndices(imageId: number): Promise<{
    image_id: number;
    indices: {
      ndvi: number[][];
      savi: number[][];
      evi: number[][];
      mcari: number[][];
    };
    metadata: any;
  }> {
    return this.request<{
      image_id: number;
      indices: {
        ndvi: number[][];
        savi: number[][];
        evi: number[][];
        mcari: number[][];
      };
      metadata: any;
    }>(`/images/indices/${imageId}`);
  }

  // Prediction APIs
  async predictCropHealth(fieldId: number): Promise<{
    field_id: number;
    predictions: {
      health_score: number;
      disease_risk: string;
      pest_risk: string;
      yield_prediction: number;
      recommendations: string[];
    };
  }> {
    return this.request<{
      field_id: number;
      predictions: {
        health_score: number;
        disease_risk: string;
        pest_risk: string;
        yield_prediction: number;
        recommendations: string[];
      };
    }>(`/predictions/crop-health/${fieldId}`, {
      method: 'POST',
    });
  }

  async predictPests(fieldId: number): Promise<{
    field_id: number;
    predictions: {
      pest_types: string[];
      risk_level: string;
      confidence: number;
      treatment_recommendations: string[];
    };
  }> {
    return this.request<{
      field_id: number;
      predictions: {
        pest_types: string[];
        risk_level: string;
        confidence: number;
        treatment_recommendations: string[];
      };
    }>(`/predictions/pests/${fieldId}`, {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();
export default apiService;
