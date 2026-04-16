import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PrivateRoute from './components/PrivateRoute';
import MarketPage from './pages/MarketPage';
import PortfoliosPage from './pages/PortfoliosPage';
import PortfolioDetailsPage from './pages/PortfolioDetailsPage';
import Header from './components/Header';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <Header />
      <main className="app-main">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <MarketPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolios"
            element={
              <PrivateRoute>
                <PortfoliosPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolio/:id"
            element={
              <PrivateRoute>
                <PortfolioDetailsPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolio/:id/trades"
            element={
              <PrivateRoute>
                <PortfolioDetailsPage activeTab="trades" />
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolio/:id/analytics"
            element={
              <PrivateRoute>
                <PortfolioDetailsPage activeTab="overview" />
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolio/:id/reports"
            element={
              <PrivateRoute>
                <PortfolioDetailsPage activeTab="reports" />
              </PrivateRoute>
            }
          />
        </Routes>
      </main>
    </Router>
  );
};

export default App;
