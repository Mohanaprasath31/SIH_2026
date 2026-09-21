import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from backend.streaming.bus import subscribe_to_observations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("consumers.analytics")

# In-memory storage for hourly volume counts: { "YYYY-MM-DD THH": count }
_hourly_volume_counts: Dict[str, int] = {}
_total_observations_count: int = 0


def process_observation(observation: Dict[str, Any]) -> None:
    """
    Increments hourly volume counter for observation timestamp and logs processing.
    """
    global _total_observations_count
    plate = observation.get("plate_number", "UNKNOWN")
    camera = observation.get("camera_id", "UNKNOWN")
    timestamp_str = observation.get("timestamp", "UNKNOWN")

    # Extract hour key (e.g., '2026-09-10T08')
    hour_key = timestamp_str[:13] if len(timestamp_str) >= 13 else "unknown_hour"

    _hourly_volume_counts[hour_key] = _hourly_volume_counts.get(hour_key, 0) + 1
    _total_observations_count += 1

    current_hour_total = _hourly_volume_counts[hour_key]
    logger.info(
        f"[AnalyticsConsumer] Processed plate: {plate}, camera: {camera}, timestamp: {timestamp_str} | "
        f"Hour {hour_key}: {current_hour_total} obs | Total: {_total_observations_count}"
    )


def start_consumer() -> None:
    """
    Registers consumer callback with observation bus.
    """
    subscribe_to_observations(process_observation)
    logger.info("[AnalyticsConsumer] Subscribed to observation stream.")


def clear_hourly_volume_store() -> None:
    """
    Clears hourly volume counter store for test resets.
    """
    global _hourly_volume_counts, _total_observations_count
    _hourly_volume_counts = {}
    _total_observations_count = 0


def get_analytics_summary() -> Dict[str, Any]:
    return {
        "total_observations": _total_observations_count,
        "hourly_counts": dict(_hourly_volume_counts)
    }


def main():
    logger.info("Starting Analytics Consumer standalone listener...")
    start_consumer()
    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Analytics Consumer stopped.")


if __name__ == "__main__":
    main()
