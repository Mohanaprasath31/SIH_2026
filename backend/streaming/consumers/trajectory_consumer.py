import asyncio
import logging
import math
import struct
from datetime import datetime
from typing import Dict, Any, List

from backend.streaming.bus import subscribe_to_observations
from backend.utils.time_utils import normalize_timestamp_utc
from backend.db import get_supabase_client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("consumers.trajectory")


GAP_THRESHOLD_SECONDS = 600.0

_active_trajectories: Dict[str, List[Dict[str, Any]]] = {}
_active_trajectory_ids: Dict[str, str] = {}


# ============================================================
# VEHICLE MANAGEMENT
# ============================================================

def get_or_create_vehicle_id(
    supabase,
    plate: str,
    timestamp: str
) -> str | None:
    """
    Find the vehicle UUID using normalized_plate.
    Create the vehicle if it does not already exist.
    """

    try:
        result = (
            supabase
            .table("vehicles")
            .select(
                "vehicle_id, first_seen, last_seen"
            )
            .eq(
                "normalized_plate",
                plate
            )
            .limit(1)
            .execute()
        )

        if result.data:
            vehicle = result.data[0]
            vehicle_id = vehicle["vehicle_id"]

            supabase.table("vehicles").update({
                "last_seen": timestamp
            }).eq(
                "vehicle_id",
                vehicle_id
            ).execute()

            return vehicle_id

        insert_result = (
            supabase
            .table("vehicles")
            .insert({
                "normalized_plate": plate,
                "first_seen": timestamp,
                "last_seen": timestamp
            })
            .execute()
        )

        if insert_result.data:
            return insert_result.data[0]["vehicle_id"]

    except Exception as e:
        logger.error(
            f"[TrajectoryConsumer] "
            f"Vehicle lookup/create failed "
            f"for {plate}: {e}"
        )

    return None


# ============================================================
# TRAJECTORY CREATION
# ============================================================

def create_trajectory(
    supabase,
    vehicle_id: str,
    observation: Dict[str, Any],
    timestamp: str
) -> str | None:
    """
    Create a new trajectory record.
    """

    camera_id = observation.get("camera_id")

    confidence = float(
        observation.get("ocr_confidence") or 0.0
    )

    try:
        result = (
            supabase
            .table("trajectories")
            .insert({
                "vehicle_id": vehicle_id,
                "start_time": timestamp,
                "end_time": timestamp,
                "camera_sequence": [camera_id],
                "distance": 0.0,
                "duration": 0.0,
                "confidence": confidence,
                "average_speed": 0.0,
                "direction": None
            })
            .execute()
        )

        if result.data:
            trajectory_id = result.data[0]["trajectory_id"]

            logger.info(
                f"[TrajectoryConsumer] "
                f"Created trajectory "
                f"{trajectory_id} for "
                f"{observation.get('plate_number')}"
            )

            return trajectory_id

    except Exception as e:
        logger.error(
            f"[TrajectoryConsumer] "
            f"Trajectory creation failed: {e}"
        )

    return None


# ============================================================
# TRAJECTORY POINT INSERTION
# ============================================================

def insert_trajectory_point(
    supabase,
    trajectory_id: str,
    observation: Dict[str, Any],
    timestamp: str
) -> bool:
    """
    Insert one trajectory point into Supabase.
    """

    camera_id = observation.get("camera_id")

    confidence = float(
        observation.get("ocr_confidence") or 0.0
    )

    location = observation.get("location")

    if not location:
        logger.warning(
            "[TrajectoryConsumer] "
            "Observation has no location. "
            "Skipping trajectory point."
        )

        return False

    try:
        result = (
            supabase
            .table("trajectory_points")
            .insert({
                "trajectory_id": trajectory_id,
                "camera_id": camera_id,
                "timestamp": timestamp,
                "location": location,
                "confidence": confidence
            })
            .execute()
        )

        return bool(result.data)

    except Exception as e:
        logger.error(
            f"[TrajectoryConsumer] "
            f"Trajectory point insertion failed: {e}"
        )

        return False


# ============================================================
# POSTGIS LOCATION PARSER
# ============================================================

def parse_postgis_point(location):
    """
    Convert a PostGIS EWKB hexadecimal point
    into:

        (longitude, latitude)

    Also supports GeoJSON-style Point objects.
    """

    if not location:
        return None

    # --------------------------------------------------------
    # GeoJSON Point
    # --------------------------------------------------------

    if isinstance(location, dict):

        coordinates = location.get("coordinates")

        if (
            isinstance(coordinates, list)
            and len(coordinates) >= 2
        ):
            try:
                return (
                    float(coordinates[0]),
                    float(coordinates[1])
                )
            except Exception:
                return None

    # --------------------------------------------------------
    # PostGIS EWKB hexadecimal
    # --------------------------------------------------------

    if isinstance(location, str):

        try:
            raw = bytes.fromhex(location)

            if len(raw) < 21:
                return None

            byte_order = (
                "<"
                if raw[0] == 1
                else ">"
            )

            geometry_type = struct.unpack(
                f"{byte_order}I",
                raw[1:5]
            )[0]

            has_srid = bool(
                geometry_type & 0x20000000
            )

            offset = 5

            if has_srid:
                offset += 4

            if len(raw) < offset + 16:
                return None

            longitude, latitude = struct.unpack(
                f"{byte_order}dd",
                raw[offset:offset + 16]
            )

            return (
                longitude,
                latitude
            )

        except Exception as e:
            logger.error(
                f"[TrajectoryConsumer] "
                f"Failed to parse PostGIS "
                f"location '{location}': {e}"
            )

            return None

    return None


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance_km(
    history: List[Dict[str, Any]]
) -> float:
    """
    Calculate total trajectory distance.

    Uses the Haversine formula between
    consecutive trajectory points.

    Returns distance in kilometers.
    """

    coordinates = []

    for point in history:

        location = parse_postgis_point(
            point.get("location")
        )

        if location:
            coordinates.append(location)

    if len(coordinates) < 2:
        return 0.0

    earth_radius_km = 6371.0088

    total_distance = 0.0

    for i in range(1, len(coordinates)):

        lon1, lat1 = coordinates[i - 1]
        lon2, lat2 = coordinates[i]

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)

        delta_lat = math.radians(
            lat2 - lat1
        )

        delta_lon = math.radians(
            lon2 - lon1
        )

        a = (
            math.sin(delta_lat / 2) ** 2
            +
            math.cos(lat1_rad)
            *
            math.cos(lat2_rad)
            *
            math.sin(delta_lon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        segment_distance = (
            earth_radius_km * c
        )

        total_distance += segment_distance

    return total_distance


# ============================================================
# AVERAGE SPEED CALCULATION
# ============================================================

def calculate_average_speed(
    distance_km: float,
    duration_seconds: float
) -> float:
    """
    Calculate average vehicle speed.

    Formula:

        speed = distance / time

    Distance is in kilometers.
    Time is converted from seconds to hours.

    Returns speed in km/h.
    """

    if duration_seconds <= 0:
        return 0.0

    duration_hours = (
        duration_seconds / 3600.0
    )

    if duration_hours <= 0:
        return 0.0

    return distance_km / duration_hours


# ============================================================
# DIRECTION CALCULATION
# ============================================================

def calculate_direction(
    history: List[Dict[str, Any]]
) -> str | None:
    """
    Calculate the overall direction of travel.

    Uses the first and last valid geographic
    trajectory points.

    Returns one of:

        North
        North-East
        East
        South-East
        South
        South-West
        West
        North-West

    Returns None when fewer than two valid
    geographic points are available.
    """

    coordinates = []

    for point in history:

        location = parse_postgis_point(
            point.get("location")
        )

        if location:
            coordinates.append(location)

    if len(coordinates) < 2:
        return None

    # --------------------------------------------------------
    # First and last trajectory coordinates
    # --------------------------------------------------------

    start_lon, start_lat = coordinates[0]
    end_lon, end_lat = coordinates[-1]

    # --------------------------------------------------------
    # Calculate bearing
    # --------------------------------------------------------

    start_lat_rad = math.radians(start_lat)
    end_lat_rad = math.radians(end_lat)

    delta_lon_rad = math.radians(
        end_lon - start_lon
    )

    y = math.sin(delta_lon_rad) * math.cos(
        end_lat_rad
    )

    x = (
        math.cos(start_lat_rad)
        * math.sin(end_lat_rad)
        -
        math.sin(start_lat_rad)
        * math.cos(end_lat_rad)
        * math.cos(delta_lon_rad)
    )

    bearing = math.degrees(
        math.atan2(y, x)
    )

    # Normalize to 0-360 degrees

    bearing = (
        bearing + 360
    ) % 360

    # --------------------------------------------------------
    # Convert bearing to compass direction
    # --------------------------------------------------------

    directions = [
        "North",
        "North-East",
        "East",
        "South-East",
        "South",
        "South-West",
        "West",
        "North-West"
    ]

    index = int(
        (bearing + 22.5) / 45
    ) % 8

    return directions[index]


# ============================================================
# TRAJECTORY UPDATE
# ============================================================

def update_trajectory(
    supabase,
    trajectory_id: str,
    history: List[Dict[str, Any]]
) -> None:
    """
    Update trajectory summary information.

    Calculates:

    - start time
    - end time
    - duration
    - camera sequence
    - total distance
    - average OCR confidence
    - average speed
    - direction
    """

    if not history:
        return

    try:

        # ----------------------------------------------------
        # Time
        # ----------------------------------------------------

        start_time = datetime.fromisoformat(
            history[0]["timestamp"]
        )

        end_time = datetime.fromisoformat(
            history[-1]["timestamp"]
        )

        duration = max(
            0.0,
            (
                end_time - start_time
            ).total_seconds()
        )

        # ----------------------------------------------------
        # Camera sequence
        # ----------------------------------------------------

        camera_sequence = []

        for point in history:

            camera_id = point.get(
                "camera_id"
            )

            if (
                camera_id
                and camera_id not in camera_sequence
            ):
                camera_sequence.append(
                    camera_id
                )

        # ----------------------------------------------------
        # OCR confidence
        # ----------------------------------------------------

        confidence_values = [

            float(
                point.get(
                    "ocr_confidence"
                ) or 0.0
            )

            for point in history

        ]

        confidence = (
            sum(confidence_values)
            /
            len(confidence_values)
            if confidence_values
            else 0.0
        )

        # ----------------------------------------------------
        # REAL DISTANCE
        # ----------------------------------------------------

        distance = calculate_distance_km(
            history
        )

        # ----------------------------------------------------
        # AVERAGE SPEED
        # ----------------------------------------------------

        average_speed = calculate_average_speed(
            distance,
            duration
        )

        # ----------------------------------------------------
        # DIRECTION
        # ----------------------------------------------------

        direction = calculate_direction(
            history
        )

        # ----------------------------------------------------
        # Update Supabase
        # ----------------------------------------------------

        supabase.table(
            "trajectories"
        ).update({

            "start_time":
                history[0]["timestamp"],

            "end_time":
                history[-1]["timestamp"],

            "camera_sequence":
                camera_sequence,

            "distance":
                distance,

            "duration":
                duration,

            "confidence":
                confidence,

            "average_speed":
                average_speed,

            "direction":
                direction

        }).eq(
            "trajectory_id",
            trajectory_id
        ).execute()

        logger.info(
            f"[TrajectoryConsumer] "
            f"Updated trajectory "
            f"{trajectory_id} | "
            f"Distance: "
            f"{distance:.3f} km | "
            f"Duration: "
            f"{duration:.1f}s | "
            f"Average Speed: "
            f"{average_speed:.2f} km/h | "
            f"Direction: "
            f"{direction or 'N/A'} | "
            f"Cameras: "
            f"{len(camera_sequence)}"
        )

    except Exception as e:

        logger.error(
            f"[TrajectoryConsumer] "
            f"Trajectory update failed: {e}"
        )


# ============================================================
# OBSERVATION PROCESSING
# ============================================================

def process_observation(
    observation: Dict[str, Any]
) -> None:
    """
    Process one observation from
    the streaming bus.
    """

    plate = observation.get(
        "plate_number",
        "UNKNOWN"
    )

    camera = observation.get(
        "camera_id",
        "UNKNOWN"
    )

    raw_timestamp = observation.get(
        "timestamp"
    )

    utc_timestamp = normalize_timestamp_utc(
        raw_timestamp
    )

    current_dt = datetime.fromisoformat(
        utc_timestamp
    )

    # --------------------------------------------------------
    # Initialize history
    # --------------------------------------------------------

    if plate not in _active_trajectories:
        _active_trajectories[plate] = []

    history = _active_trajectories[plate]

    # --------------------------------------------------------
    # Gap detection
    # --------------------------------------------------------

    has_gap = False

    gap_duration = 0.0

    segment_status = "continuous"

    if history:

        last_point = history[-1]

        last_dt = datetime.fromisoformat(
            last_point["timestamp"]
        )

        gap_duration = (
            current_dt - last_dt
        ).total_seconds()

        if gap_duration > GAP_THRESHOLD_SECONDS:

            has_gap = True

            segment_status = "gap"

            logger.warning(
                f"[TrajectoryConsumer] "
                f"Time gap threshold "
                f"exceeded for plate "
                f"{plate}! "
                f"Gap: "
                f"{gap_duration:.1f}s "
                f"(> "
                f"{GAP_THRESHOLD_SECONDS}s). "
                f"Segment marked as GAP."
            )

    # --------------------------------------------------------
    # Create history point
    # --------------------------------------------------------

    point_entry = {

        "event_id":
            observation.get(
                "event_id"
            ),

        "observation_id":
            observation.get(
                "observation_id"
            ),

        "camera_id":
            camera,

        "timestamp":
            utc_timestamp,

        "location":
            observation.get(
                "location"
            ),

        "ocr_confidence":
            observation.get(
                "ocr_confidence"
            ),

        "has_gap":
            has_gap,

        "segment_status":
            segment_status,

        "gap_duration_seconds":
            (
                gap_duration
                if has_gap
                else 0.0
            )
    }

    history.append(point_entry)

    point_count = len(history)

    logger.info(
        f"[TrajectoryConsumer] "
        f"Processed plate: "
        f"{plate}, "
        f"camera: "
        f"{camera}, "
        f"timestamp: "
        f"{utc_timestamp} | "
        f"Points: "
        f"{point_count} | "
        f"Status: "
        f"{segment_status}"
    )

    # ========================================================
    # SUPABASE PERSISTENCE
    # ========================================================

    supabase = get_supabase_client()

    if not supabase:

        logger.warning(
            "[TrajectoryConsumer] "
            "Supabase unavailable. "
            "Keeping trajectory in "
            "memory only."
        )

        return

    # --------------------------------------------------------
    # Get/create vehicle
    # --------------------------------------------------------

    vehicle_id = get_or_create_vehicle_id(
        supabase,
        plate,
        utc_timestamp
    )

    if not vehicle_id:
        return

    # --------------------------------------------------------
    # Current trajectory
    # --------------------------------------------------------

    trajectory_id = (
        _active_trajectory_ids.get(
            plate
        )
    )

    # --------------------------------------------------------
    # Create first trajectory
    # --------------------------------------------------------

    if not trajectory_id:

        trajectory_id = create_trajectory(
            supabase,
            vehicle_id,
            observation,
            utc_timestamp
        )

        if not trajectory_id:
            return

        _active_trajectory_ids[
            plate
        ] = trajectory_id

    # --------------------------------------------------------
    # Large time gap
    # --------------------------------------------------------

    elif has_gap:

        trajectory_id = create_trajectory(
            supabase,
            vehicle_id,
            observation,
            utc_timestamp
        )

        if not trajectory_id:
            return

        _active_trajectory_ids[
            plate
        ] = trajectory_id

        history = [
            point_entry
        ]

        _active_trajectories[
            plate
        ] = history

    # --------------------------------------------------------
    # Insert trajectory point
    # --------------------------------------------------------

    point_inserted = (
        insert_trajectory_point(
            supabase,
            trajectory_id,
            observation,
            utc_timestamp
        )
    )

    if not point_inserted:
        return

    # --------------------------------------------------------
    # Update trajectory
    # --------------------------------------------------------

    update_trajectory(
        supabase,
        trajectory_id,
        history
    )


# ============================================================
# CONSUMER STARTUP
# ============================================================

def start_consumer() -> None:

    subscribe_to_observations(
        process_observation
    )

    logger.info(
        "[TrajectoryConsumer] "
        "Subscribed to observation "
        "stream with gap detection enabled."
    )


# ============================================================
# ACCESSORS
# ============================================================

def get_trajectories() -> Dict[
    str,
    List[Dict[str, Any]]
]:

    return _active_trajectories


def clear_trajectories_store() -> None:

    global _active_trajectories
    global _active_trajectory_ids

    _active_trajectories = {}

    _active_trajectory_ids = {}


# ============================================================
# STANDALONE MODE
# ============================================================

def main():

    logger.info(
        "Starting Trajectory Consumer "
        "standalone listener..."
    )

    start_consumer()

    try:

        loop = asyncio.get_event_loop()

        loop.run_forever()

    except (
        KeyboardInterrupt,
        SystemExit
    ):

        logger.info(
            "Trajectory Consumer stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()