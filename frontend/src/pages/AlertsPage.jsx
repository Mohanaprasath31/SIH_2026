import React, { useEffect, useMemo, useState } from 'react';
import {
    AlertTriangle,
    ArrowDown,
    ArrowUp,
    Bell,
    Camera,
    CheckCircle2,
    ChevronDown,
    ChevronUp,
    Clock3,
    Eye,
    Filter,
    MapPin,
    RefreshCw,
    Search,
    ShieldAlert,
    ShieldCheck,
    Siren,
    Timer,
    Truck,
    XCircle,
    Activity,
} from 'lucide-react';

import {
    getAlerts,
    getCameras,
    updateAlertStatus,
} from '../api/client';
import './AlertsPage.css';

const AlertsPage = () => {
    const [alerts, setAlerts] = useState([]);
    const [cameraMap, setCameraMap] = useState({});
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const [error, setError] = useState('');
    const [statusSuccess, setStatusSuccess] = useState('');
    const [statusError, setStatusError] = useState('');

    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [severityFilter, setSeverityFilter] = useState('');
    const [sortOrder, setSortOrder] = useState('newest');

    const [expandedAlertId, setExpandedAlertId] = useState(null);
    const [updatingAlertId, setUpdatingAlertId] = useState(null);

    const loadData = async (showLoader = true) => {
        try {
            if (showLoader) {
                setLoading(true);
            } else {
                setRefreshing(true);
            }

            setError('');

            const [alertsResponse, camerasResponse] = await Promise.all([
                getAlerts(),
                getCameras(),
            ]);

            const alertData = Array.isArray(alertsResponse)
                ? alertsResponse
                : alertsResponse?.data || alertsResponse?.items || [];

            const cameraData = Array.isArray(camerasResponse)
                ? camerasResponse
                : camerasResponse?.data || camerasResponse?.items || [];

            setAlerts(alertData);

            const map = {};

            cameraData.forEach((camera) => {
                const id = camera.id || camera.camera_id;
                if (id) {
                    map[id] = camera;
                }
            });

            setCameraMap(map);
        } catch (err) {
            console.error('Failed to load alerts:', err);
            setError(err.message || 'Failed to load alerts.');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleRefresh = async () => {
        setStatusSuccess('');
        setStatusError('');
        await loadData(false);
    };

    const handleStatusChange = async (alertId, newStatus) => {
        try {
            setUpdatingAlertId(alertId);
            setStatusSuccess('');
            setStatusError('');

            await updateAlertStatus(alertId, newStatus);

            setAlerts((previous) =>
                previous.map((alert) =>
                    alert.id === alertId
                        ? { ...alert, status: newStatus }
                        : alert
                )
            );

            setStatusSuccess('Alert status updated to "' + newStatus + '".');
        } catch (err) {
            console.error('Failed to update alert:', err);
            setStatusError(err.message || 'Failed to update alert status.');
        } finally {
            setUpdatingAlertId(null);
        }
    };

    const normalize = (value) => String(value || '').trim().toLowerCase();

    const getSeverity = (alert) => {
        const severity = normalize(alert?.severity);
        if (severity === 'critical') return 'Critical';
        if (severity === 'high') return 'High';
        if (severity === 'medium') return 'Medium';
        if (severity === 'low') return 'Low';
        return 'Unknown';
    };

    const getStatus = (alert) => {
        return alert?.status || 'New';
    };

    const getPlate = (alert) => {
        return alert?.normalized_plate || alert?.plate || alert?.vehicle_plate || 'Unknown';
    };

    const getCamera = (alert) => {
        const cameraId = alert?.camera_id || alert?.cameraId || alert?.camera?.id;
        if (cameraId && cameraMap[cameraId]) return cameraMap[cameraId];
        if (alert?.camera) return alert.camera;
        return null;
    };

    const getCameraName = (alert) => {
        const camera = getCamera(alert);
        return camera?.name || camera?.camera_name || camera?.location || alert?.camera_name || alert?.camera_id || 'Unknown camera';
    };

    const getDetectionTime = (alert) => {
        return alert?.detected_at || alert?.detection_time || alert?.created_at || alert?.timestamp || null;
    };

    const formatDateTime = (value) => {
        if (!value) return 'Not available';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return date.toLocaleString([], {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const formatTimeAgo = (value) => {
        if (!value) return 'Unknown time';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return 'Unknown time';
        const difference = Date.now() - date.getTime();
        const seconds = Math.floor(difference / 1000);
        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes} min ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} hr ago`;
        const days = Math.floor(hours / 24);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    };

    const getSeverityClasses = (severity) => {
        switch (severity) {
            case 'Critical':
                return {
                    badge: 'badge-critical',
                    dot: 'dot-critical',
                    border: 'border-critical',
                    icon: 'icon-critical',
                };
            case 'High':
                return {
                    badge: 'badge-high',
                    dot: 'dot-high',
                    border: 'border-high',
                    icon: 'icon-high',
                };
            case 'Medium':
                return {
                    badge: 'badge-medium',
                    dot: 'dot-medium',
                    border: 'border-medium',
                    icon: 'icon-medium',
                };
            case 'Low':
                return {
                    badge: 'badge-low',
                    dot: 'dot-low',
                    border: 'border-low',
                    icon: 'icon-low',
                };
            default:
                return {
                    badge: 'badge-default',
                    dot: 'dot-default',
                    border: 'border-default',
                    icon: 'icon-default',
                };
        }
    };

    const getStatusClasses = (status) => {
        switch (status) {
            case 'New': return 'status-new';
            case 'Acknowledged': return 'status-acknowledged';
            case 'Investigating': return 'status-investigating';
            case 'Resolved': return 'status-resolved';
            case 'Dismissed': return 'status-dismissed';
            default: return 'status-dismissed';
        }
    };

    const filteredAlerts = useMemo(() => {
        const result = alerts.filter((alert) => {
            const plate = getPlate(alert);
            const cameraName = getCameraName(alert);
            const severity = getSeverity(alert);
            const status = getStatus(alert);

            const searchableText = [plate, cameraName, severity, status, alert?.description, alert?.message].join(' ').toLowerCase();

            const matchesSearch = !search || searchableText.includes(search.toLowerCase());
            const matchesStatus = !statusFilter || status === statusFilter;
            const matchesSeverity = !severityFilter || severity === severityFilter;

            return matchesSearch && matchesStatus && matchesSeverity;
        });

        result.sort((a, b) => {
            const dateA = new Date(getDetectionTime(a) || 0).getTime();
            const dateB = new Date(getDetectionTime(b) || 0).getTime();
            return sortOrder === 'oldest' ? dateA - dateB : dateB - dateA;
        });

        return result;
    }, [alerts, cameraMap, search, statusFilter, severityFilter, sortOrder]);

    const statistics = useMemo(() => {
        const critical = alerts.filter((alert) => getSeverity(alert) === 'Critical').length;
        const high = alerts.filter((alert) => getSeverity(alert) === 'High').length;
        const active = alerts.filter((alert) => !['Resolved', 'Dismissed'].includes(getStatus(alert))).length;
        const resolved = alerts.filter((alert) => getStatus(alert) === 'Resolved').length;

        return { total: alerts.length, critical, high, active, resolved };
    }, [alerts]);

    const toggleExpand = (alertId) => {
        setStatusSuccess('');
        setStatusError('');
        setExpandedAlertId((current) => current === alertId ? null : alertId);
    };

    const clearFilters = () => {
        setSearch('');
        setStatusFilter('');
        setSeverityFilter('');
        setSortOrder('newest');
    };

    const getAlertTitle = (alert) => {
        if (alert?.title) return alert.title;
        if (alert?.alert_type) {
            return String(alert.alert_type).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
        }
        return 'ANPR Security Alert';
    };

    const getAlertMessage = (alert) => {
        return alert?.description || alert?.message || alert?.reason || 'Vehicle observation requires investigation.';
    };

    const getEvidence = (alert) => {
        return alert?.evidence_image || alert?.evidenceImage || alert?.image_url || alert?.imageUrl || null;
    };

    if (loading) {
        return (
            <div className="alerts-loading">
                <div className="alerts-header-container">
                    <div className="alerts-header-content" style={{ padding: '1.75rem 1.5rem' }}>
                        <div className="alerts-header-left">
                            <div className="alerts-header-icon-box">
                                <ShieldAlert className="alerts-header-icon" />
                            </div>
                            <div>
                                <h1 className="alerts-title">Security Alerts</h1>
                                <p className="alerts-subtitle">City-wide ANPR monitoring and incident response</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="alerts-loading-content">
                    <div className="alerts-loading-icon-box">
                        <RefreshCw className="alerts-loading-icon icon-spin" />
                    </div>
                    <h2 className="alerts-loading-title">Loading alerts</h2>
                    <p className="alerts-loading-text">Fetching the latest city surveillance events...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="alerts-page">
            {/* HEADER */}
            <header className="alerts-header-container">
                <div className="alerts-header-content">
                    <div className="alerts-header-left">
                        <div className="alerts-header-icon-box">
                            <ShieldAlert className="alerts-header-icon" />
                            {statistics.active > 0 && <span className="alerts-active-dot" />}
                        </div>
                        <div>
                            <div className="alerts-title-row">
                                <h1 className="alerts-title">Security Alerts</h1>
                                <span className="alerts-live-badge">
                                    <span className="alerts-live-dot" />
                                    Live monitoring
                                </span>
                            </div>
                            <p className="alerts-subtitle">City-wide ANPR incidents and vehicle security events</p>
                        </div>
                    </div>
                    <div className="alerts-header-right">
                        <div className="alerts-system-status">
                            <Activity className="alerts-system-icon" />
                            <div>
                                <p className="alerts-system-label">System</p>
                                <p className="alerts-system-value">Operational</p>
                            </div>
                        </div>
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className="alerts-refresh-btn"
                        >
                            <RefreshCw className={`${refreshing ? 'icon-spin' : ''}`} style={{ width: '1rem', height: '1rem' }} />
                            {refreshing ? 'Refreshing' : 'Refresh'}
                        </button>
                    </div>
                </div>
            </header>

            {/* MAIN */}
            <main className="alerts-main">
                {error && (
                    <div className="alerts-message alerts-message-error">
                        <XCircle className="alerts-message-icon" />
                        <div>
                            <p className="alerts-message-title">Unable to load alerts</p>
                            <p className="alerts-message-text">{error}</p>
                        </div>
                    </div>
                )}
                {statusSuccess && (
                    <div className="alerts-message alerts-message-success">
                        <CheckCircle2 className="alerts-message-icon" />
                        <p className="alerts-message-title" style={{ margin: 0 }}>{statusSuccess}</p>
                    </div>
                )}
                {statusError && (
                    <div className="alerts-message alerts-message-error">
                        <XCircle className="alerts-message-icon" />
                        <p className="alerts-message-title" style={{ margin: 0 }}>{statusError}</p>
                    </div>
                )}

                {/* STATISTICS */}
                <section className="alerts-stats-grid">
                    <div className="alerts-stat-card">
                        <div className="alerts-stat-glow glow-blue" />
                        <div className="alerts-stat-content">
                            <div>
                                <p className="alerts-stat-label">Total alerts</p>
                                <p className="alerts-stat-value val-white">{statistics.total}</p>
                                <p className="alerts-stat-subtext">All recorded incidents</p>
                            </div>
                            <div className="alerts-stat-icon-box box-blue">
                                <Bell className="alerts-stat-icon" />
                            </div>
                        </div>
                    </div>

                    <div className="alerts-stat-card">
                        <div className="alerts-stat-glow glow-orange" />
                        <div className="alerts-stat-content">
                            <div>
                                <p className="alerts-stat-label">Active</p>
                                <p className="alerts-stat-value val-white">{statistics.active}</p>
                                <p className="alerts-stat-subtext">Require attention</p>
                            </div>
                            <div className="alerts-stat-icon-box box-orange">
                                <Siren className="alerts-stat-icon" />
                            </div>
                        </div>
                    </div>

                    <div className="alerts-stat-card">
                        <div className="alerts-stat-glow glow-red" />
                        <div className="alerts-stat-content">
                            <div>
                                <p className="alerts-stat-label">Critical</p>
                                <p className="alerts-stat-value val-red">{statistics.critical}</p>
                                <p className="alerts-stat-subtext">Highest severity</p>
                            </div>
                            <div className="alerts-stat-icon-box box-red">
                                <AlertTriangle className="alerts-stat-icon" />
                            </div>
                        </div>
                    </div>

                    <div className="alerts-stat-card">
                        <div className="alerts-stat-glow glow-orange" />
                        <div className="alerts-stat-content">
                            <div>
                                <p className="alerts-stat-label">High</p>
                                <p className="alerts-stat-value val-orange">{statistics.high}</p>
                                <p className="alerts-stat-subtext">Elevated priority</p>
                            </div>
                            <div className="alerts-stat-icon-box box-orange">
                                <ShieldAlert className="alerts-stat-icon" />
                            </div>
                        </div>
                    </div>

                    <div className="alerts-stat-card col-span-2">
                        <div className="alerts-stat-glow glow-emerald" />
                        <div className="alerts-stat-content">
                            <div>
                                <p className="alerts-stat-label">Resolved</p>
                                <p className="alerts-stat-value val-emerald">{statistics.resolved}</p>
                                <p className="alerts-stat-subtext">Closed incidents</p>
                            </div>
                            <div className="alerts-stat-icon-box box-emerald">
                                <ShieldCheck className="alerts-stat-icon" />
                            </div>
                        </div>
                    </div>
                </section>

                {/* FILTER BAR */}
                <section className="alerts-filters">
                    <div className="alerts-filters-inner">
                        <div className="alerts-filters-row">
                            {/* Search */}
                            <div className="alerts-search-wrapper">
                                <Search className="alerts-search-icon" />
                                <input
                                    type="text"
                                    value={search}
                                    onChange={(event) => setSearch(event.target.value)}
                                    placeholder="Search plate, camera, alert type..."
                                    className="alerts-input"
                                />
                            </div>

                            {/* Severity */}
                            <div className="alerts-select-wrapper">
                                <select
                                    value={severityFilter}
                                    onChange={(event) => setSeverityFilter(event.target.value)}
                                    className="alerts-select"
                                >
                                    <option value="">All severities</option>
                                    <option value="Critical">Critical</option>
                                    <option value="High">High</option>
                                    <option value="Medium">Medium</option>
                                    <option value="Low">Low</option>
                                </select>
                                <ChevronDown className="alerts-select-icon" />
                            </div>

                            {/* Status */}
                            <div className="alerts-select-wrapper">
                                <select
                                    value={statusFilter}
                                    onChange={(event) => setStatusFilter(event.target.value)}
                                    className="alerts-select"
                                >
                                    <option value="">All statuses</option>
                                    <option value="New">New</option>
                                    <option value="Acknowledged">Acknowledged</option>
                                    <option value="Investigating">Investigating</option>
                                    <option value="Resolved">Resolved</option>
                                    <option value="Dismissed">Dismissed</option>
                                </select>
                                <ChevronDown className="alerts-select-icon" />
                            </div>

                            {/* Sort */}
                            <div className="alerts-select-wrapper">
                                <select
                                    value={sortOrder}
                                    onChange={(event) => setSortOrder(event.target.value)}
                                    className="alerts-select"
                                >
                                    <option value="newest">Newest first</option>
                                    <option value="oldest">Oldest first</option>
                                </select>
                                <ChevronDown className="alerts-select-icon" />
                            </div>

                            <button onClick={clearFilters} className="alerts-clear-btn">
                                <Filter style={{ width: '1rem', height: '1rem' }} />
                                Clear
                            </button>
                        </div>

                        <div className="alerts-filters-footer">
                            <p className="alerts-filters-count">
                                Showing <span>{filteredAlerts.length}</span> of <span>{alerts.length}</span> alerts
                            </p>
                            <div className="alerts-filters-hint">
                                <Filter style={{ width: '0.875rem', height: '0.875rem' }} />
                                Filters update instantly
                            </div>
                        </div>
                    </div>
                </section>

                {/* ALERT LIST */}
                <section>
                    {filteredAlerts.length === 0 ? (
                        <div className="alerts-list-empty">
                            <div className="alerts-empty-icon-box">
                                <ShieldCheck className="alerts-empty-icon" />
                            </div>
                            <h2 className="alerts-empty-title">No alerts found</h2>
                            <p className="alerts-empty-text">
                                There are no alerts matching the current filters. Try clearing the filters or refreshing the system.
                            </p>
                            <button onClick={clearFilters} className="alerts-empty-btn">
                                Clear filters
                            </button>
                        </div>
                    ) : (
                        <div className="alerts-list">
                            {filteredAlerts.map((alert) => {
                                const severity = getSeverity(alert);
                                const status = getStatus(alert);
                                const severityStyle = getSeverityClasses(severity);
                                const camera = getCamera(alert);
                                const plate = getPlate(alert);
                                const detectionTime = getDetectionTime(alert);
                                const isExpanded = expandedAlertId === alert.id;
                                const evidence = getEvidence(alert);

                                return (
                                    <article
                                        key={alert.id}
                                        className={`alert-item ${severityStyle.border}`}
                                    >
                                        <div className="alert-item-summary">
                                            <div className="alert-item-row">
                                                {/* Alert icon */}
                                                <div className="alert-item-title-section">
                                                    <div className={`alert-item-icon-box ${severityStyle.icon}`}>
                                                        {severity === 'Critical' ? <Siren className="alert-item-icon" /> : <AlertTriangle className="alert-item-icon" />}
                                                    </div>
                                                    <div className="alert-item-title-content">
                                                        <div className="alert-item-title-row">
                                                            <h3 className="alert-item-title">{getAlertTitle(alert)}</h3>
                                                            <span className={`alert-item-dot ${severityStyle.dot}`} />
                                                        </div>
                                                        <p className="alert-item-desc">{getAlertMessage(alert)}</p>
                                                    </div>
                                                </div>

                                                {/* Plate */}
                                                <div className="alert-item-col alert-item-plate-col">
                                                    <p className="alert-item-label">Vehicle</p>
                                                    <div className="alert-item-plate">
                                                        <Truck className="alert-item-plate-icon" />
                                                        <span className="alert-item-plate-text">{plate}</span>
                                                    </div>
                                                </div>

                                                {/* Camera */}
                                                <div className="alert-item-col alert-item-camera-col">
                                                    <p className="alert-item-label">Camera</p>
                                                    <div className="alert-item-camera">
                                                        <Camera className="alert-item-camera-icon" />
                                                        <span className="alert-item-camera-text">{getCameraName(alert)}</span>
                                                    </div>
                                                </div>

                                                {/* Time */}
                                                <div className="alert-item-col alert-item-time-col">
                                                    <p className="alert-item-label">Detected</p>
                                                    <div className="alert-item-time">
                                                        <Clock3 className="alert-item-time-icon" />
                                                        <span className="alert-item-time-text">{formatTimeAgo(detectionTime)}</span>
                                                    </div>
                                                </div>

                                                {/* Badges */}
                                                <div className="alert-item-col alert-item-badges-col">
                                                    <span className={`alert-badge ${severityStyle.badge}`}>
                                                        {severity}
                                                    </span>
                                                    <span className={`alert-badge ${getStatusClasses(status)}`}>
                                                        {status}
                                                    </span>
                                                    {/* Expand */}
                                                    <button
                                                        onClick={() => toggleExpand(alert.id)}
                                                        className="alert-expand-btn"
                                                    >
                                                        <Eye style={{ width: '1rem', height: '1rem', color: '#94a3b8' }} />
                                                        {isExpanded ? 'Hide' : 'Details'}
                                                        {isExpanded ? <ChevronUp className="alert-expand-icon" /> : <ChevronDown className="alert-expand-icon" />}
                                                    </button>
                                                </div>
                                            </div>
                                        </div>

                                        {/* EXPANDED DETAILS */}
                                        {isExpanded && (
                                            <div className="alert-expanded">
                                                <div className="alert-expanded-grid">
                                                    {/* Evidence */}
                                                    <div>
                                                        <div className="alert-evidence-box">
                                                            {evidence ? (
                                                                <>
                                                                    <div className="alert-evidence-overlay" />
                                                                    <img
                                                                        src={evidence}
                                                                        alt={`Evidence for ${plate}`}
                                                                        className="alert-evidence-img"
                                                                    />
                                                                    <div className="alert-evidence-label">EVIDENCE_CAM_FEED</div>
                                                                </>
                                                            ) : (
                                                                <div className="alert-no-evidence">
                                                                    <Camera className="alert-no-evidence-icon" />
                                                                    <p className="alert-no-evidence-title">No evidence image</p>
                                                                    <p className="alert-no-evidence-text">No visual feed was attached to this alert record.</p>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Alert information */}
                                                    <div className="alert-detail-card">
                                                        <div className="alert-detail-header">
                                                            <div className="alert-detail-header-icon-box" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#60a5fa' }}>
                                                                <ShieldAlert className="alert-detail-header-icon" />
                                                            </div>
                                                            <h4 className="alert-detail-header-title">Alert Information</h4>
                                                        </div>

                                                        <div className="alert-info-list">
                                                            <div>
                                                                <p className="alert-info-item-label">Alert ID</p>
                                                                <p className="alert-info-item-val val-id">{alert.id || 'Not available'}</p>
                                                            </div>
                                                            <div>
                                                                <p className="alert-info-item-label">Detection time</p>
                                                                <p className="alert-info-item-val val-time">{formatDateTime(detectionTime)}</p>
                                                            </div>
                                                            <div>
                                                                <p className="alert-info-item-label">Severity</p>
                                                                <div style={{ marginTop: '0.5rem' }}>
                                                                    <span className={`alert-badge ${severityStyle.badge}`}>{severity}</span>
                                                                </div>
                                                            </div>
                                                            <div>
                                                                <p className="alert-info-item-label">Description</p>
                                                                <p className="alert-info-item-val val-desc">{getAlertMessage(alert)}</p>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Detection information */}
                                                    <div className="alert-detail-card">
                                                        <div className="alert-detail-header">
                                                            <div className="alert-detail-header-icon-box" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)', color: '#818cf8' }}>
                                                                <MapPin className="alert-detail-header-icon" />
                                                            </div>
                                                            <h4 className="alert-detail-header-title">Detection Details</h4>
                                                        </div>

                                                        <div className="alert-det-list">
                                                            <div className="alert-det-row">
                                                                <span className="alert-det-label">License plate</span>
                                                                <span className="alert-det-val val-plate">{plate}</span>
                                                            </div>
                                                            <div className="alert-det-row">
                                                                <span className="alert-det-label">Camera</span>
                                                                <span className="alert-det-val val-cam">{getCameraName(alert)}</span>
                                                            </div>
                                                            <div className="alert-det-row">
                                                                <span className="alert-det-label">Camera ID</span>
                                                                <span className="alert-det-val val-camid">{alert?.camera_id || camera?.id || 'Not available'}</span>
                                                            </div>
                                                            <div className="alert-det-row">
                                                                <span className="alert-det-label">Location</span>
                                                                <span className="alert-det-val val-loc">{camera?.location || camera?.road_name || camera?.address || 'Not available'}</span>
                                                            </div>
                                                            <div className="alert-det-row">
                                                                <span className="alert-det-label">OCR confidence</span>
                                                                <span className="alert-det-val val-conf">
                                                                    {alert?.confidence != null ? (
                                                                        <>
                                                                            <span className="conf-bar-bg">
                                                                                <div className="conf-bar-fill" style={{ width: `${Number(alert.confidence) * 100}%` }} />
                                                                            </span>
                                                                            {(Number(alert.confidence) * 100).toFixed(1)}%
                                                                        </>
                                                                    ) : 'Not available'}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Investigation footer */}
                                                <div className="alert-inv-footer">
                                                    <div className="alert-inv-content">
                                                        <div className="alert-inv-left">
                                                            <div className="alert-inv-icon-box">
                                                                <Timer className="alert-inv-icon" />
                                                            </div>
                                                            <div>
                                                                <h4 className="alert-inv-title">Investigation Status</h4>
                                                                <p className="alert-inv-desc">Update the operational workflow state of this security alert.</p>
                                                            </div>
                                                        </div>

                                                        <div className="alert-inv-right">
                                                            <span className={`alert-badge ${getStatusClasses(status)}`}>
                                                                Current: {status}
                                                            </span>

                                                            <div className="alert-status-select-wrapper">
                                                                <select
                                                                    value={status}
                                                                    disabled={updatingAlertId === alert.id}
                                                                    onChange={(event) => handleStatusChange(alert.id, event.target.value)}
                                                                    className="alert-status-select"
                                                                >
                                                                    <option value="New">New</option>
                                                                    <option value="Acknowledged">Acknowledged</option>
                                                                    <option value="Investigating">Investigating</option>
                                                                    <option value="Resolved">Resolved</option>
                                                                    <option value="Dismissed">Dismissed</option>
                                                                </select>
                                                                <ChevronDown className="alert-status-icon" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </article>
                                );
                            })}
                        </div>
                    )}
                </section>

                {/* FOOTER */}
                <div className="alerts-footer">
                    <div className="alerts-footer-left">
                        <Activity className="alerts-footer-icon" />
                        <span>Advanced ANPR Monitoring System v2.0</span>
                    </div>
                    <div>{filteredAlerts.length} visible alerts in current view</div>
                </div>
            </main>
        </div>
    );
};

export default AlertsPage;
export { AlertsPage };