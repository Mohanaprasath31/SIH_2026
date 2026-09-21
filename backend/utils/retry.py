import asyncio
import functools
import logging
import time
from typing import Callable, Any, List, Dict, Tuple, Optional

logger = logging.getLogger("utils.retry")

# In-memory dead letter queue for buffering operations that failed after max retries:
# list of (func, args, kwargs, timestamp)
_failed_queue: List[Tuple[Callable, Tuple[Any, ...], Dict[str, Any], float]] = []


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    buffer_on_failure: bool = True
):
    """
    Decorator/wrapper for synchronous functions with exponential backoff retries.
    Buffers failed calls into _failed_queue if max_retries exceeded.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"[Retry] Function {func.__name__} failed attempt {attempt}/{max_retries}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            logger.error(f"[Retry] Function {func.__name__} exhausted {max_retries} retries.")
            if buffer_on_failure:
                _failed_queue.append((func, args, kwargs, time.time()))
                logger.info(f"[Retry] Buffered failed call to queue. Total buffered: {len(_failed_queue)}")

            if last_exception:
                raise last_exception
            raise RuntimeError(f"Function {func.__name__} failed after retries")
        return wrapper
    return decorator


def async_retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    buffer_on_failure: bool = True
):
    """
    Decorator/wrapper for asynchronous functions with exponential backoff retries.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception: Optional[Exception] = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"[AsyncRetry] Function {func.__name__} failed attempt {attempt}/{max_retries}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            logger.error(f"[AsyncRetry] Function {func.__name__} exhausted {max_retries} retries.")
            if buffer_on_failure:
                _failed_queue.append((func, args, kwargs, time.time()))
                logger.info(f"[Retry] Buffered failed call to queue. Total buffered: {len(_failed_queue)}")

            if last_exception:
                raise last_exception
            raise RuntimeError(f"Function {func.__name__} failed after retries")
        return wrapper
    return decorator



def process_buffered_retries() -> int:
    """
    Attempts to re-execute all buffered failed operations. Returns count of successfully processed items.
    """
    global _failed_queue
    if not _failed_queue:
        return 0

    logger.info(f"[RetryQueue] Attempting to process {len(_failed_queue)} buffered failed calls...")
    remaining = []
    success_count = 0

    for func, args, kwargs, timestamp in _failed_queue:
        try:
            func(*args, **kwargs)
            success_count += 1
            logger.info(f"[RetryQueue] Successfully re-executed buffered call: {func.__name__}")
        except Exception as e:
            logger.warning(f"[RetryQueue] Re-execution failed for {func.__name__}: {e}")
            remaining.append((func, args, kwargs, timestamp))

    _failed_queue = remaining
    return success_count


def get_buffered_queue_count() -> int:
    return len(_failed_queue)


def clear_buffered_queue() -> None:
    global _failed_queue
    _failed_queue = []
