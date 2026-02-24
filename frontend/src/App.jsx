import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Toolbox from './pages/Toolbox';
import StockSelector from './pages/StockSelector';
import BatchBacktest from './pages/BatchBacktest';
import SingleBacktest from './pages/SingleBacktest';
import StrategyManagement from './pages/StrategyManagement';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/toolbox"
          element={
            <PrivateRoute>
              <Toolbox />
            </PrivateRoute>
          }
        />
        <Route
          path="/stock-selector"
          element={
            <PrivateRoute>
              <StockSelector />
            </PrivateRoute>
          }
        />
        <Route
          path="/batch-backtest"
          element={
            <PrivateRoute>
              <BatchBacktest />
            </PrivateRoute>
          }
        />
        <Route
          path="/single-backtest"
          element={
            <PrivateRoute>
              <SingleBacktest />
            </PrivateRoute>
          }
        />
        <Route
          path="/strategy-management"
          element={
            <PrivateRoute>
              <StrategyManagement />
            </PrivateRoute>
          }
        />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
};

export default App;
