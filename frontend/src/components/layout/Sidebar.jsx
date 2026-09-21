import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Map,
    Search,
    Navigation,
    BarChart3,
    ShieldAlert,
    Radio,
    ChevronRight,
} from 'lucide-react';

const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Surveillance Map', path: '/map', icon: Map, badge: 'LIVE' },
    { name: 'Plate Search', path: '/search', icon: Search },
    { name: 'Vehicle Trajectory', path: '/trajectory', icon: Navigation },
    { name: 'Traffic Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Security Alerts', path: '/alerts', icon: ShieldAlert, badge: '5' },
];

export const Sidebar = () => {
    return (
        <aside className="ops-sidebar">
            <div>
                {/* Brand Header */}
                <div className="sidebar-header">
                    <div className="sidebar-brand-icon">
                        <Radio size={20} />
                    </div>
                    <div>
                        <h2 className="sidebar-brand-title">
                            TRAFFIC <span>INTELLIGENCE</span>
                        </h2>
                        <p className="sidebar-brand-sub">SECURITY COMMAND CENTRE</p>
                    </div>
                </div>

                {/* Navigation Items */}
                <nav className="sidebar-nav">
                    <div className="nav-section-title">Operations Modules</div>

                    {navItems.map((item) => {
                        const Icon = item.icon;
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) =>
                                    `nav-item ${isActive ? 'active' : ''}`
                                }
                            >
                                {({ isActive }) => (
                                    <>
                                        <div className="nav-item-left">
                                            <Icon
                                                size={16}
                                                style={{ color: isActive ? '#1f4e79' : 'inherit' }}
                                            />
                                            <span>{item.name}</span>
                                        </div>

                                        <div className="nav-item-right">
                                            {item.badge && (
                                                <span
                                                    style={{
                                                        fontSize: '10px',
                                                        fontFamily: 'var(--font-mono)',
                                                        fontWeight: 700,
                                                        padding: '2px 6px',
                                                        borderRadius: '4px',
                                                        backgroundColor: item.badge === 'LIVE' ? 'var(--alert-success-bg)' : 'var(--alert-critical-bg)',
                                                        color: item.badge === 'LIVE' ? 'var(--alert-success)' : 'var(--alert-critical)',
                                                        border: item.badge === 'LIVE' ? '1px solid var(--alert-success-border)' : '1px solid var(--alert-critical-border)'
                                                    }}
                                                >
                                                    {item.badge}
                                                </span>
                                            )}
                                            {isActive && <ChevronRight size={14} color="#1f4e79" />}
                                        </div>
                                    </>
                                )}
                            </NavLink>
                        );
                    })}
                </nav>
            </div>

            {/* Footer System Status Badge */}
            <div className="sidebar-footer">
                <div className="sidebar-footer-info">
                    <span>FASTAPI BACKEND</span>
                    <span style={{ color: '#06b6d4', fontWeight: 600 }}>:8000</span>
                </div>
                <div className="sidebar-footer-progress">
                    <div className="sidebar-footer-bar" />
                </div>
            </div>
        </aside>
    );
};
