import asyncio
import logging
import uuid
from typing import Callable, List, Dict, Any, Set, Awaitable, Union

from backend.db import get_supabase_client
from backend.utils.time_utils import normalize_timestamp_utc

logger = logging.getLogger("streaming.bus")

# Type for subscriber callback (can be async or sync)
SubscriberCallback = Callable[[Dict[str, Any]], Union[None, Awaitable[None]]]

_subscribers: List[SubscriberCallback] = []

# Set of processed event IDs for idempotency
_processed_event_ids: Set[str] = set()

# In-memory stored vehicle observations
_vehicle_observations_db: List[Dict[str, Any]] = []


def subscribe_to_observations(callback: SubscriberCallback) -> None:
    """
    Subscribe an async or sync callback to receive observation events.
    """
    if callback not in _subscribers:
        _subscribers.append(callback)
        logger.info(
            f"Subscribed new consumer to observations channel. "
            f"Total subscribers: {len(_subscribers)}"
        )


def unsubscribe_from_observations(callback: SubscriberCallback) -> None:
    """
    Unsubscribe a callback from observation events.
    """
    if callback in _subscribers:
        _subscribers.remove(callback)


def is_event_processed(event_id: str) -> bool:
    """
    Check whether an event_id has already been processed.
    """
    return event_id in _processed_event_ids


def get_stored_vehicle_observations() -> List[Dict[str, Any]]:
    """
    Return stored vehicle observations from the in-memory store.
    """
    return list(_vehicle_observations_db)


def clear_processed_events_store() -> None:
    """
    Clear idempotency store and in-memory observations.
    """
    global _processed_event_ids, _vehicle_observations_db

    _processed_event_ids.clear()
    _vehicle_observations_db.clear()


async def publish_observation(observation: Dict[str, Any]) -> bool:
    """
    Publish an already-ingested observation to the streaming system.

    Database persistence is handled by /anpr/ingest.
    This function is responsible for:
      1. Event ID generation
      2. Idempotency
      3. In-memory storage
      4. Local consumer dispatch
      5. Optional Supabase Realtime broadcast

    Returns:
        True  -> observation published
        False -> duplicate event skipped
    """

    # ---------------------------------------------------------
    # 1. Generate observation/event IDs
    # ---------------------------------------------------------

    obs_id = observation.get("observation_id") or str(uuid.uuid4())

    event_id = observation.get("event_id") or f"evt-{obs_id}"

    observation["observation_id"] = obs_id
    observation["event_id"] = event_id

    # ---------------------------------------------------------
    # 2. Normalize timestamp
    # ---------------------------------------------------------

    observation["timestamp"] = normalize_timestamp_utc(
        observation.get("timestamp")
    )

    # ---------------------------------------------------------
    # 3. Idempotency check
    # ---------------------------------------------------------

    if is_event_processed(event_id):
        logger.warning(
            f"[Idempotency] Duplicate event_id '{event_id}' detected! "
            f"Skipping re-processing."
        )
        return False

    # Mark event as processed
    _processed_event_ids.add(event_id)

    # ---------------------------------------------------------
    # 4. Store in memory
    # ---------------------------------------------------------

    _vehicle_observations_db.append(dict(observation))

    logger.info(
        f"[Bus] Publishing observation: "
        f"{observation.get('plate_number', 'UNKNOWN')} | "
        f"Camera: {observation.get('camera_id', 'UNKNOWN')} | "
        f"Event: {event_id}"
    )

    # ---------------------------------------------------------
    # 5. Dispatch to local subscribers
    # ---------------------------------------------------------

    for callback in list(_subscribers):
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(observation)
            else:
                callback(observation)

        except Exception as e:
            logger.error(
                f"Error in observation subscriber callback "
                f"{callback}: {e}"
            )

    # ---------------------------------------------------------
    # 6. Optional Supabase Realtime broadcast
    # ---------------------------------------------------------

    supabase = get_supabase_client()

    if supabase and hasattr(supabase, "realtime"):
        try:
            realtime_client = getattr(supabase, "realtime", None)

            if realtime_client and hasattr(
                realtime_client,
                "channel"
            ):
                channel = realtime_client.channel("observations")

                if hasattr(channel, "send_broadcast"):
                    await channel.send_broadcast(
                        event="observation",
                        payload=observation
                    )

                    logger.debug(
                        "[Bus] Observation broadcast through "
                        "Supabase Realtime."
                    )

        except Exception as e:
            logger.debug(
                f"[Bus] Supabase Realtime broadcast skipped: {e}"
            )

    return True