import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { MapPage } from './pages/MapPage';
import { SearchPage } from './pages/SearchPage';
import { TrajectoryPage } from './pages/TrajectoryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AlertsPage } from './pages/AlertsPage';
import { LoginPage } from './pages/LoginPage';

export const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* Standalone Login Route */}
                <Route path="/login" element={<LoginPage />} />

                <Route path="/" element={<Layout />}>
                    {/* Default redirect to /dashboard */}
                    <Route index element={<Navigate to="/dashboard" replace />} />

                    {/* Main 6 Surveillance Control Room Routes */}
                    <Route path="dashboard" element={<DashboardPage />} />
                    <Route path="map" element={<MapPage />} />
                    <Route path="search" element={<SearchPage />} />
                    <Route path="trajectory/:vehicleId" element={<TrajectoryPage />} />
                    <Route path="trajectory" element={<TrajectoryPage />} />
                    <Route path="analytics" element={<AnalyticsPage />} />
                    <Route path="alerts" element={<AlertsPage />} />

                    {/* Fallback route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
};

export default App;

