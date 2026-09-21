from typing import Any, Dict, List
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException

from backend.db import get_supabase_client
from backend.auth import require_roles, UserProfile
from backend.streaming.bus import publish_observation


router = APIRouter(
    prefix="/anpr",
    tags=["ANPR"]
)


@router.post("/ingest")
async def ingest_observations(
    observations: List[Dict[str, Any]],
    current_user: UserProfile = Depends(
        require_roles(["admin", "investigator"])
    )
):
    # ---------------------------------------------------------
    # Validate input
    # ---------------------------------------------------------

    if not observations:
        raise HTTPException(
            status_code=400,
            detail="No observations supplied."
        )

    # ---------------------------------------------------------
    # Connect to Supabase
    # ---------------------------------------------------------

    supabase = get_supabase_client()

    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase connection unavailable."
        )

    inserted_observations = []
    inserted_vehicles = {}

    # ---------------------------------------------------------
    # Determine video base time
    # ---------------------------------------------------------

    max_video_seconds = max(
        float(obs.get("timestamp_seconds", 0))
        for obs in observations
    )

    video_start_time = (
        datetime.now(timezone.utc)
        - timedelta(seconds=max_video_seconds)
    )

    # ---------------------------------------------------------
    # Process every ANPR observation
    # ---------------------------------------------------------

    for observation in observations:

        # -----------------------------------------------------
        # Get plate number
        # -----------------------------------------------------

        plate_number = (
            observation.get("plate_number")
            or observation.get("normalized_plate")
            or ""
        ).strip().upper()

        if not plate_number:
            continue

        # -----------------------------------------------------
        # Get camera identifier
        # -----------------------------------------------------

        camera_identifier = observation.get("camera_id")

        if not camera_identifier:
            raise HTTPException(
                status_code=400,
                detail="camera_id is required."
            )

        # -----------------------------------------------------
        # Resolve camera
        #
        # Accept:
        #   1. Camera UUID
        #   2. Camera name such as CAM-001
        # -----------------------------------------------------

        camera_result = None

        try:
            # Check whether the supplied identifier is a UUID.
            UUID(str(camera_identifier))

            camera_result = (
                supabase
                .table("cameras")
                .select(
                    "camera_id, name, location"
                )
                .eq(
                    "camera_id",
                    str(camera_identifier)
                )
                .limit(1)
                .execute()
            )

        except ValueError:

            # The AI pipeline currently sends values such as:
            # CAM-001
            #
            # In the database, this is stored in the
            # cameras.name column.

            camera_result = (
                supabase
                .table("cameras")
                .select(
                    "camera_id, name, location"
                )
                .eq(
                    "name",
                    str(camera_identifier)
                )
                .limit(1)
                .execute()
            )

        # -----------------------------------------------------
        # Make sure camera exists
        # -----------------------------------------------------

        if not camera_result.data:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Camera not found: "
                    f"{camera_identifier}"
                )
            )

        camera = camera_result.data[0]

        camera_id = camera["camera_id"]
        camera_location = camera.get("location")

        # -----------------------------------------------------
        # Make sure camera has location
        # -----------------------------------------------------

        if not camera_location:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Camera {camera_identifier} "
                    f"has no location."
                )
            )

        # -----------------------------------------------------
        # Convert video timestamp to real timestamp
        # -----------------------------------------------------

        if observation.get("timestamp"):

            timestamp = observation["timestamp"]

        else:

            timestamp_seconds = float(
                observation.get(
                    "timestamp_seconds",
                    0
                )
            )

            timestamp = (
                video_start_time
                + timedelta(
                    seconds=timestamp_seconds
                )
            ).isoformat()

        # -----------------------------------------------------
        # OCR confidence
        # -----------------------------------------------------

        ocr_confidence = float(
            observation.get(
                "confidence",
                observation.get(
                    "ocr_confidence",
                    0.0
                )
            )
        )

        # Keep confidence between 0 and 1.
        ocr_confidence = max(
            0.0,
            min(1.0, ocr_confidence)
        )

        # -----------------------------------------------------
        # Prepare vehicle information
        # -----------------------------------------------------

        if plate_number not in inserted_vehicles:

            inserted_vehicles[plate_number] = {
                "normalized_plate": plate_number,
                "first_seen": timestamp,
                "last_seen": timestamp,
            }

        else:

            # Same vehicle appeared multiple times.
            inserted_vehicles[plate_number]["last_seen"] = (
                timestamp
            )

        # -----------------------------------------------------
        # Prepare observation record
        # -----------------------------------------------------

        observation_record = {
            "observation_id": str(uuid4()),

            "camera_id": camera_id,

            "plate_number": plate_number,

            "timestamp": timestamp,

            "location": camera_location,

            "ocr_confidence": ocr_confidence,

            "vehicle_type": observation.get(
                "vehicle_type",
                "Unknown"
            ),

            "direction": observation.get(
                "direction",
                "Unknown"
            ),
        }

        # -----------------------------------------------------
        # Optional image reference
        # -----------------------------------------------------

        if observation.get("image_ref") is not None:

            observation_record["image_ref"] = (
                observation["image_ref"]
            )

        # -----------------------------------------------------
        # Add observation to batch
        # -----------------------------------------------------

        inserted_observations.append(
            observation_record
        )

    # ---------------------------------------------------------
    # Insert / update vehicles
    # ---------------------------------------------------------

    for plate_number, vehicle in inserted_vehicles.items():

        try:

            # Check whether vehicle already exists.

            existing = (
                supabase
                .table("vehicles")
                .select("*")
                .eq(
                    "normalized_plate",
                    plate_number
                )
                .limit(1)
                .execute()
            )

            if existing.data:

                # Vehicle already exists.
                # Update last_seen.

                existing_vehicle = existing.data[0]

                (
                    supabase
                    .table("vehicles")
                    .update({
                        "last_seen": vehicle["last_seen"]
                    })
                    .eq(
                        "vehicle_id",
                        existing_vehicle["vehicle_id"]
                    )
                    .execute()
                )

            else:

                # New vehicle.
                # PostgreSQL generates vehicle_id.

                (
                    supabase
                    .table("vehicles")
                    .insert(vehicle)
                    .execute()
                )

        except Exception as e:

            print(
                f"[!] Vehicle insert error: {e}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Failed to insert vehicle: {e}"
                )
            )

    # ---------------------------------------------------------
    # Insert observations into Supabase
    # ---------------------------------------------------------

    if inserted_observations:

        try:

            result = (
                supabase
                .table("vehicle_observations")
                .insert(inserted_observations)
                .execute()
            )

            if result.data:
                inserted_observations = result.data

        except Exception as e:

            print(
                f"[!] Observation insert error: {e}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Failed to insert observations: {e}"
                )
            )

    # ---------------------------------------------------------
    # Publish observations to streaming bus
    #
    # This sends each real ANPR observation to:
    #
    #   Observation Bus
    #          |
    #     +----+----+---------+
    #     |         |         |
    # Trajectory  Alert   Analytics
    # Consumer   Consumer Consumer
    #
    # ---------------------------------------------------------

    published_count = 0

    for observation in inserted_observations:

        try:

            processed = await publish_observation(
                observation
            )

            if processed:
                published_count += 1

        except Exception as e:

            # Bus errors should not make the already
            # successfully stored database observation
            # disappear.

            print(
                f"[!] Observation publish error: {e}"
            )

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return {
        "status": "success",

        "vehicles_processed": len(
            inserted_vehicles
        ),

        "observations_inserted": len(
            inserted_observations
        ),

        "observations_published": published_count,

        "plates": list(
            inserted_vehicles.keys()
        )
    }