from typing import List
from fastapi import APIRouter, HTTPException, Depends

from backend.db import get_supabase_client
from backend.models import CameraResponse, CameraHealthResponse
from backend.services.camera_health import get_camera_health_state, get_all_cameras_health_state
from backend.auth import require_roles, UserProfile
from backend.demo_data import CAMERAS

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("", response_model=List[CameraResponse])
def get_cameras(
    current_user: UserProfile = Depends(require_roles(["analyst", "traffic_operator", "admin"]))
):
    """
    GET /cameras
    Fetches all registered ANPR cameras with live health summary attached.
    """
    supabase = get_supabase_client()
    base_cameras = []
    if supabase:
        try:
            res = supabase.table("cameras").select("*").execute()
            if res.data and len(res.data) > 0:
                base_cameras = res.data
        except Exception as e:
            print(f"[!] Supabase cameras fetch error: {e}")

    if not base_cameras:
        base_cameras = CAMERAS[:5]

    # Merge live health summary
    result = []
    for cam in base_cameras:
        cam_id = str(cam.get("camera_id"))
        health = get_camera_health_state(cam_id)
        
        cam_copy = dict(cam)
        if health:
            cam_copy["health"] = health
            cam_copy["status"] = health.get("status", cam.get("status", "online"))
        
        result.append(cam_copy)

    return result


@router.get("/{id}/health", response_model=CameraHealthResponse)
def get_camera_health(id: str):
    """
    GET /cameras/{id}/health
    Returns operational health status for a specific camera.
    """
    health = get_camera_health_state(id)

    if not health:
        cameras = get_cameras()
        camera = next((c for c in cameras if str(c.get("camera_id")) == id), None)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera with ID {id} not found")
        status = camera.get("status", "online")
        is_online = status in ["active", "online", "degraded"]
        return CameraHealthResponse(
            camera_id=id,
            name=camera.get("name", "ANPR Camera"),
            status=status,
            is_online=is_online,
            last_active=None,
            observation_count=0
        )

    status = health.get("status", "online")
    is_online = status in ["active", "online", "degraded"]

    return CameraHealthResponse(
        camera_id=str(health.get("camera_id")),
        name=health.get("name", "ANPR Camera"),
        status=status,
        is_online=is_online,
        last_active=health.get("last_heartbeat"),
        last_heartbeat=health.get("last_heartbeat"),
        fps=float(health.get("fps", 29.5)),
        latency=float(health.get("latency", 18.0)),
        frame_drops=int(health.get("frame_drops", 0)),
        network_status=str(health.get("network_status", "optimal")),
        ocr_confidence=float(health.get("ocr_confidence", 0.97)),
        detection_rate=float(health.get("detection_rate", 0.98)),
        observation_count=0
    )

