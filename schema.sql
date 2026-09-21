-- ANPR Traffic Surveillance System Database Schema
-- Target Database: Supabase (PostgreSQL 15+ with PostGIS)

-- Enable PostGIS extension for spatial geography support
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CAMERAS TABLE
-- Stores ANPR camera installations, location coordinates (PostGIS Point), road, zone, & status.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.cameras (
    camera_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    road VARCHAR(255) NOT NULL,
    direction VARCHAR(50) NOT NULL,
    zone VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'offline')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. VEHICLE OBSERVATIONS TABLE
-- Stores real-time ANPR camera detections/reads including plate numbers, location, & OCR confidence.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.vehicle_observations (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES public.cameras(camera_id) ON DELETE CASCADE,
    plate_number VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    ocr_confidence DOUBLE PRECISION NOT NULL CHECK (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0),
    vehicle_type VARCHAR(50) NOT NULL,
    direction VARCHAR(50) NOT NULL,
    image_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. VEHICLES TABLE
-- Master repository of unique normalized vehicle plates tracked across the network.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_plate VARCHAR(20) UNIQUE NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. TRAJECTORIES TABLE
-- Represents mapped trips/routes taken by vehicles across sequences of ANPR cameras.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.trajectories (
    trajectory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES public.vehicles(vehicle_id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    camera_sequence UUID[] NOT NULL,
    distance DOUBLE PRECISION NOT NULL, -- Distance in kilometers
    duration DOUBLE PRECISION NOT NULL, -- Duration in seconds
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. TRAJECTORY POINTS TABLE
-- Waypoints along a specific vehicle trajectory recorded at camera checkpoints.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.trajectory_points (
    point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trajectory_id UUID NOT NULL REFERENCES public.trajectories(trajectory_id) ON DELETE CASCADE,
    camera_id UUID REFERENCES public.cameras(camera_id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. WATCHLIST TABLE
-- High-priority license plates flagged for surveillance, stolen status, or offenses.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.watchlist (
    plate_number VARCHAR(20) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('High', 'Medium', 'Low', 'Critical')),
    status VARCHAR(50) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Resolved', 'Expired')),
    validity TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 7. ALERTS TABLE
-- Real-time security and traffic alerts generated upon watchlist hits or anomalies.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plate_number VARCHAR(20) NOT NULL,
    camera_id UUID REFERENCES public.cameras(camera_id) ON DELETE SET NULL,
    alert_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('Critical', 'High', 'Medium', 'Low')),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    status VARCHAR(50) NOT NULL DEFAULT 'New' CHECK (status IN ('New', 'Acknowledged', 'Investigating', 'Resolved', 'Dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- Optimize lookups on plate_number, camera_id, timestamp, and PostGIS geography.
-- ============================================================================

-- Cameras Table Indexes
CREATE INDEX IF NOT EXISTS idx_cameras_location ON public.cameras USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_cameras_road ON public.cameras (road);
CREATE INDEX IF NOT EXISTS idx_cameras_zone ON public.cameras (zone);
CREATE INDEX IF NOT EXISTS idx_cameras_status ON public.cameras (status);

-- Vehicle Observations Table Indexes
CREATE INDEX IF NOT EXISTS idx_obs_plate_number ON public.vehicle_observations (plate_number);
CREATE INDEX IF NOT EXISTS idx_obs_camera_id ON public.vehicle_observations (camera_id);
CREATE INDEX IF NOT EXISTS idx_obs_timestamp ON public.vehicle_observations (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_obs_plate_timestamp ON public.vehicle_observations (plate_number, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_obs_location ON public.vehicle_observations USING GIST (location);

-- Vehicles Table Indexes
CREATE INDEX IF NOT EXISTS idx_vehicles_normalized_plate ON public.vehicles (normalized_plate);
CREATE INDEX IF NOT EXISTS idx_vehicles_first_seen ON public.vehicles (first_seen);
CREATE INDEX IF NOT EXISTS idx_vehicles_last_seen ON public.vehicles (last_seen DESC);

-- Trajectories Table Indexes
CREATE INDEX IF NOT EXISTS idx_trajectories_vehicle_id ON public.trajectories (vehicle_id);
CREATE INDEX IF NOT EXISTS idx_trajectories_start_time ON public.trajectories (start_time DESC);
CREATE INDEX IF NOT EXISTS idx_trajectories_end_time ON public.trajectories (end_time DESC);

-- Trajectory Points Table Indexes
CREATE INDEX IF NOT EXISTS idx_traj_pts_trajectory_id ON public.trajectory_points (trajectory_id);
CREATE INDEX IF NOT EXISTS idx_traj_pts_camera_id ON public.trajectory_points (camera_id);
CREATE INDEX IF NOT EXISTS idx_traj_pts_timestamp ON public.trajectory_points (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_traj_pts_location ON public.trajectory_points USING GIST (location);

-- Watchlist Table Indexes
CREATE INDEX IF NOT EXISTS idx_watchlist_category ON public.watchlist (category);
CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON public.watchlist (priority);
CREATE INDEX IF NOT EXISTS idx_watchlist_status ON public.watchlist (status);

-- Alerts Table Indexes
CREATE INDEX IF NOT EXISTS idx_alerts_plate_number ON public.alerts (plate_number);
CREATE INDEX IF NOT EXISTS idx_alerts_camera_id ON public.alerts (camera_id);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON public.alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON public.alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON public.alerts (status);
