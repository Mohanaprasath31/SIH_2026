import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.alert_engine import (
    plate_normalize,
    check_and_alert,
    get_generated_alerts,
    clear_generated_alerts,
    map_priority_to_severity
)
from backend.streaming.replay import run_replay
from backend.streaming.consumers import alert_consumer, trajectory_consumer, analytics_consumer


def test_plate_normalize():
    """
    Tests OCR confusion cleanup, whitespace stripping, and uppercase normalization.
    """
    print("[TEST] Running test_plate_normalize...")
    assert plate_normalize("tn-07 cb 4821") == "TNO7CB4B2I"
    assert plate_normalize("TN 70 K 3321") == "TN7OK332I"
    assert plate_normalize("  tn 10 w 8890 ") == "TNIOWBB9O"
    assert plate_normalize("tn-01-ax-9912") == "TNOIAX99I2"
    print("  [SUCCESS] Plate normalization passed.")


def test_priority_severity_mapping():
    """
    Tests watchlist priority to alert severity mapping.
    """
    print("[TEST] Running test_priority_severity_mapping...")
    assert map_priority_to_severity("Critical") == "High"
    assert map_priority_to_severity("High") == "High"
    assert map_priority_to_severity("Medium") == "Medium"
    assert map_priority_to_severity("Low") == "Low"
    print("  [SUCCESS] Priority mapping passed.")


async def test_replay_and_alerts():
    """
    Runs replay.py for a short window and asserts that test plates (High, Medium, Low priority)
    each produce an alert row with correct severity.
    """
    print("[TEST] Running test_replay_and_alerts...")
    clear_generated_alerts()

    # Subscribe consumers
    alert_consumer.start_consumer()
    trajectory_consumer.start_consumer()
    analytics_consumer.start_consumer()

    # Replay first 15 observations with fast delay for testing
    count = await run_replay(limit=15, delay_min=0.005, delay_max=0.01)
    assert count > 0, "Replay should process observations"

    alerts = get_generated_alerts()
    print(f"  [INFO] Generated {len(alerts)} alerts during replay test.")
    assert len(alerts) >= 3, f"Expected at least 3 alerts generated, got {len(alerts)}"

    # Map normalized plate -> alert severity
    plate_severity_map = {
        plate_normalize(a["plate"]): a["severity"] for a in alerts
    }

    # Verify High, Medium, and Low severity alerts were created
    high_plate_norm = plate_normalize("TN 01 AX 9912")
    med_plate_norm = plate_normalize("TN 70 K 3321")
    low_plate_norm = plate_normalize("TN 10 W 8890")

    assert high_plate_norm in plate_severity_map, f"Expected alert for high priority plate {high_plate_norm}"
    assert plate_severity_map[high_plate_norm] == "High"
    print(f"  [SUCCESS] High severity plate {high_plate_norm} verified.")

    assert med_plate_norm in plate_severity_map, f"Expected alert for medium priority plate {med_plate_norm}"
    assert plate_severity_map[med_plate_norm] == "Medium"
    print(f"  [SUCCESS] Medium severity plate {med_plate_norm} verified.")

    assert low_plate_norm in plate_severity_map, f"Expected alert for low priority plate {low_plate_norm}"
    assert plate_severity_map[low_plate_norm] == "Low"
    print(f"  [SUCCESS] Low severity plate {low_plate_norm} verified.")


def main():
    print("=" * 60)
    print("RUNNING ANPR STREAMING & ALERT ENGINE TEST SUITE")
    print("=" * 60)
    test_plate_normalize()
    test_priority_severity_mapping()
    asyncio.run(test_replay_and_alerts())
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
