import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Radio, ShieldAlert, Car, Gauge, Flame, RefreshCw, AlertCircle } from 'lucide-react';
import { getCameras, getAlerts, getHourlyVolume, searchVehicles } from '../api/client';

export const DashboardPage = () => {
    const [stats, setStats] = useState({
        activeCameras: '0 / 0',
        activeCamerasPercent: '0%',
        vehiclesDetected: '0',
        activeAlerts: '0',
        avgSpeed: '0 km/h',
        isOnline: true,
    });

    const [congestedRoads, setCongestedRoads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setLastRefreshed] = useState(new Date().toLocaleTimeString());
    const [error, setError] = useState(null);

    const fetchDashboardData = async () => {
        try {
            setError(null);
            const [camerasData, alertsData, hourlyData, vehiclesSearchData] = await Promise.all([
                getCameras().catch(err => { console.warn('Cameras API error:', err); return []; }),
                getAlerts().catch(err => { console.warn('Alerts API error:', err); return []; }),
                getHourlyVolume().catch(err => { console.warn('Hourly API error:', err); return null; }),
                searchVehicles('TN').catch(err => { console.warn('Vehicles API error:', err); return null; }),
            ]);

            // 1. Active Cameras Stat
            const camerasList = Array.isArray(camerasData) ? camerasData : [];
            const activeCams = camerasList.filter(c => c.status === 'active' || c.status === 'online').length;
            const totalCams = camerasList.length;
            const pct = Math.round((activeCams / totalCams) * 100);

            // 2. Vehicles Detected Today Stat
            let totalVehicles = 0;
            if (hourlyData && hourlyData.total_observations) {
                totalVehicles = hourlyData.total_observations;
            } else if (vehiclesSearchData && vehiclesSearchData.recent_observations) {
                totalVehicles = vehiclesSearchData.recent_observations.length;
            }

            // 3. Active Alerts Stat
            const alertsList = Array.isArray(alertsData) ? alertsData : [];
            const activeAlertsCount = alertsList.filter(a => a.status === 'New' || a.status === 'Investigating').length;

            setStats({
                activeCameras: `${activeCams} / ${totalCams}`,
                activeCamerasPercent: `${pct}% Online`,
                vehiclesDetected: totalVehicles.toLocaleString(),
                activeAlerts: String(activeAlertsCount),
                avgSpeed: '--',
                isOnline: true,
            });

            // 5. Congested Roads Ranking
            // Map road density per camera location
            const roadDensityMap = {};
            camerasList.forEach(cam => {
                const rName = cam.road || cam.name || 'Unknown Corridor';
                if (!roadDensityMap[rName]) {
                    roadDensityMap[rName] = {
                        road: rName,
                        zone: cam.zone || 'District',
                        count: 0,
                        activeCamerasCount: 0,
                        totalCamerasCount: 0,
                    };
                }
                roadDensityMap[rName].totalCamerasCount += 1;
                if (cam.status === 'active' || cam.status === 'online') {
                    roadDensityMap[rName].activeCamerasCount += 1;
                }
                roadDensityMap[rName].count += Number(cam.observation_count || 0);
            });

            let rankedList = Object.values(roadDensityMap);

            // Sort by observation volume descending
            rankedList.sort((a, b) => b.count - a.count);

            // Compute maximum volume for progress bar styling
            const maxVol = Math.max(...rankedList.map(r => r.count), 1);
            const formattedRoads = rankedList.map((r, idx) => {
                const fillPct = Math.round((r.count / maxVol) * 100);
                let severityClass = 'normal';
                if (fillPct > 80) severityClass = 'critical';
                else if (fillPct > 60) severityClass = 'high';
                else if (fillPct > 40) severityClass = 'medium';

                return {
                    ...r,
                    rank: idx + 1,
                    fillPct,
                    severityClass,
                };
            });

            setCongestedRoads(formattedRoads);
            setLastRefreshed(new Date().toLocaleTimeString());
        } catch (err) {
            console.error('Error loading dashboard data:', err);
            setError('Failed to refresh live surveillance feed data.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
        const intervalId = setInterval(() => {
            fetchDashboardData();
        }, 10000); // Auto-refresh every 10 seconds

        return () => clearInterval(intervalId);
    }, []);

    return (
        <div className="page-container">
            {/* Page Header with System Status */}
            <div className="page-header">
                <div>
                    <h1 className="page-title">
                        <LayoutDashboard size={24} color="#06b6d4" />
                        Control Room Operations Dashboard
                    </h1>
                    <p className="page-subtitle">
                        Real-time automated number plate recognition traffic metrics & congestion index.
                    </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div className={`status-pill ${stats.isOnline ? 'online' : 'offline'}`}>
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        {loading ? 'REFRESHING...' : 'LIVE 10S POLLING'}
                    </div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--ops-text-muted)' }}>
                        Updated: {lastRefreshed}
                    </span>
                </div>
            </div>

            {error && (
                <div className="alert-card critical" style={{ padding: '0.75rem 1rem' }}>
                    <AlertCircle size={18} color="#ef4444" />
                    <span style={{ fontSize: '0.875rem', color: '#ef4444', fontFamily: 'var(--font-mono)' }}>
                        {error}
                    </span>
                </div>
            )}

            {/* 4 Stat Cards Grid */}
            <div className="card-grid">
                {/* 1. Active Cameras */}
                <div className="ops-card">
                    <div className="card-header">
                        <span className="card-label">Active ANPR Cameras</span>
                        <Radio size={20} color="#10b981" />
                    </div>
                    <p className="card-value">{stats.activeCameras}</p>
                    <span className="card-subtext text-emerald">● {stats.activeCamerasPercent}</span>
                </div>

                {/* 2. Vehicles Detected Today */}
                <div className="ops-card">
                    <div className="card-header">
                        <span className="card-label">Vehicles Detected Today</span>
                        <Car size={20} color="#06b6d4" />
                    </div>
                    <p className="card-value">{stats.vehiclesDetected}</p>
                    <span className="card-subtext text-cyan">↑ 24h Aggregated OCR Captures</span>
                </div>

                {/* 3. Active Watchlist Alerts */}
                <div className="ops-card">
                    <div className="card-header">
                        <span className="card-label">Active Security Alerts</span>
                        <ShieldAlert size={20} color="#ef4444" />
                    </div>
                    <p className="card-value text-red">{stats.activeAlerts}</p>
                    <span className="card-subtext text-red">● High Priority Incident Flags</span>
                </div>

                {/* 4. Average Traffic Speed */}
                <div className="ops-card">
                    <div className="card-header">
                        <span className="card-label">Average Traffic Speed</span>
                        <Gauge size={20} color="#818cf8" />
                    </div>
                    <p className="card-value">{stats.avgSpeed}</p>
                    <span className="card-subtext" style={{ color: '#818cf8' }}>Corridor Flow Velocity</span>
                </div>
            </div>

            {/* Ranked List Panel: Congested Roads */}
            <div className="ops-card congested-roads-panel">
                <div className="panel-header-row">
                    <div className="panel-title">
                        <Flame size={20} color="#f97316" />
                        Congested Roads (Observation Density)
                    </div>
                    <span className="panel-badge">
                        RANKED BY TRAFFIC VOLUME
                    </span>
                </div>

                <div className="road-list">
                    {congestedRoads.map(road => {
                        const rankClass = road.rank <= 3 ? `rank-${road.rank}` : 'rank-normal';
                        return (
                            <div key={road.road} className="road-item-card">
                                <div className={`road-rank-badge ${rankClass}`}>
                                    #{road.rank}
                                </div>

                                <div className="road-info-col">
                                    <div className="road-name">{road.road}</div>
                                    <div className="road-meta">
                                        <span>Zone: {road.zone}</span>
                                        <span>•</span>
                                        <span>Cameras: {road.activeCamerasCount}/{road.totalCamerasCount} Online</span>
                                    </div>
                                </div>

                                <div className="road-metrics-col">
                                    <div className="road-volume-badge">
                                        {road.count} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--ops-text-muted)' }}>obs</span>
                                    </div>
                                    <div className="road-bar-wrapper">
                                        <div
                                            className={`road-bar-fill ${road.severityClass}`}
                                            style={{ width: `${road.fillPct}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
