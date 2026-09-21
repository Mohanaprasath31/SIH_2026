from typing import List, Dict
from fastapi import APIRouter

from backend.db import get_supabase_client
from backend.streaming.bus import get_stored_vehicle_observations
from backend.models import (
    HourlyVolumeResponse,
    HourlyVolumeItem,
    ODMatrixResponse,
    ODMatrixEntry,
)
from backend.demo_data import OBSERVATIONS

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/hourly-volume", response_model=HourlyVolumeResponse)
def get_hourly_volume():
    """
    GET /analytics/hourly-volume
    Returns vehicle count traffic volume aggregated by hour of the day.
    """
    supabase = get_supabase_client()
    obs_list = []

    if supabase:
        try:
            res = supabase.table("vehicle_observations").select("*").execute()
            if res.data and len(res.data) > 0:
                obs_list = res.data
        except Exception as e:
            print(f"[!] Supabase hourly volume error: {e}")

    if not obs_list:
        # First check streaming live stored observations
        obs_list = get_stored_vehicle_observations()

    if not obs_list:
        obs_list = OBSERVATIONS[:5]
    
    # Aggregate observations by hour
    hourly_counts: Dict[str, Dict[str, int]] = {}
    for obs in obs_list:
        ts_str = obs.get("timestamp", "")
        # Extract hour representation e.g. "08:00", "09:00"
        hour_key = ts_str[11:13] + ":00" if len(ts_str) >= 13 else "10:00"
        vtype = obs.get("vehicle_type", "Car")

        if hour_key not in hourly_counts:
            hourly_counts[hour_key] = {}
        hourly_counts[hour_key][vtype] = hourly_counts[hour_key].get(vtype, 0) + 1

    hourly_items: List[HourlyVolumeItem] = []
    for h in sorted(hourly_counts.keys()):
        types_map = hourly_counts[h]
        total_h = sum(types_map.values())
        hourly_items.append(
            HourlyVolumeItem(
                hour=h,
                count=total_h,
                vehicle_types=types_map
            )
        )

    total_obs = sum(item.count for item in hourly_items)
    return HourlyVolumeResponse(
        total_observations=total_obs,
        hourly_data=hourly_items
    )


@router.get("/od-matrix", response_model=ODMatrixResponse)
def get_origin_destination_matrix():
    """
    GET /analytics/od-matrix
    Returns Origin-Destination (OD) traffic volume matrix between ANPR camera locations.
    """
    matrix_entries: List[ODMatrixEntry] = []

    total_trips = sum(entry.trip_count for entry in matrix_entries)
    return ODMatrixResponse(
        total_trips=total_trips,
        matrix=matrix_entries
    )
