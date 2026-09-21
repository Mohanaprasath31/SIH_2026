"""
Streaming replay utilities.

Used by the admin API to replay stored ANPR observations
through the existing streaming bus.
"""

from typing import Any, Dict, List


def run_replay(
    observations: List[Dict[str, Any]] | None = None,
    **kwargs
):
    """
    Replays ANPR observations through the application's
    streaming infrastructure.

    This is currently a lightweight compatibility implementation.
    The real-time ANPR pipeline will publish observations directly
    in the later integration stage.
    """

    if observations is None:
        observations = []

    print(
        f"[REPLAY] Starting replay of "
        f"{len(observations)} observations."
    )

    return {
        "status": "completed",
        "observations_processed": len(observations),
    }