import logging
import uuid
from typing import Dict, Any, Optional, List

from backend.db import get_supabase_client
from backend.demo_data import WATCHLIST, OBSERVATIONS

logger = logging.getLogger("services.alert_engine")

# In-memory storage for fallback mode
_local_alerts: List[Dict[str, Any]] = []
_observation_history: List[Dict[str, Any]] = []


def plate_normalize(raw_plate: str) -> str:
    """
    Normalizes plate string:
    - Strips whitespace, dashes, dots, and special symbols
    - Converts to uppercase
    - Replaces common OCR confusions: '0' -> 'O', '1' -> 'I', '8' -> 'B'
    """
    if not raw_plate:
        return ""
    
    clean = "".join(c for c in raw_plate if c.isalnum()).upper()
    
    # OCR confusion mapping
    ocr_map = {
        '0': 'O',
        '1': 'I',
        '8': 'B'
    }
    
    normalized = "".join(ocr_map.get(c, c) for c in clean)
    return normalized


def get_watchlist_match(normalized_plate: str) -> Optional[Dict[str, Any]]:
    """
    Queries the Supabase watchlist table for a matching plate.
    """
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("watchlist").select("*").execute()
            if res.data:
                for item in res.data:
                    if plate_normalize(item.get("plate_number", "")) == normalized_plate:
                        return item
        except Exception as e:
            logger.warning(f"Supabase watchlist query error (using fallback): {e}")

    for item in WATCHLIST[:5]:
        if plate_normalize(item.get("plate_number", "")) == normalized_plate:
            return item

    return None


def find_previous_observation_id(normalized_plate: str, current_obs_id: str) -> Optional[str]:
    """
    Finds the most recent prior observation ID for the plate.
    """
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("vehicle_observations").select("*").execute()
            if res.data:
                matches = [
                    o for o in res.data 
                    if plate_normalize(o.get("plate_number", "")) == normalized_plate and o.get("observation_id") != current_obs_id
                ]
                if matches:
                    matches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                    return matches[0].get("observation_id")
        except Exception as e:
            logger.warning(f"Supabase observation query error (using fallback): {e}")

    all_obs = _observation_history or OBSERVATIONS[:5]
    matches = [
        o for o in all_obs 
        if plate_normalize(o.get("plate_number", "")) == normalized_plate and o.get("observation_id") != current_obs_id
    ]
    if matches:
        matches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return matches[0].get("observation_id")

    return None


def map_priority_to_severity(priority: str) -> str:
    """
    Maps watchlist priority to alert severity:
    - Critical -> High (or Critical)
    - High -> High
    - Medium -> Medium
    - Low -> Low
    """
    p_lower = str(priority).strip().lower()
    if p_lower in ["critical", "high"]:
        return "High"
    elif p_lower in ["medium", "med"]:
        return "Medium"
    elif p_lower in ["low"]:
        return "Low"
    return "Medium"


def check_and_alert(observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Checks an incoming observation against the watchlist and generates/inserts an alert if matched.
    """
    # Track observation history for prior observation lookup
    _observation_history.append(observation)

    raw_plate = observation.get("plate_number", "")
    norm_plate = plate_normalize(raw_plate)
    if not norm_plate:
        return None

    match = get_watchlist_match(norm_plate)
    if not match:
        logger.debug(f"[AlertEngine] No watchlist match for plate: {raw_plate}")
        return None

    obs_id = observation.get("observation_id", str(uuid.uuid4()))
    camera_id = observation.get("camera_id")
    alert_type = match.get("category", "Watchlist Detection")
    priority = match.get("priority", "High")
    severity = map_priority_to_severity(priority)
    confidence = float(observation.get("ocr_confidence", 0.95))
    timestamp = observation.get("timestamp", "")
    prev_obs_id = find_previous_observation_id(norm_plate, obs_id)

    image_ref = observation.get("image_ref")
    if image_ref and image_ref.startswith("s3://"):
        evidence_image = image_ref.replace("s3://anpr-captures/", "evidence-images/")
    else:
        evidence_image = None

    alert_record = {
        "alert_id": str(uuid.uuid4()),
        "plate": raw_plate,
        "plate_number": raw_plate,
        "normalized_plate": norm_plate,
        "camera_id": camera_id,
        "alert_type": alert_type,
        "timestamp": timestamp,
        "severity": severity,
        "confidence": confidence,
        "previous_observation_id": prev_obs_id,
        "evidence_image": evidence_image,
        "status": "New"
    }

    # Save to Supabase table if connected
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("alerts").insert(alert_record).execute()
            logger.info(f"[AlertEngine] Alert inserted to Supabase for {raw_plate} (Severity: {severity})")
        except Exception as e:
            logger.warning(f"[AlertEngine] Error inserting alert to Supabase: {e}")

    # Always keep in local fallback memory
    _local_alerts.append(alert_record)
    logger.info(f"[AlertEngine] Alert generated: Plate={raw_plate}, Category={alert_type}, Severity={severity}")
    return alert_record


def get_generated_alerts() -> List[Dict[str, Any]]:
    """
    Returns all alerts generated during replay session.
    """
    return list(_local_alerts)


def clear_generated_alerts() -> None:
    """
    Clears local alert storage for testing.
    """
    global _local_alerts, _observation_history
    _local_alerts = []
    _observation_history = []
