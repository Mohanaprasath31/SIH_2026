import sys
from pathlib import Path
from fastapi import HTTPException

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.auth import (
    get_current_user,
    require_roles,
    log_audit_access,
    get_stored_audit_logs,
    UserProfile
)
from backend.routers.watchlist import add_to_watchlist
from backend.models import WatchlistCreate


def test_jwt_user_validation():
    """
    Tests JWT / token extraction and user profile construction.
    """
    print("[TEST] Running test_jwt_user_validation...")
    user_admin = get_current_user(authorization="Bearer dev-admin-user")
    assert user_admin.role == "admin"
    assert user_admin.user_id == "dev-admin-user"

    user_investigator = get_current_user(authorization="Bearer dev-investigator-user")
    assert user_investigator.role == "investigator"
    assert user_investigator.user_id == "dev-investigator-user"

    user_analyst = get_current_user(authorization="Bearer dev-analyst-user")
    assert user_analyst.role == "analyst"
    assert user_analyst.user_id == "dev-analyst-user"

    print("  [SUCCESS] JWT token validation and user profile role resolution verified.")


def test_rbac_authorization_rules():
    """
    Tests RBAC role permission enforcement.
    Allows permitted roles and raises HTTP 403 Forbidden for unpermitted roles.
    """
    print("[TEST] Running test_rbac_authorization_rules...")
    admin_checker = require_roles(["admin"])
    investigator_checker = require_roles(["investigator", "admin"])

    admin_user = UserProfile(user_id="u-admin", email="admin@anpr.local", role="admin")
    analyst_user = UserProfile(user_id="u-analyst", email="analyst@anpr.local", role="analyst")
    investigator_user = UserProfile(user_id="u-investigator", email="inv@anpr.local", role="investigator")

    # Admin allowed for admin_checker
    res = admin_checker(admin_user)
    assert res.role == "admin"

    # Analyst blocked (403) for admin_checker
    try:
        admin_checker(analyst_user)
        assert False, "Analyst role should have raised 403 Forbidden for admin requirement"
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  [SUCCESS] Analyst role correctly returned HTTP 403: {e.detail}")

    # Investigator allowed for investigator_checker
    res_inv = investigator_checker(investigator_user)
    assert res_inv.role == "investigator"

    # Analyst blocked (403) for investigator_checker
    try:
        investigator_checker(analyst_user)
        assert False, "Analyst role should have raised 403 Forbidden for investigator requirement"
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  [SUCCESS] Analyst role correctly blocked from vehicle search: {e.detail}")


def test_audit_logging():
    """
    Verifies that sensitive data accesses are logged to the audit log.
    """
    print("[TEST] Running test_audit_logging...")
    initial_count = len(get_stored_audit_logs())

    entry = log_audit_access(
        user_id="dev-investigator-user",
        action="SELECT",
        table_name="vehicle_observations",
        row_reference="plate:TN01AX9912"
    )

    logs = get_stored_audit_logs()
    assert len(logs) == initial_count + 1
    assert logs[-1]["user_id"] == "dev-investigator-user"
    assert logs[-1]["table_name"] == "vehicle_observations"
    assert logs[-1]["row_reference"] == "plate:TN01AX9912"
    print("  [SUCCESS] Audit logging entry verified.")


def main():
    print("=" * 60)
    print("RUNNING BACKEND SECURITY & RBAC TEST SUITE")
    print("=" * 60)
    test_jwt_user_validation()
    test_rbac_authorization_rules()
    test_audit_logging()
    print("=" * 60)
    print("ALL SECURITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
