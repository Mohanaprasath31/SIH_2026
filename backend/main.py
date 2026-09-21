import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.db import get_supabase_client
from backend.models import HealthCheckResponse

from backend.routers import (
    cameras,
    vehicles,
    alerts,
    analytics,
    watchlist,
    admin,
    anpr
)

from backend.streaming.bus import publish_observation

from backend.streaming.consumers import (
    trajectory_consumer,
    alert_consumer,
    analytics_consumer
)

from backend.services.camera_health import (
    start_camera_health_monitor
)


# ============================================================
# LOAD ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ANPR Traffic Surveillance System API",
    description=(
        "High-performance backend API for automated number "
        "plate recognition, vehicle tracking, alerts, and analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTER API ROUTERS
# ============================================================

app.include_router(cameras.router)
app.include_router(vehicles.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(watchlist.router)
app.include_router(admin.router)
app.include_router(anpr.router)


# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
def startup_event():
    """
    Initializes all streaming consumers and the camera
    health monitoring service when FastAPI starts.
    """

    # --------------------------------------------------------
    # Trajectory Consumer
    # --------------------------------------------------------

    trajectory_consumer.start_consumer()


    # --------------------------------------------------------
    # Alert Consumer
    # --------------------------------------------------------

    alert_consumer.start_consumer()


    # --------------------------------------------------------
    # Analytics Consumer
    # --------------------------------------------------------

    analytics_consumer.start_consumer()


    # --------------------------------------------------------
    # Camera Health Monitor
    # --------------------------------------------------------

    start_camera_health_monitor()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"]
)
def health_check():
    """
    GET /health

    Verifies backend status and Supabase connectivity.
    """

    supabase = get_supabase_client()

    db_status = (
        "connected"
        if supabase is not None
        else "disconnected (offline/fallback mode)"
    )

    return HealthCheckResponse(
        status="healthy",
        database=db_status,
        version="1.0.0"
    )


# ============================================================
# TEST OBSERVATION ENDPOINT
# ============================================================

@app.post(
    "/test/observation",
    tags=["Testing"]
)
async def test_observation(observation: dict):
    """
    Test endpoint for publishing an ANPR observation
    through the in-process observation bus.

    This endpoint is intentionally used for development/testing.

    Because the observation is published inside the same
    FastAPI/Uvicorn process, all registered consumers receive it:

        Observation
              ↓
        Observation Bus
              ↓
        ┌───────────────┬───────────────┐
        ↓               ↓               ↓
    Trajectory       Alert          Analytics
     Consumer       Consumer        Consumer
        ↓               ↓               ↓
    Trajectory        Alert          Analytics
    Database         Database         Data
    """

    # --------------------------------------------------------
    # Publish observation to in-memory event bus
    # --------------------------------------------------------

    published = await publish_observation(
        observation
    )


    # --------------------------------------------------------
    # Return test result
    # --------------------------------------------------------

    return {
        "published": published,
        "observation": observation
    }


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )