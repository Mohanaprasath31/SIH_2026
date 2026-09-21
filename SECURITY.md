# ANPR Surveillance System Security Architecture

## Authentication & Access Control
- **Supabase Auth & JWT Validation**: Authenticates users using JWT bearer tokens verified on protected API endpoints (`backend/auth.py`).
- **Role-Based Access Control (RBAC)**: Enforces role permissions across system components. Allowed roles: `admin`, `traffic_operator`, `investigator`, `analyst`, `auditor`.
- **Row-Level Security (RLS)**: Postgres RLS policies in `backend/schema_security.sql` enforce granular database-level access constraints per role.
- **Audit Logging**: Sensitive reads on `vehicle_observations` and `trajectories` are recorded in `audit_log` with timestamp, user ID, and query reference.

## Transport Layer Security (HTTPS/TLS)
> [!NOTE]
> HTTPS/TLS termination occurs at the hosting/reverse-proxy layer (e.g., Nginx, Traefik, AWS ALB, Cloudflare) upon deployment into production environments. SSL certificates and TLS configuration are managed externally at the edge/gateway layer rather than inside the application dev server.
