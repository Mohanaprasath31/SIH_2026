from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends

from backend.db import get_supabase_client
from backend.models import WatchlistCreate, WatchlistResponse
from backend.auth import require_roles, UserProfile
from backend.demo_data import WATCHLIST

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=List[WatchlistResponse])
def get_watchlist(
    current_user: UserProfile = Depends(require_roles(["investigator", "traffic_operator", "admin"]))
):
    """
    GET /watchlist
    Retrieves all active and historical watchlist plates.
    Restricted to investigator, traffic_operator, and admin roles.
    """
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("watchlist").select("*").execute()
            if res.data and len(res.data) > 0:
                return res.data
        except Exception as e:
            print(f"[!] Supabase watchlist fetch error: {e}")

    return WATCHLIST[:5]


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: WatchlistCreate,
    current_user: UserProfile = Depends(require_roles(["admin"]))
):
    """
    POST /watchlist
    Adds or updates a license plate entry on the surveillance watchlist.
    Restricted to ADMIN role ONLY.
    """

    plate_norm = payload.plate_number.strip().upper()
    now_iso = datetime.now().isoformat()

    record = {
        "plate_number": plate_norm,
        "category": payload.category,
        "priority": payload.priority,
        "status": payload.status or "Active",
        "validity": payload.validity,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("watchlist").upsert(record).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            print(f"[!] Supabase watchlist insert error: {e}")

    # Return created/updated record
    return WatchlistResponse(**record)
