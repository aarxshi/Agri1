# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Frontend (React/TypeScript)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server (runs on port 3000)
npm start

# Build for production
npm run build

# Run tests
npm test

# Type checking
npx tsc --noEmit
```

### Backend (Flask/Python)
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start Flask development server (runs on port 5000)
python app.py

# Run with specific environment
FLASK_ENV=development python app.py

# Run tests (if test files exist)
pytest

# Format code
black .
flake8 .
```

### Database Operations
```bash
# Create PostgreSQL database
createdb agriculture_monitoring

# Initialize database schema (if schema file exists)
psql -d agriculture_monitoring -f database/init_schema.sql

# Reset database (development)
python -c "from backend.models.models import init_db; init_db()"
```

### MATLAB Processing
```bash
# MATLAB scripts are in matlab-processing/
# Key processing functions:
# - hyperspectral/hyperspectral_processor.m
# - ai_models/crop_prediction_models.m  
# - simulation/digital_twin_crop_growth.m

# To run MATLAB processing from Python:
# Ensure MATLAB Engine for Python is installed
cd "matlabroot/extern/engines/python"
python setup.py install
```

### Full Development Setup
```bash
# Start all services (run each in separate terminal)
redis-server                    # Terminal 1: Redis cache/queue
cd backend && python app.py     # Terminal 2: Flask API
cd frontend && npm start        # Terminal 3: React frontend

# Access application at http://localhost:3000
```

### Testing
```bash
# Frontend tests
cd frontend && npm test

# Backend tests (if available)
cd backend && pytest

# Run specific test
cd frontend && npm test -- --testNamePattern="specific test"
```

## High-Level Architecture

### System Overview
This is a comprehensive agriculture monitoring platform that integrates multiple technologies:

**Frontend (React/TypeScript)**
- Modern React application with TypeScript
- TailwindCSS for responsive styling  
- Leaflet.js for interactive mapping
- Recharts for data visualization
- Runs on port 3000 in development

**Backend (Flask/Python)**
- RESTful API using Flask
- JWT authentication
- PostgreSQL for data persistence
- Redis for caching and background tasks
- Runs on port 5000 in development

**MATLAB Processing Engine**
- Hyperspectral image analysis using MATLAB's specialized toolboxes
- AI/ML models for crop health prediction
- Digital twin simulation capabilities
- Processes drone-captured imagery for vegetation indices (NDVI, SAVI, EVI, MCARI)

### Key Architectural Patterns

**Multi-tier Architecture**
```
Frontend (React) → Backend API (Flask) → Database (PostgreSQL)
                                     ↓
                              MATLAB Processing Engine
```

**Data Flow for Hyperspectral Processing**
1. Drone captures hyperspectral images
2. Images uploaded via React frontend
3. Flask API queues processing job
4. MATLAB engine processes images and calculates vegetation indices
5. Results stored in PostgreSQL and cached in Redis
6. Frontend displays processed maps and analytics

**AI/ML Pipeline**
- CNN models for spectral classification (ResNet-50 based)
- LSTM networks for time series forecasting  
- Ensemble models (XGBoost + Random Forest) for yield prediction
- Real-time sensor data fusion for comprehensive monitoring

### Database Schema Architecture
The application uses PostgreSQL with the following key entities:
- Users and authentication
- Fields and farm boundaries (geospatial data)
- Sensor readings time series
- Hyperspectral image metadata
- AI model predictions and alerts
- Processing job queue and results

### Background Processing
- Redis-backed Celery for asynchronous tasks
- MATLAB processing jobs run in background
- Weather data integration via APIs
- Automated alert generation based on thresholds

## Development Workflow

### File Structure Understanding
```
backend/
├── app.py              # Flask application entry point
├── app/__init__.py     # Application factory with blueprints
├── routes/             # API endpoint definitions
│   ├── auth_routes.py      # Authentication endpoints
│   ├── sensor_routes.py    # Sensor data APIs  
│   ├── image_routes.py     # Image upload/processing
│   ├── prediction_routes.py # AI model endpoints
│   └── dashboard_routes.py # Dashboard data
├── models/models.py    # SQLAlchemy database models
└── utils/             # Utility functions

frontend/src/
├── pages/             # Main application pages
├── components/        # Reusable React components
└── services/          # API communication layer

matlab-processing/
├── hyperspectral/     # Image processing algorithms
├── ai_models/         # Machine learning models
└── simulation/        # Digital twin simulations
```

### API Architecture
The Flask backend follows RESTful conventions with these main blueprint groups:
- `/api/auth/*` - Authentication (login, register, JWT refresh)
- `/api/sensors/*` - Sensor data CRUD operations
- `/api/images/*` - Image upload and hyperspectral processing  
- `/api/predictions/*` - AI model inference endpoints
- `/api/dashboard/*` - Aggregated data for dashboard views
- `/api/alerts/*` - Alert management system

### Configuration Management
- Environment-specific configs in `config/config.py`
- Development, Testing, and Production configurations
- Environment variables loaded from `.env` file
- Database connection pooling and Redis caching configured per environment

### Authentication & Security
- JWT-based authentication with Flask-JWT-Extended
- CORS configured for frontend-backend communication
- Input validation and SQL injection prevention
- File upload restrictions and security checks

### External Integrations
- **Weather APIs**: OpenWeatherMap integration for environmental data
- **Firebase**: Push notifications for alerts
- **Geospatial**: PostGIS extensions for spatial queries
- **MATLAB Engine**: Python-MATLAB bridge for processing

## Key Development Notes

### MATLAB Integration
- Requires MATLAB R2021a+ with specific toolboxes:
  - Hyperspectral Imaging Library
  - Image Processing Toolbox  
  - Deep Learning Toolbox
  - Simulink (for digital twin)
- MATLAB Engine for Python must be installed separately
- Processing functions return JSON results for Python integration

### Database Considerations
- Uses PostgreSQL with PostGIS for geospatial data
- Time series data for sensor readings requires partitioning for performance
- Hyperspectral images stored as file paths with metadata in database
- Redis caching for frequent queries and session management

### Performance Optimization
- Large hyperspectral images (500MB+) processed asynchronously
- Database connection pooling configured for concurrent users
- Image processing results cached in Redis
- Consider GPU acceleration for AI model inference in production

### Testing Strategy
- Frontend: Jest/React Testing Library (basic setup exists)
- Backend: pytest for API testing
- MATLAB: Unit tests for processing functions
- Integration tests for end-to-end workflows

### Development Environment
- Frontend hot-reloading via React dev server
- Backend auto-restart with Flask debug mode
- Database migrations handled via Flask-Migrate
- Environment variables in `.env.example` template

## Deployment Notes

### Environment Variables Required
Essential variables for production deployment:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Flask session encryption
- `JWT_SECRET_KEY` - JWT token signing
- `WEATHER_API_KEY` - OpenWeatherMap API key
- `REDIS_URL` - Redis connection string
- `FIREBASE_CREDENTIALS_PATH` - Firebase service account

### Production Considerations
- MATLAB Engine licensing for server deployment
- PostgreSQL tuning for time series data
- Redis configuration for background job queue
- File storage strategy for large image datasets
- Load balancing for concurrent hyperspectral processing

### Service Dependencies
- PostgreSQL 12+ with PostGIS extension
- Redis 6+ for caching and job queue
- MATLAB Runtime or full MATLAB installation
- Node.js 16+ for frontend build
- Python 3.8+ with scientific computing libraries
