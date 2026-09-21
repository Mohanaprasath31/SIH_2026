import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { setAuthToken } from '../api/client';

export const LoginPage = () => {
    const [email, setEmail] = useState('operator@anpr.tn.gov.in');
    const [password, setPassword] = useState('••••••••••••');
    const [role, setRole] = useState('admin');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const handleLogin = (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');

        setTimeout(() => {
            // Store session token and role in localStorage
            const token = `dev-${role}-user`;
            setAuthToken(token);
            localStorage.setItem('user_role', role);
            localStorage.setItem('user_email', email);

            setLoading(false);
            setMessage(`Successfully authenticated as ${role.toUpperCase()}`);

            setTimeout(() => {
                navigate('/dashboard');
            }, 600);
        }, 500);
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <div style={styles.header}>
                    <div style={styles.badge}>SECURE CONTROL ROOM</div>
                    <h1 style={styles.title}>ANPR Surveillance Access</h1>
                    <p style={styles.subtitle}>Sign in via Supabase Authentication & Role Validation</p>
                </div>

                <form onSubmit={handleLogin} style={styles.form}>
                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Email Address</label>
                        <input
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            style={styles.input}
                            placeholder="operator@anpr.tn.gov.in"
                        />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={styles.input}
                            placeholder="••••••••"
                        />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Assigned System Role (RBAC)</label>
                        <select
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            style={styles.select}
                        >
                            <option value="admin">Administrator (Full Access)</option>
                            <option value="investigator">Investigator (Vehicles, Trajectories, Alerts)</option>
                            <option value="traffic_operator">Traffic Operator (Cameras, Alerts, Map)</option>
                            <option value="analyst">Data Analyst (Analytics & Cameras)</option>
                            <option value="auditor">Auditor (Audit Log & Security)</option>
                        </select>
                    </div>

                    {message && <div style={styles.alertSuccess}>{message}</div>}

                    <button type="submit" disabled={loading} style={styles.button}>
                        {loading ? 'AUTHENTICATING...' : 'SIGN IN TO CONTROL ROOM'}
                    </button>
                </form>
            </div>
        </div>
    );
};

const styles = {
    container: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#070a12',
        color: '#e2e8f0',
        fontFamily: "'Inter', sans-serif",
    },
    card: {
        width: '100%',
        maxWidth: '440px',
        padding: '2.5rem',
        backgroundColor: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: '12px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(56, 189, 248, 0.1)',
    },
    header: {
        textAlign: 'center',
        marginBottom: '2rem',
    },
    badge: {
        display: 'inline-block',
        padding: '0.25rem 0.75rem',
        fontSize: '0.7rem',
        fontWeight: '700',
        letterSpacing: '1px',
        color: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.1)',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        borderRadius: '9999px',
        marginBottom: '0.75rem',
    },
    title: {
        fontSize: '1.5rem',
        fontWeight: '800',
        color: '#f8fafc',
        margin: '0 0 0.5rem 0',
    },
    subtitle: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        margin: 0,
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
    },
    inputGroup: {
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
    },
    label: {
        fontSize: '0.8rem',
        fontWeight: '600',
        color: '#cbd5e1',
        letterSpacing: '0.5px',
    },
    input: {
        padding: '0.75rem 1rem',
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '6px',
        color: '#f8fafc',
        fontSize: '0.95rem',
        outline: 'none',
    },
    select: {
        padding: '0.75rem 1rem',
        backgroundColor: '#1e293b',
        border: '1px solid #38bdf8',
        borderRadius: '6px',
        color: '#f8fafc',
        fontSize: '0.9rem',
        outline: 'none',
        cursor: 'pointer',
    },
    button: {
        marginTop: '0.5rem',
        padding: '0.875rem',
        backgroundColor: '#0284c7',
        color: '#ffffff',
        fontWeight: '700',
        fontSize: '0.9rem',
        letterSpacing: '0.5px',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)',
    },
    alertSuccess: {
        padding: '0.75rem',
        backgroundColor: 'rgba(16, 185, 129, 0.15)',
        border: '1px solid rgba(16, 185, 129, 0.4)',
        color: '#34d399',
        borderRadius: '6px',
        fontSize: '0.85rem',
        textAlign: 'center',
    }
};

export default LoginPage;
