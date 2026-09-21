import asyncio
import logging
from typing import Dict, Any

from backend.services.alert_engine import check_and_alert
from backend.streaming.bus import subscribe_to_observations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("consumers.alert")


def process_observation(observation: Dict[str, Any]) -> None:
    """
    Evaluates observation against watchlist via alert engine and logs processing.
    """
    plate = observation.get("plate_number", "UNKNOWN")
    camera = observation.get("camera_id", "UNKNOWN")
    timestamp = observation.get("timestamp", "UNKNOWN")

    logger.info(f"[AlertConsumer] Processed plate: {plate}, camera: {camera}, timestamp: {timestamp}")

    # Evaluate against watchlist rules
    alert = check_and_alert(observation)
    if alert:
        logger.warning(
            f"[AlertConsumer] ALERT TRIGGERED! Plate: {alert['plate']} | Type: {alert['alert_type']} | Severity: {alert['severity']}"
        )


def start_consumer() -> None:
    """
    Registers consumer callback with observation bus.
    """
    subscribe_to_observations(process_observation)
    logger.info("[AlertConsumer] Subscribed to observation stream.")


def main():
    logger.info("Starting Alert Consumer standalone listener...")
    start_consumer()
    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Alert Consumer stopped.")


if __name__ == "__main__":
    main()
