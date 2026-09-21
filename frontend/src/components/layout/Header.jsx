import React, { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { getHealth } from '../../api/client';
import { WifiOff, RefreshCw, Clock, Database } from 'lucide-react';

const routeTitles = {
    '/dashboard': 'Dashboard Overview',
    '/map': 'Surveillance Map Layer',
    '/search': 'Vehicle Plate Search & OCR',
    '/analytics': 'Traffic Volume & OD Matrix',
    '/alerts': 'Security & Watchlist Alerts',
};

export const Header = () => {
    const location = useLocation();
    const [health, setHealth] = useState(null);
    const [status, setStatus] = useState('checking');
    const [currentTime, setCurrentTime] = useState('');

    // Live clock ticker
    useEffect(() => {
        const updateTime = () => {
            const now = new Date();
            setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }));
        };
        updateTime();
        const interval = setInterval(updateTime, 1000);
        return () => clearInterval(interval);
    }, []);

    // Ping backend GET /health
    const checkApiHealth = useCallback(async () => {
        setStatus('checking');
        try {
            const data = await getHealth();
            setHealth(data);
            setStatus('connected');
        } catch (err) {
            console.warn('API connection ping failed:', err);
            setHealth(null);
            setStatus('offline');
        }
    }, []);

    useEffect(() => {
        checkApiHealth();
        const timer = setInterval(checkApiHealth, 10000);
        return () => clearInterval(timer);
    }, [checkApiHealth]);

    let pageTitle = routeTitles[location.pathname];
    if (!pageTitle) {
        if (location.pathname.startsWith('/trajectory')) {
            pageTitle = 'Vehicle Trajectory Analysis';
        } else {
            pageTitle = 'ANPR Control Room';
        }
    }

    return (
        <header className="ops-header">
            {/* Route Title & Breadcrumb */}
            <div className="header-left">
                <div className="header-dot" />
                <div>
                    <h1 className="header-title">{pageTitle}</h1>
                    <p className="header-breadcrumb">
                        CONTROL ROOM / <span>{location.pathname}</span>
                    </p>
                </div>
            </div>

            {/* Right Controls & Live API Health Status */}
            <div className="header-right">
                {/* Real-time Clock */}
                <div className="clock-badge">
                    <Clock size={14} color="#06b6d4" />
                    <span>{currentTime || '00:00:00'} IST</span>
                </div>

                {/* Live API Health Status Badge */}
                <div>
                    {status === 'connected' && (
                        <div className="status-pill online">
                            <span className="header-dot" style={{ backgroundColor: '#10b981', boxShadow: '0 0 8px #10b981' }} />
                            <span>API ONLINE</span>
                            {health?.database && (
                                <span className="status-pill-db">
                                    <Database size={12} />
                                    {health.database}
                                </span>
                            )}
                        </div>
                    )}

                    {status === 'offline' && (
                        <div className="status-pill offline">
                            <WifiOff size={14} />
                            <span>API OFFLINE</span>
                            <button
                                onClick={checkApiHealth}
                                title="Retry API connection"
                                className="icon-button"
                            >
                                <RefreshCw size={12} />
                            </button>
                        </div>
                    )}

                    {status === 'checking' && (
                        <div className="status-pill checking">
                            <RefreshCw size={14} className="animate-spin" />
                            <span>PINGING API...</span>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};
