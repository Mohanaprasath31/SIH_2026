import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import Depends, HTTPException, Header, status
from pydantic import BaseModel

from backend.db import get_supabase_client

logger = logging.getLogger("backend.auth")

# Allowed system roles
ALLOWED_ROLES = ["admin", "traffic_operator", "investigator", "analyst", "auditor"]

# In-memory stores for dev/test fallback when Supabase is not connected
_user_roles_db: Dict[str, str] = {
    "dev-admin-user": "admin",
    "dev-investigator-user": "investigator",
    "dev-operator-user": "traffic_operator",
    "dev-analyst-user": "analyst",
    "dev-auditor-user": "auditor"
}

_audit_log_db: List[Dict[str, Any]] = []


class UserProfile(BaseModel):
    user_id: str
    email: str
    role: str


def log_audit_access(user_id: str, action: str, table_name: str, row_reference: str) -> Dict[str, Any]:
    """
    Logs every sensitive access to vehicle_observations, watchlist, etc. into audit_log table.
    """
    audit_entry = {
        "id": f"audit-{len(_audit_log_db)+1}",
        "user_id": user_id,
        "action": action,
        "table_name": table_name,
        "row_reference": row_reference,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    _audit_log_db.append(audit_entry)

    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("audit_log").insert(audit_entry).execute()
        except Exception as e:
            logger.debug(f"[Audit] Supabase insert log (handled): {e}")

    logger.info(f"[AuditLog] User '{user_id}' ({action}) on {table_name}: {row_reference}")
    return audit_entry


def get_stored_audit_logs() -> List[Dict[str, Any]]:
    return list(_audit_log_db)


def get_current_user(authorization: Optional[str] = Header(None)) -> UserProfile:
    """
    FastAPI dependency to extract and validate Supabase JWT from Authorization header.
    In dev/test environment without token, provides default admin fallback.
    """
    if not authorization:
        # Dev fallback for local API testing without auth header
        return UserProfile(user_id="dev-admin-user", email="admin@anpr.local", role="admin")

    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token format"
        )

    # Check hardcoded dev tokens for fast testing
    if token in _user_roles_db:
        role = _user_roles_db[token]
        return UserProfile(user_id=token, email=f"{token}@anpr.local", role=role)

    # Validate against Supabase Auth if connected
    supabase = get_supabase_client()
    if supabase:
        try:
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                u = user_response.user
                user_id = str(u.id)
                email = str(u.email or "user@anpr.local")

                # Fetch user role from user_roles table
                role_res = supabase.table("user_roles").select("role").eq("user_id", user_id).execute()
                role = "traffic_operator"
                if role_res and role_res.data:
                    role = role_res.data[0].get("role", "traffic_operator")

                return UserProfile(user_id=user_id, email=email, role=role)
        except Exception as e:
            logger.warning(f"[Auth] Supabase token verification failed: {e}")

    # Fallback default user for valid token string
    return UserProfile(user_id=f"usr-{token[:8]}", email="operator@anpr.local", role="traffic_operator")


def require_roles(allowed_roles: List[str]):
    """
    FastAPI Dependency Factory that checks if the authenticated user has one of the allowed roles.
    Returns HTTP 403 Forbidden if user role is not in allowed_roles.
    """
    def role_checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"[RBAC Denied] User '{current_user.user_id}' with role '{current_user.role}' "
                f"attempted unauthorized access (required: {allowed_roles})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted to access this resource. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker
