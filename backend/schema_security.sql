-- ============================================================================
-- ANPR TRAFFIC SURVEILLANCE - SECURITY SCHEMA & RLS POLICIES
-- ============================================================================

-- 1. USER ROLES TABLE
CREATE TABLE IF NOT EXISTS public.user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'traffic_operator', 'investigator', 'analyst', 'auditor')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Helper function to fetch current authenticated user's role
CREATE OR REPLACE FUNCTION public.get_current_user_role()
RETURNS TEXT AS $$
DECLARE
    user_role TEXT;
BEGIN
    SELECT role INTO user_role FROM public.user_roles WHERE user_id = auth.uid();
    RETURN COALESCE(user_role, 'traffic_operator');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 2. AUDIT LOG TABLE
CREATE TABLE IF NOT EXISTS public.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    row_reference TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 3. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all sensitive tables
ALTER TABLE public.vehicle_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trajectories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cameras ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hourly_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- POLICIES: vehicle_observations & trajectories
-- Allowed: investigator, admin
-- ----------------------------------------------------------------------------
CREATE POLICY "Investigator & Admin read vehicle_observations" ON public.vehicle_observations
    FOR SELECT USING (public.get_current_user_role() IN ('investigator', 'admin'));

CREATE POLICY "Investigator & Admin read trajectories" ON public.trajectories
    FOR SELECT USING (public.get_current_user_role() IN ('investigator', 'admin'));

-- ----------------------------------------------------------------------------
-- POLICIES: cameras & hourly_analytics
-- Allowed: analyst, traffic_operator, admin
-- ----------------------------------------------------------------------------
CREATE POLICY "Analyst, Operator & Admin read cameras" ON public.cameras
    FOR SELECT USING (public.get_current_user_role() IN ('analyst', 'traffic_operator', 'admin'));

CREATE POLICY "Analyst, Operator & Admin read hourly_analytics" ON public.hourly_analytics
    FOR SELECT USING (public.get_current_user_role() IN ('analyst', 'traffic_operator', 'admin'));

-- ----------------------------------------------------------------------------
-- POLICIES: watchlist & alerts
-- SELECT Allowed: investigator, traffic_operator, admin
-- INSERT/UPDATE watchlist Allowed: admin ONLY
-- ----------------------------------------------------------------------------
CREATE POLICY "Investigator, Operator & Admin read watchlist" ON public.watchlist
    FOR SELECT USING (public.get_current_user_role() IN ('investigator', 'traffic_operator', 'admin'));

CREATE POLICY "Admin write watchlist" ON public.watchlist
    FOR ALL USING (public.get_current_user_role() = 'admin');

CREATE POLICY "Investigator, Operator & Admin read alerts" ON public.alerts
    FOR SELECT USING (public.get_current_user_role() IN ('investigator', 'traffic_operator', 'admin'));

-- ----------------------------------------------------------------------------
-- POLICIES: audit_log
-- SELECT Allowed: auditor, admin ONLY
-- ----------------------------------------------------------------------------
CREATE POLICY "Auditor & Admin read audit_log" ON public.audit_log
    FOR SELECT USING (public.get_current_user_role() IN ('auditor', 'admin'));

-- ============================================================================
-- AUDIT LOG TRIGGER FUNCTION ON vehicle_observations
-- ============================================================================
CREATE OR REPLACE FUNCTION public.log_vehicle_observation_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.audit_log(user_id, action, table_name, row_reference, timestamp)
    VALUES (
        COALESCE(auth.uid()::text, 'system'),
        'SELECT',
        'vehicle_observations',
        NEW.plate_number,
        now()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
