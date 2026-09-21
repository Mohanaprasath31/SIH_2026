from typing import List
import re
import struct

from fastapi import APIRouter, Query, Depends, HTTPException

from backend.db import get_supabase_client
from backend.models import (
    VehicleSearchResponse,
    TrajectoryResponse,
)
from backend.auth import require_roles, log_audit_access, UserProfile
from backend.demo_data import OBSERVATIONS


router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


# ============================================================
# POSTGIS LOCATION PARSER
# ============================================================

def parse_postgis_point(location):
    """
    Convert a PostGIS location into GeoJSON-style Point data.

    Supported formats:

    1. GeoJSON:
       {
           "type": "Point",
           "coordinates": [longitude, latitude]
       }

    2. WKT:
       POINT(longitude latitude)

    3. PostGIS EWKB hexadecimal:
       0101000020E6100000...
    """

    if not location:
        return location

    # --------------------------------------------------------
    # Already GeoJSON
    # --------------------------------------------------------

    if isinstance(location, dict):

        if (
            location.get("type") == "Point"
            and isinstance(
                location.get("coordinates"),
                list
            )
        ):
            return location

    # --------------------------------------------------------
    # String formats
    # --------------------------------------------------------

    if isinstance(location, str):

        # ----------------------------------------------------
        # WKT POINT
        # ----------------------------------------------------

        match = re.match(
            r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)",
            location,
            re.IGNORECASE
        )

        if match:

            return {
                "type": "Point",
                "coordinates": [
                    float(match.group(1)),
                    float(match.group(2))
                ]
            }

        # ----------------------------------------------------
        # PostGIS EWKB hexadecimal
        # ----------------------------------------------------

        try:

            raw = bytes.fromhex(location)

            if len(raw) < 21:
                return location

            # ------------------------------------------------
            # Byte order
            # ------------------------------------------------

            byte_order = (
                "<"
                if raw[0] == 1
                else ">"
            )

            # ------------------------------------------------
            # Geometry type
            # ------------------------------------------------

            geometry_type = struct.unpack(
                f"{byte_order}I",
                raw[1:5]
            )[0]

            # ------------------------------------------------
            # SRID flag
            # 0x20000000 = SRID present
            # ------------------------------------------------

            has_srid = bool(
                geometry_type & 0x20000000
            )

            offset = 5

            if has_srid:
                offset += 4

            # ------------------------------------------------
            # Read longitude + latitude
            # ------------------------------------------------

            if len(raw) < offset + 16:
                return location

            longitude, latitude = struct.unpack(
                f"{byte_order}dd",
                raw[offset:offset + 16]
            )

            return {
                "type": "Point",
                "coordinates": [
                    longitude,
                    latitude
                ]
            }

        except Exception as e:

            print(
                f"[!] Failed to parse PostGIS location "
                f"'{location}': {e}"
            )

            return location

    return location


# ============================================================
# VEHICLE SEARCH
# ============================================================

@router.get(
    "/search",
    response_model=VehicleSearchResponse
)
def search_vehicles(
    plate: str = Query(
        ...,
        description="Plate number or partial search query"
    ),
    current_user: UserProfile = Depends(
        require_roles(["investigator", "admin"])
    )
):
    """
    GET /vehicles/search?plate=

    Searches vehicles and recent observations
    by license plate number.
    """

    query_norm = plate.strip().upper()

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    log_audit_access(
        user_id=current_user.user_id,
        action="SELECT",
        table_name="vehicle_observations",
        row_reference=f"plate:{query_norm}"
    )

    supabase = get_supabase_client()

    vehicles_res: List[dict] = []
    observations_res: List[dict] = []

    # --------------------------------------------------------
    # Supabase search
    # --------------------------------------------------------

    if supabase:

        try:

            # ------------------------------------------------
            # Search vehicles
            # ------------------------------------------------

            v_data = (
                supabase
                .table("vehicles")
                .select("*")
                .ilike(
                    "normalized_plate",
                    f"%{query_norm}%"
                )
                .execute()
            )

            if v_data.data:
                vehicles_res = v_data.data

            # ------------------------------------------------
            # Search observations
            # ------------------------------------------------

            o_data = (
                supabase
                .table("vehicle_observations")
                .select("*")
                .ilike(
                    "plate_number",
                    f"%{query_norm}%"
                )
                .execute()
            )

            if o_data.data:
                observations_res = o_data.data

        except Exception as e:

            print(
                f"[!] Supabase vehicle search error: {e}"
            )

    # --------------------------------------------------------
    # Demo fallback
    # --------------------------------------------------------

    if not vehicles_res and not observations_res:

        matching_obs = [
            observation
            for observation in OBSERVATIONS[:5]
            if query_norm in observation.get(
                "plate_number",
                ""
            ).upper()
        ]

        if matching_obs:

            first_seen = min(
                observation["timestamp"]
                for observation in matching_obs
            )

            last_seen = max(
                observation["timestamp"]
                for observation in matching_obs
            )

            vehicles_res = [{
                "vehicle_id": (
                    f"demo-vehicle-"
                    f"{matching_obs[0]['plate_number']}"
                ),
                "normalized_plate": (
                    matching_obs[0]["plate_number"]
                ),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "created_at": first_seen,
                "updated_at": last_seen,
            }]

            observations_res = matching_obs

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return VehicleSearchResponse(
        query=plate,
        total_matches=len(vehicles_res),
        vehicles=vehicles_res,
        recent_observations=observations_res
    )


# ============================================================
# VEHICLE TRAJECTORY
# ============================================================

@router.get(
    "/{id}/trajectory",
    response_model=List[TrajectoryResponse]
)
def get_vehicle_trajectory(
    id: str,
    current_user: UserProfile = Depends(
        require_roles(["investigator", "admin"])
    )
):
    """
    GET /vehicles/{id}/trajectory

    Returns all trajectories associated with a vehicle.

    Each trajectory contains:

    - trajectory_id
    - vehicle_id
    - start_time
    - end_time
    - camera_sequence
    - distance
    - duration
    - confidence
    - average_speed
    - direction
    - created_at
    - trajectory points

    PostGIS locations are converted into
    GeoJSON-style Point objects.
    """

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    log_audit_access(
        user_id=current_user.user_id,
        action="SELECT",
        table_name="trajectories",
        row_reference=f"vehicle_id:{id}"
    )

    # --------------------------------------------------------
    # Supabase client
    # --------------------------------------------------------

    supabase = get_supabase_client()

    if not supabase:

        print(
            "[!] Supabase client is not available."
        )

        raise HTTPException(
            status_code=503,
            detail="Database connection is unavailable."
        )

    try:

        # ====================================================
        # STEP 1 — GET TRAJECTORIES
        # ====================================================

        print(
            f"[TRAJECTORY] Searching trajectories "
            f"for vehicle_id={id}"
        )

        trajectory_res = (
            supabase
            .table("trajectories")
            .select("*")
            .eq(
                "vehicle_id",
                id
            )
            .order(
                "start_time",
                desc=False
            )
            .execute()
        )

        trajectories = (
            trajectory_res.data or []
        )

        print(
            f"[TRAJECTORY] Found "
            f"{len(trajectories)} trajectory records."
        )

        # ====================================================
        # STEP 2 — PROCESS EACH TRAJECTORY
        # ====================================================

        processed_trajectories = []

        for trajectory in trajectories:

            trajectory_id = trajectory.get(
                "trajectory_id"
            )

            print(
                f"[TRAJECTORY] Processing "
                f"trajectory_id={trajectory_id}"
            )

            # ------------------------------------------------
            # Ensure new fields exist
            # ------------------------------------------------

            if trajectory.get("average_speed") is None:

                trajectory["average_speed"] = 0.0

            if trajectory.get("direction") is None:

                trajectory["direction"] = None

            # ------------------------------------------------
            # Load trajectory points
            # ------------------------------------------------

            points = []

            if trajectory_id:

                point_res = (
                    supabase
                    .table("trajectory_points")
                    .select("*")
                    .eq(
                        "trajectory_id",
                        trajectory_id
                    )
                    .order(
                        "timestamp",
                        desc=False
                    )
                    .execute()
                )

                point_rows = (
                    point_res.data or []
                )

                print(
                    f"[TRAJECTORY] "
                    f"{len(point_rows)} points found "
                    f"for trajectory "
                    f"{trajectory_id}"
                )

                # --------------------------------------------
                # Convert PostGIS locations
                # --------------------------------------------

                for point in point_rows:

                    point["location"] = (
                        parse_postgis_point(
                            point.get("location")
                        )
                    )

                    points.append(point)

            trajectory["points"] = points

            # ------------------------------------------------
            # Debug output
            # ------------------------------------------------

            print(
                "[TRAJECTORY] "
                f"distance={trajectory.get('distance')} km | "
                f"duration={trajectory.get('duration')} sec | "
                f"average_speed={trajectory.get('average_speed')} km/h | "
                f"direction={trajectory.get('direction')}"
            )

            processed_trajectories.append(
                trajectory
            )

        # ====================================================
        # STEP 3 — RETURN RESULT
        # ====================================================

        print(
            f"[TRAJECTORY] Returning "
            f"{len(processed_trajectories)} trajectories."
        )

        return processed_trajectories

    # ========================================================
    # DATABASE ERROR
    # ========================================================

    except Exception as e:

        print(
            "[!] Supabase trajectory error:"
        )

        print(
            f"    Vehicle ID: {id}"
        )

        print(
            f"    Error type: {type(e).__name__}"
        )

        print(
            f"    Error message: {e}"
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Do NOT silently return [].
        # Return the actual server error so that
        # frontend/API debugging is possible.
        # ----------------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve vehicle trajectory: "
                f"{str(e)}"
            )
        )