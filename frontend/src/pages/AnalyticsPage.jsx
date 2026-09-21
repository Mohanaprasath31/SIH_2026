import React, { useState, useEffect } from 'react';
import {
    BarChart,
    Bar,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';
import { BarChart3, TrendingUp, Gauge, Activity, ArrowRightLeft, Loader2, AlertCircle } from 'lucide-react';
import { getHourlyVolume, getODMatrix } from '../api/client';

export const AnalyticsPage = () => {
    // Independent loading and error states for each chart block
    const [volumeData, setVolumeData] = useState([]);
    const [loadingVolume, setLoadingVolume] = useState(true);
    const [errorVolume, setErrorVolume] = useState(null);

    const [speedData, setSpeedData] = useState([]);
    const [loadingSpeed, setLoadingSpeed] = useState(true);

    const [congestionData, setCongestionData] = useState([]);
    const [loadingCongestion, setLoadingCongestion] = useState(true);

    const [odMatrix, setOdMatrix] = useState({ origins: [], destinations: [], matrix: [] });
    const [loadingOd, setLoadingOd] = useState(true);
    const [errorOd, setErrorOd] = useState(null);

    // 1. Fetch Hourly Volume & derive Speed + Congestion
    useEffect(() => {
        setLoadingVolume(true);
        setLoadingSpeed(true);
        setLoadingCongestion(true);

        getHourlyVolume()
            .then(data => {
                let hourly = [];
                if (Array.isArray(data)) {
                    hourly = data;
                } else if (data && Array.isArray(data.hourly)) {
                    hourly = data.hourly;
                }

                const formattedVolume = hourly.map(item => ({
                    time: item.hour || `${item.hour_of_day}:00` || '00:00',
                    volume: item.volume ?? item.count ?? 0,
                }));

                setVolumeData(formattedVolume);
                setLoadingVolume(false);

                const formattedSpeed = formattedVolume.map(item => {
                    return {
                        time: item.time,
                        avgSpeed: item.avg_speed ?? null,
                    };
                });
                setSpeedData(formattedSpeed);
                setLoadingSpeed(false);

                const formattedCongestion = formattedVolume.map(item => ({
                    time: item.time,
                    density: item.congestion ?? null,
                }));
                setCongestionData(formattedCongestion);
                setLoadingCongestion(false);
            })
            .catch(err => {
                console.error('Failed to load hourly volume:', err);
                setErrorVolume('Failed to load traffic volume analytics.');
                setLoadingVolume(false);
                setLoadingSpeed(false);
                setLoadingCongestion(false);
            });
    }, []);

    // 4. Fetch Origin-Destination Matrix
    useEffect(() => {
        setLoadingOd(true);
        getODMatrix()
            .then(data => {
                if (data && data.origins && data.destinations && data.matrix) {
                    setOdMatrix(data);
                }
            })
            .catch(err => {
                console.error('Failed to load OD matrix:', err);
                setErrorOd('Failed to load Origin-Destination matrix data.');
            })
            .finally(() => {
                setLoadingOd(false);
            });
    }, []);

    // Helper for OD matrix cell color scale
    const getCellColorClass = (val) => {
        if (!val || val === 0) return 'od-cell-0';
        if (val < 100) return 'od-cell-low';
        if (val < 200) return 'od-cell-med';
        if (val < 300) return 'od-cell-high';
        return 'od-cell-extreme';
    };

    return (
        <div className="page-container">
            {/* Page Header */}
            <div className="page-header">
                <div>
                    <h1 className="page-title">
                        <BarChart3 size={24} color="#06b6d4" />
                        Traffic Flow & Volume Analytics
                    </h1>
                    <p className="page-subtitle">
                        24-hour vehicle volume distribution, flow speed metrics, congestion index, and OD corridor matrices.
                    </p>
                </div>
            </div>

            {/* 2x2 Analytics Grid Container */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '1.5rem' }}>

                {/* Chart 1: Hourly Traffic Volume Bar Chart */}
                <div className="ops-card">
                    <div className="chart-card-header">
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <TrendingUp size={16} color="#06b6d4" />
                            Hourly Traffic Volume (24h)
                        </h3>
                        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#06b6d4' }}>
                            GET /analytics/hourly-volume
                        </span>
                    </div>

                    {loadingVolume ? (
                        <div className="state-container" style={{ padding: '2.5rem' }}>
                            <Loader2 size={24} className="animate-spin" />
                            <p style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono)', marginTop: '0.5rem' }}>
                                Loading hourly volume data...
                            </p>
                        </div>
                    ) : errorVolume ? (
                        <div className="state-container" style={{ padding: '2.5rem', color: '#ef4444' }}>
                            <AlertCircle size={24} />
                            <p style={{ fontSize: '0.8125rem', marginTop: '0.5rem' }}>{errorVolume}</p>
                        </div>
                    ) : (
                        <div style={{ width: '100%', height: 240 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={volumeData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                    <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} />
                                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px', color: '#fff' }}
                                        labelStyle={{ color: '#06b6d4', fontWeight: 'bold' }}
                                    />
                                    <Bar dataKey="volume" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>

                {/* Chart 2: Average Speed Line Chart */}
                <div className="ops-card">
                    <div className="chart-card-header">
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Gauge size={16} color="#10b981" />
                            Average Vehicle Speed (km/h)
                        </h3>
                        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#10b981' }}>
                            Flow Velocity
                        </span>
                    </div>

                    {loadingSpeed ? (
                        <div className="state-container" style={{ padding: '2.5rem' }}>
                            <Loader2 size={24} className="animate-spin" />
                            <p style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono)', marginTop: '0.5rem' }}>
                                Computing velocity metrics...
                            </p>
                        </div>
                    ) : (
                        <div style={{ width: '100%', height: 240 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={speedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                    <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} />
                                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} domain={[0, 80]} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px', color: '#fff' }}
                                        labelStyle={{ color: '#10b981', fontWeight: 'bold' }}
                                        formatter={(val) => [`${val} km/h`, 'Avg Speed']}
                                    />
                                    <Line type="monotone" dataKey="avgSpeed" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3, fill: '#10b981' }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>

                {/* Chart 3: Congestion Density Chart */}
                <div className="ops-card">
                    <div className="chart-card-header">
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Activity size={16} color="#f59e0b" />
                            Road Congestion Density Index
                        </h3>
                        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#f59e0b' }}>
                            Observation Density / hr
                        </span>
                    </div>

                    {loadingCongestion ? (
                        <div className="state-container" style={{ padding: '2.5rem' }}>
                            <Loader2 size={24} className="animate-spin" />
                            <p style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono)', marginTop: '0.5rem' }}>
                                Calculating congestion density...
                            </p>
                        </div>
                    ) : (
                        <div style={{ width: '100%', height: 240 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={congestionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                    <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} />
                                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} domain={[0, 100]} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px', color: '#fff' }}
                                        labelStyle={{ color: '#f59e0b', fontWeight: 'bold' }}
                                        formatter={(val) => [`${val}% Density Index`, 'Congestion']}
                                    />
                                    <Bar dataKey="density" radius={[4, 4, 0, 0]}>
                                        {congestionData.map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={entry.density > 75 ? '#ef4444' : entry.density > 45 ? '#f59e0b' : '#06b6d4'}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>

                {/* Chart 4: Origin-Destination Matrix Heatmap Table */}
                <div className="ops-card">
                    <div className="chart-card-header">
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <ArrowRightLeft size={16} color="#818cf8" />
                            Origin-Destination (OD) Matrix
                        </h3>
                        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#818cf8' }}>
                            GET /analytics/od-matrix
                        </span>
                    </div>

                    {loadingOd ? (
                        <div className="state-container" style={{ padding: '2.5rem' }}>
                            <Loader2 size={24} className="animate-spin" />
                            <p style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono)', marginTop: '0.5rem' }}>
                                Building OD Matrix Heatmap...
                            </p>
                        </div>
                    ) : errorOd ? (
                        <div className="state-container" style={{ padding: '2.5rem', color: '#ef4444' }}>
                            <AlertCircle size={24} />
                            <p style={{ fontSize: '0.8125rem', marginTop: '0.5rem' }}>{errorOd}</p>
                        </div>
                    ) : (
                        <div className="od-matrix-container">
                            <table className="od-table">
                                <thead>
                                    <tr>
                                        <th style={{ backgroundColor: '#0f172a', textAlign: 'left' }}>Origin \ Dest</th>
                                        {odMatrix.destinations.map((dest, idx) => (
                                            <th key={idx}>{dest}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {odMatrix.origins.map((orig, rIdx) => (
                                        <tr key={rIdx}>
                                            <td style={{ backgroundColor: '#0f172a', fontWeight: 'bold', color: '#f8fafc', textAlign: 'left' }}>
                                                {orig}
                                            </td>
                                            {odMatrix.matrix[rIdx]?.map((val, cIdx) => (
                                                <td key={cIdx} className={getCellColorClass(val)} title={`Trip count from ${orig} to ${odMatrix.destinations[cIdx]}: ${val}`}>
                                                    {val}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default AnalyticsPage;
