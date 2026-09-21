import logging
from datetime import datetime, timezone
from typing import Tuple, Optional

logger = logging.getLogger("utils.time_utils")


def normalize_timestamp_utc(ts_input: Optional[str]) -> str:
    """
    Normalizes an incoming timestamp string to UTC ISO 8601 format.
    If input is invalid or None, returns current UTC timestamp ISO.
    """
    if not ts_input:
        return datetime.now(timezone.utc).isoformat()

    try:
        # Replace 'Z' with +00:00 for datetime.fromisoformat
        clean_ts = ts_input.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean_ts)
        
        # If naive (no tzinfo), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        return dt.isoformat()
    except Exception as e:
        logger.warning(f"Error parsing timestamp '{ts_input}': {e}. Fallback to current UTC time.")
        return datetime.now(timezone.utc).isoformat()


def check_heartbeat_drift(heartbeat_ts_str: str, threshold_seconds: float = 5.0) -> Tuple[bool, float]:
    """
    Calculates time drift between camera heartbeat timestamp and current server UTC time.
    Logs warning if drift exceeds threshold_seconds.
    Returns (has_drifted, drift_seconds).
    """
    try:
        hb_utc_str = normalize_timestamp_utc(heartbeat_ts_str)
        hb_dt = datetime.fromisoformat(hb_utc_str)
        server_dt = datetime.now(timezone.utc)

        drift = abs((server_dt - hb_dt).total_seconds())
        if drift > threshold_seconds:
            logger.warning(
                f"[TimestampSync] Heartbeat timestamp drift detected! "
                f"Heartbeat: {heartbeat_ts_str}, Server UTC: {server_dt.isoformat()}, Drift: {drift:.2f}s (threshold: {threshold_seconds}s)"
            )
            return True, drift
        return False, drift
    except Exception as e:
        logger.error(f"Error checking heartbeat drift: {e}")
        return False, 0.0
