from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# HEALTH & STATUS MODELS
# ============================================================================
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="API operational status")
    database: str = Field(..., description="Supabase connection status")
    version: str = Field(default="1.0.0", description="API version")


# ============================================================================
# CAMERA MODELS
# ============================================================================
class CameraResponse(BaseModel):
    camera_id: str
    name: str
    location: Any  # PostGIS Geography Point string or Dict
    road: str
    direction: str
    zone: str
    status: str
    health: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CameraHealthResponse(BaseModel):
    camera_id: str
    name: str
    status: str
    is_online: bool
    last_active: Optional[str] = None
    last_heartbeat: Optional[str] = None
    fps: float = 29.5
    latency: float = 18.0
    frame_drops: int = 0
    network_status: str = "optimal"
    ocr_confidence: float = 0.97
    detection_rate: float = 0.98
    observation_count: int = 0



# ============================================================================
# VEHICLE & OBSERVATION MODELS
# ============================================================================
class VehicleResponse(BaseModel):
    vehicle_id: str
    normalized_plate: str
    first_seen: str
    last_seen: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VehicleObservationResponse(BaseModel):
    observation_id: str
    camera_id: str
    plate_number: str
    timestamp: str
    location: Any
    ocr_confidence: float
    vehicle_type: str
    direction: str
    image_ref: Optional[str] = None
    created_at: Optional[str] = None


class VehicleSearchResponse(BaseModel):
    query: str
    total_matches: int
    vehicles: List[VehicleResponse]
    recent_observations: List[VehicleObservationResponse]


# ============================================================================
# TRAJECTORY MODELS
# ============================================================================
class TrajectoryPointResponse(BaseModel):
    point_id: str
    trajectory_id: str
    camera_id: Optional[str] = None
    timestamp: str
    location: Any
    confidence: float
    created_at: Optional[str] = None
class TrajectoryResponse(BaseModel):
    trajectory_id: str
    vehicle_id: str
    start_time: str
    end_time: str
    camera_sequence: List[str]
    distance: float
    duration: float
    confidence: float
    average_speed: float = 0.0
    created_at: Optional[str] = None
    points: Optional[List[TrajectoryPointResponse]] = Field(default_factory=list)

# ============================================================================
# WATCHLIST MODELS
# ============================================================================
class WatchlistCreate(BaseModel):
    plate_number: str
    category: str = Field(..., example="Stolen Vehicle")
    priority: str = Field(..., example="High")
    status: str = Field(default="Active", example="Active")
    validity: Optional[str] = Field(default=None, example="2026-12-31T23:59:59+05:30")


class WatchlistResponse(BaseModel):
    plate_number: str
    category: str
    priority: str
    status: str
    validity: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ============================================================================
# ALERT MODELS
# ============================================================================
class AlertResponse(BaseModel):
    alert_id: str
    plate_number: str
    camera_id: Optional[str] = None
    alert_type: str
    timestamp: str
    severity: str
    confidence: float
    status: str
    created_at: Optional[str] = None


# ============================================================================
# ANALYTICS MODELS
# ============================================================================
class HourlyVolumeItem(BaseModel):
    hour: str
    count: int
    vehicle_types: Dict[str, int] = Field(default_factory=dict)


class HourlyVolumeResponse(BaseModel):
    total_observations: int
    hourly_data: List[HourlyVolumeItem]


class ODMatrixEntry(BaseModel):
    origin_camera_id: str
    origin_camera_name: str
    destination_camera_id: str
    destination_camera_name: str
    trip_count: int


class ODMatrixResponse(BaseModel):
    total_trips: int
    matrix: List[ODMatrixEntry]
