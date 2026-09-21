import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const Layout = () => {
    return (
        <div className="app-layout">
            {/* Sidebar Navigation Shell */}
            <Sidebar />

            {/* Main Content Area */}
            <div className="main-content">
                {/* Top Operational Header */}
                <Header />

                {/* Page Content Viewport */}
                <main className="page-viewport">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};
