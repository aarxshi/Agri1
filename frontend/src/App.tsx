import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './index.css';
import { DashboardPage } from './pages/DashboardPage';
import { FieldDetailPage } from './pages/FieldDetailPage';
import { AlertsPage } from './pages/AlertsPage';
import { LoginForm } from './components/LoginForm';
import { useAuth } from './hooks/useApi';

function App() {
  const { isAuthenticated, logout } = useAuth();
  const [showDashboard, setShowDashboard] = useState(false);

  // Show dashboard if authenticated OR if login was successful
  const shouldShowDashboard = isAuthenticated || showDashboard;

  if (!shouldShowDashboard) {
    return (
      <LoginForm 
        onSuccess={() => setShowDashboard(true)} 
      />
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-agri-light-green flex items-center justify-center shadow-soft">
                <span className="text-agri-green font-heading text-xl">🌱</span>
              </div>
              <div>
                <h1 className="text-xl font-heading font-semibold text-gray-900">Agri Monitor</h1>
                <p className="text-sm text-gray-500 -mt-1">Healthy crops, smart insights</p>
              </div>
            </Link>
            <nav className="flex items-center gap-6 text-sm">
              <Link to="/alerts" className="text-gray-600 hover:text-agri-green">Alerts</Link>
              <a href="#" className="text-gray-600 hover:text-agri-green">Reports</a>
              <a href="#" className="text-gray-600 hover:text-agri-green">Settings</a>
              <button
                onClick={() => {
                  logout();
                  setShowDashboard(false);
                }}
                className="text-gray-600 hover:text-agri-red transition-colors"
              >
                Sign Out
              </button>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/fields/:id" element={<FieldDetailPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
