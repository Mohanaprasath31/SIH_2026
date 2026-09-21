import asyncio
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Query

from backend.streaming.replay import run_replay

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/start-replay")
async def start_replay(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = Query(None, description="Limit number of observations to replay"),
    delay_min: float = Query(1.0, description="Minimum spacing delay in seconds"),
    delay_max: float = Query(3.0, description="Maximum spacing delay in seconds")
):
    """
    POST /admin/start-replay
    Triggers observation replay engine in background task.
    """
    background_tasks.add_task(run_replay, limit=limit, delay_min=delay_min, delay_max=delay_max)
    
    return {
        "status": "started",
        "message": "Observation replay engine initiated in background.",
        "config": {
            "limit": limit,
            "delay_min": delay_min,
            "delay_max": delay_max
        }
    }
