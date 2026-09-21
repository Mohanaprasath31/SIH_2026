/**
 * ANPR Traffic Surveillance Dashboard - API Client
 * Communicates with FastAPI backend running at http://localhost:8000
 */

const BASE_URL = 'http://localhost:8000';

/**
 * Gets active auth token from localStorage.
 * @returns {string|null}
 */
export function getAuthToken() {
    return localStorage.getItem('supabase_token') || localStorage.getItem('access_token') || 'dev-admin-user';
}

/**
 * Sets auth token in localStorage.
 * @param {string} token 
 */
export function setAuthToken(token) {
    if (token) {
        localStorage.setItem('supabase_token', token);
    } else {
        localStorage.removeItem('supabase_token');
    }
}

/**
 * Generic fetch wrapper for FastAPI backend attaching Authorization header
 * @param {string} path 
 * @param {RequestInit} [options] 
 * @returns {Promise<any>}
 */
async function fetchApi(path, options = {}) {
    const url = `${BASE_URL}${path}`;
    const token = getAuthToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const response = await fetch(url, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown API Error');
        throw new Error(`API Request Failed [${response.status} ${response.statusText}]: ${errorText}`);
    }

    return response.json();
}

/**
 * GET /health
 */
export async function getHealth() {
    return fetchApi('/health');
}

/**
 * GET /cameras
 */
export async function getCameras() {
    return fetchApi('/cameras');
}

/**
 * GET /cameras/{id}/health
 */
export async function getCameraHealth(id) {
    return fetchApi(`/cameras/${encodeURIComponent(id)}/health`);
}

/**
 * GET /vehicles/search?plate=
 */
export async function searchVehicles(plate) {
    return fetchApi(`/vehicles/search?plate=${encodeURIComponent(plate)}`);
}

/**
 * GET /vehicles/{id}/trajectory
 */
export async function getVehicleTrajectory(id) {
    return fetchApi(`/vehicles/${encodeURIComponent(id)}/trajectory`);
}

/**
 * GET /alerts
 */
export async function getAlerts(params = {}) {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status', params.status);
    if (params.severity) queryParams.append('severity', params.severity);

    const queryString = queryParams.toString();
    const path = queryString ? `/alerts?${queryString}` : '/alerts';
    return fetchApi(path);
}
/**
 * PATCH /alerts/{alert_id}/status
 */
export async function updateAlertStatus(alertId, status) {
    return fetchApi(
        `/alerts/${encodeURIComponent(alertId)}/status`,
        {
            method: 'PATCH',
            body: JSON.stringify({
                status,
            }),
        }
    );
}
/**
 * GET /analytics/hourly-volume
 */
export async function getHourlyVolume() {
    return fetchApi('/analytics/hourly-volume');
}

/**
 * GET /analytics/od-matrix
 */
export async function getODMatrix() {
    return fetchApi('/analytics/od-matrix');
}

/**
 * POST /watchlist
 */
export async function addToWatchlist(payload) {
    return fetchApi('/watchlist', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}
