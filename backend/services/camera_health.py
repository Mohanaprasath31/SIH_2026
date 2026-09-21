import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.db import get_supabase_client
from backend.utils.time_utils import normalize_timestamp_utc, check_heartbeat_drift
from backend.utils.retry import retry_with_backoff
from backend.demo_data import CAMERAS

logger = logging.getLogger("services.camera_health")

# In-memory store of live camera health states: { camera_id: health_dict }
_camera_health_store: Dict[str, Dict[str, Any]] = {}
# Tracking low confidence duration for degradation rule: { camera_id: timestamp_below_60 }
_low_confidence_timer: Dict[str, Optional[float]] = {}
# Active incident tracking: { camera_id: { "phase": "dropping"|"recovering", "start_time": float, "target_drop_time": float } }
_active_incidents: Dict[str, Dict[str, Any]] = {}

_background_task: Optional[asyncio.Task] = None


def load_base_cameras() -> List[Dict[str, Any]]:
    """
    Loads the base camera list from Supabase.
    """
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("cameras").select("*").execute()
            if res.data:
                return res.data
        except Exception as e:
            logger.warning(f"Supabase cameras load error: {e}")

    return CAMERAS[:5]


def initialize_health_store():
    """
    Initializes health state dictionary for all cameras if empty.
    """
    cameras = load_base_cameras()
    now_iso = datetime.now(timezone.utc).isoformat()

    for cam in cameras:
        cam_id = str(cam.get("camera_id"))
        if cam_id not in _camera_health_store:
            _camera_health_store[cam_id] = {
                "camera_id": cam_id,
                "name": cam.get("name", f"ANPR Camera {cam_id[:8]}"),
                "road": cam.get("road", "Main Corridor"),
                "zone": cam.get("zone", "City Center"),
                "status": "online" if cam.get("status") in ["active", "online"] else cam.get("status", "online"),
                "is_online": True,
                "last_heartbeat": now_iso,
                "fps": 29.5,
                "latency": 18.0,
                "frame_drops": 0,
                "network_status": "optimal",
                "ocr_confidence": 0.97,
                "detection_rate": 0.98,
                "incident": None
            }


def trigger_dirty_lens_incident(camera_id: Optional[str] = None) -> str:
    """
    Triggers a dirty-lens incident for a specific or random camera.
    """
    if not _camera_health_store:
        initialize_health_store()

    if not camera_id or camera_id not in _camera_health_store:
        camera_id = random.choice(list(_camera_health_store.keys()))

    now = asyncio.get_event_loop().time()
    _active_incidents[camera_id] = {
        "phase": "dropping",
        "start_time": now,
        "duration_drop": 15.0,     # ~15s to drop
        "duration_low": 12.0,      # ~12s stayed low (triggers degraded rule >10s)
        "duration_recover": 15.0   # ~15s to recover back
    }
    
    _camera_health_store[camera_id]["incident"] = "dirty_lens"
    _camera_health_store[camera_id]["network_status"] = "degraded"
    logger.warning(f"[CameraHealth] Dirty-lens incident triggered on camera {camera_id}")
    return camera_id


async def update_camera_metrics_loop(interval: float = 2.0):
    """
    Background loop that updates camera metrics with realistic random fluctuations,
    handles dirty-lens incident simulations, and enforces degradation rules.
    """
    logger.info("Starting Camera Health Background Monitoring Service...")
    initialize_health_store()

    cycle_count = 0

    while True:
        try:
            now_loop = asyncio.get_event_loop().time()
            now_iso = datetime.now(timezone.utc).isoformat()
            cycle_count += 1

            # Trigger a random dirty-lens incident roughly every 25-30 cycles (~50-60s) if none active
            if cycle_count % 25 == 0 and not _active_incidents:
                trigger_dirty_lens_incident()

            for cam_id, state in _camera_health_store.items():
                state["last_heartbeat"] = now_iso

                # Check for heartbeat timestamp drift against server UTC time
                check_heartbeat_drift(now_iso, threshold_seconds=5.0)

                # Check if camera is currently in a dirty-lens incident
                if cam_id in _active_incidents:
                    inc = _active_incidents[cam_id]
                    elapsed = now_loop - inc["start_time"]
                    drop_t = inc["duration_drop"]
                    low_t = inc["duration_low"]
                    rec_t = inc["duration_recover"]
                    total_incident = drop_t + low_t + rec_t

                    if elapsed < drop_t:
                        # Dropping phase: linear interpolation from 0.96 down to 0.42
                        progress = elapsed / drop_t
                        state["ocr_confidence"] = max(0.40, 0.96 - progress * (0.96 - 0.42))
                    elif elapsed < drop_t + low_t:
                        # Stay low (~0.42)
                        state["ocr_confidence"] = random.uniform(0.40, 0.48)
                    elif elapsed < total_incident:
                        # Recovering phase: 0.42 back to 0.96
                        rec_elapsed = elapsed - (drop_t + low_t)
                        progress = rec_elapsed / rec_t
                        state["ocr_confidence"] = min(0.97, 0.42 + progress * (0.97 - 0.42))
                    else:
                        # Incident finished
                        del _active_incidents[cam_id]
                        state["incident"] = None
                        state["network_status"] = "optimal"
                        state["ocr_confidence"] = 0.97
                        logger.info(f"[CameraHealth] Incident resolved for camera {cam_id}")
                else:
                    # Normal realistic fluctuations
                    base_ocr = 0.97
                    state["ocr_confidence"] = max(0.85, min(0.99, base_ocr + random.uniform(-0.02, 0.02)))
                    state["fps"] = round(max(24.0, min(30.0, 29.5 + random.uniform(-1.0, 0.5))), 1)
                    state["latency"] = round(max(10.0, min(45.0, 18.0 + random.uniform(-2.5, 3.5))), 1)
                    state["frame_drops"] = random.choice([0, 0, 0, 1, 2])
                    state["detection_rate"] = round(max(0.90, min(0.99, 0.97 + random.uniform(-0.01, 0.01))), 2)

                # ============================================================
                # Rule: if ocr_confidence stays below 60% for >10s -> "degraded"
                # Once recovers above 60% -> "online"
                # ============================================================
                curr_ocr = state["ocr_confidence"]
                if curr_ocr < 0.60:
                    if _low_confidence_timer.get(cam_id) is None:
                        _low_confidence_timer[cam_id] = now_loop
                    elif (now_loop - _low_confidence_timer[cam_id]) >= 10.0:
                        if state["status"] != "degraded":
                            state["status"] = "degraded"
                            state["is_online"] = True
                            logger.warning(
                                f"[CameraHealth] Camera {cam_id} marked DEGRADED "
                                f"(OCR confidence {curr_ocr*100:.1f}% below 60% for >10s)"
                            )
                else:
                    _low_confidence_timer[cam_id] = None
                    if state["status"] == "degraded" and curr_ocr >= 0.60:
                        state["status"] = "online"
                        state["is_online"] = True
                        logger.info(f"[CameraHealth] Camera {cam_id} recovered to ONLINE (OCR confidence {curr_ocr*100:.1f}%)")

            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Camera health monitor task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in camera health monitor loop: {e}")
            await asyncio.sleep(interval)


def start_camera_health_monitor():
    """
    Starts camera health monitoring background task if not already running.
    """
    global _background_task
    if _background_task is None or _background_task.done():
        loop = asyncio.get_event_loop()
        _background_task = loop.create_task(update_camera_metrics_loop(interval=2.0))
        logger.info("Camera health background task started.")


def get_camera_health_state(camera_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns live health state for a single camera.
    """
    if not _camera_health_store:
        initialize_health_store()
    return _camera_health_store.get(str(camera_id))


def get_all_cameras_health_state() -> List[Dict[str, Any]]:
    """
    Returns list of all cameras merged with their live health summary.
    """
    if not _camera_health_store:
        initialize_health_store()
    return list(_camera_health_store.values())
