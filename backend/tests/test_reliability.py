import asyncio
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.streaming.bus import (
    publish_observation,
    get_stored_vehicle_observations,
    clear_processed_events_store
)
from backend.streaming.consumers.trajectory_consumer import (
    process_observation as process_trajectory,
    get_trajectories,
    clear_trajectories_store
)
from backend.utils.time_utils import normalize_timestamp_utc, check_heartbeat_drift
from backend.utils.retry import retry_with_backoff, get_buffered_queue_count, clear_buffered_queue


async def test_idempotency_double_replay():
    """
    Replays the exact same observation twice and asserts only ONE row exists in vehicle_observations.
    """
    print("[TEST] Running test_idempotency_double_replay...")
    clear_processed_events_store()

    test_obs = {
        "observation_id": "99999999-9999-4999-a999-999999999999",
        "event_id": "evt-99999999-test-idempotency",
        "camera_id": "11111111-1111-4111-a111-111111111101",
        "plate_number": "TN 99 RE 1001",
        "timestamp": "2026-09-11T20:00:00+05:30",
        "location": "POINT(80.2462 12.9815)",
        "ocr_confidence": 0.98,
        "vehicle_type": "Sedan",
        "direction": "Southbound"
    }

    # First publication attempt
    res1 = await publish_observation(test_obs)
    assert res1 is True, "First publication of observation should succeed"

    # Second publication attempt (exact same payload & event_id)
    res2 = await publish_observation(test_obs)
    assert res2 is False, "Second publication of duplicate event_id should be skipped by idempotency"

    stored_obs = get_stored_vehicle_observations()
    matching_rows = [o for o in stored_obs if o.get("event_id") == "evt-99999999-test-idempotency"]

    assert len(matching_rows) == 1, f"Expected exactly 1 stored observation row, found {len(matching_rows)}"
    print("  [SUCCESS] Idempotency verified: duplicate replay skipped, exactly 1 row stored.")


def test_trajectory_unknown_interval_gap():
    """
    Verifies that observations for the same plate separated by >10 minutes (600s)
    are marked with segment_status = 'gap' and has_gap = True.
    """
    print("[TEST] Running test_trajectory_unknown_interval_gap...")
    clear_trajectories_store()

    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(minutes=2)    # 2 mins gap -> continuous
    t2 = t0 + timedelta(minutes=15)   # 13 mins gap from t1 -> GAP (> 10 mins threshold)

    obs1 = {
        "event_id": "e1",
        "observation_id": "o1",
        "plate_number": "TN 55 GAP 777",
        "camera_id": "cam-1",
        "timestamp": t0.isoformat(),
        "ocr_confidence": 0.95
    }
    obs2 = {
        "event_id": "e2",
        "observation_id": "o2",
        "plate_number": "TN 55 GAP 777",
        "camera_id": "cam-2",
        "timestamp": t1.isoformat(),
        "ocr_confidence": 0.96
    }
    obs3 = {
        "event_id": "e3",
        "observation_id": "o3",
        "plate_number": "TN 55 GAP 777",
        "camera_id": "cam-3",
        "timestamp": t2.isoformat(),
        "ocr_confidence": 0.97
    }

    process_trajectory(obs1)
    process_trajectory(obs2)
    process_trajectory(obs3)

    trajectories = get_trajectories()
    plate_points = trajectories.get("TN 55 GAP 777", [])

    assert len(plate_points) == 3
    assert plate_points[0]["segment_status"] == "continuous"
    assert plate_points[1]["segment_status"] == "continuous"
    assert plate_points[2]["segment_status"] == "gap"
    assert plate_points[2]["has_gap"] is True
    print("  [SUCCESS] Trajectory gap detection (>10 min threshold) verified.")


def test_timestamp_utc_normalization_and_drift():
    """
    Tests UTC timestamp normalization and camera heartbeat drift detection.
    """
    print("[TEST] Running test_timestamp_utc_normalization_and_drift...")
    
    # 1. UTC normalization
    raw_ts = "2026-09-11T12:00:00+05:30"
    utc_ts = normalize_timestamp_utc(raw_ts)
    assert "+00:00" in utc_ts or "Z" in utc_ts or utc_ts.endswith("+00:00")
    
    # 2. Heartbeat drift detection
    drift_ts = (datetime.now(timezone.utc) - timedelta(seconds=12)).isoformat()
    has_drifted, drift_secs = check_heartbeat_drift(drift_ts, threshold_seconds=5.0)
    assert has_drifted is True
    assert drift_secs >= 10.0
    print("  [SUCCESS] UTC timestamp normalization and drift detection verified.")


def main():
    print("=" * 60)
    print("RUNNING BACKEND RELIABILITY TEST SUITE")
    print("=" * 60)
    asyncio.run(test_idempotency_double_replay())
    test_trajectory_unknown_interval_gap()
    test_timestamp_utc_normalization_and_drift()
    print("=" * 60)
    print("ALL RELIABILITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
