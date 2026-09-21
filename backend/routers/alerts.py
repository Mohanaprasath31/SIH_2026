from typing import List, Optional

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

from backend.db import get_supabase_client
from backend.models import AlertResponse
from backend.auth import require_roles, UserProfile
from backend.demo_data import ALERTS


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class AlertStatusUpdate(BaseModel):
    status: str


# ============================================================
# ALLOWED ALERT STATUSES
# ============================================================

ALLOWED_STATUSES = {
    "New",
    "Acknowledged",
    "Investigating",
    "Resolved",
    "Dismissed"
}


# ============================================================
# GET ALERTS
# ============================================================

@router.get(
    "",
    response_model=List[AlertResponse]
)
def get_alerts(
    status: Optional[str] = Query(
        None,
        description=(
            "Filter by status "
            "(New, Acknowledged, Investigating, Resolved, Dismissed)"
        )
    ),
    severity: Optional[str] = Query(
        None,
        description=(
            "Filter by severity "
            "(Critical, High, Medium, Low)"
        )
    ),
    current_user: UserProfile = Depends(
        require_roles(
            [
                "investigator",
                "traffic_operator",
                "admin"
            ]
        )
    )
):

    """
    GET /alerts

    Retrieves system security and ANPR traffic surveillance
    alerts from Supabase.
    """

    supabase = get_supabase_client()

    if supabase:

        try:

            query = (
                supabase
                .table("alerts")
                .select("*")
                .order("timestamp", desc=True)
            )

            if status:
                query = query.eq(
                    "status",
                    status
                )

            if severity:
                query = query.eq(
                    "severity",
                    severity
                )

            res = query.execute()

            if res.data:
                return res.data

        except Exception as e:

            print(
                f"[!] Supabase alerts fetch error: {e}"
            )


    # --------------------------------------------------------
    # Fallback demo data
    # --------------------------------------------------------

    demo_alerts = ALERTS[:5]

    if status:

        demo_alerts = [
            alert
            for alert in demo_alerts
            if alert["status"].lower()
            == status.lower()
        ]

    if severity:

        demo_alerts = [
            alert
            for alert in demo_alerts
            if alert["severity"].lower()
            == severity.lower()
        ]

    return demo_alerts


# ============================================================
# UPDATE ALERT STATUS
# ============================================================

@router.patch(
    "/{alert_id}/status"
)
def update_alert_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    current_user: UserProfile = Depends(
        require_roles(
            [
                "investigator",
                "traffic_operator",
                "admin"
            ]
        )
    )
):

    """
    PATCH /alerts/{alert_id}/status

    Updates the lifecycle status of an alert.

    Allowed statuses:

        New
        Acknowledged
        Investigating
        Resolved
        Dismissed
    """

    # --------------------------------------------------------
    # Validate status
    # --------------------------------------------------------

    new_status = payload.status.strip()

    if new_status not in ALLOWED_STATUSES:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid alert status",
                "allowed_statuses": sorted(
                    ALLOWED_STATUSES
                )
            }
        )


    # --------------------------------------------------------
    # Connect to Supabase
    # --------------------------------------------------------

    supabase = get_supabase_client()

    if not supabase:

        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable."
        )


    # --------------------------------------------------------
    # Verify alert exists
    # --------------------------------------------------------

    try:

        existing = (
            supabase
            .table("alerts")
            .select("*")
            .eq("alert_id", alert_id)
            .limit(1)
            .execute()
        )

    except Exception as e:

        print(
            f"[!] Alert lookup error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve alert."
        )


    if not existing.data:

        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found."
        )


    # --------------------------------------------------------
    # Update status
    # --------------------------------------------------------

    try:

        updated = (
            supabase
            .table("alerts")
            .update({
                "status": new_status
            })
            .eq("alert_id", alert_id)
            .execute()
        )

    except Exception as e:

        print(
            f"[!] Alert status update error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to update alert status."
        )


    if not updated.data:

        raise HTTPException(
            status_code=500,
            detail="Alert status update returned no data."
        )


    # --------------------------------------------------------
    # Return updated alert
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": (
            f"Alert status updated to "
            f"'{new_status}'."
        ),
        "alert": updated.data[0]
    }