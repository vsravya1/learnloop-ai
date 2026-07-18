"""Bounded execution helpers for external agent requests."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError


def run_with_timeout(operation, timeout_seconds=15):
    """Run an external request without allowing it to block the Streamlit UI."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(operation)
    try:
        return future.result(timeout=timeout_seconds)
    except TimeoutError:
        future.cancel()
        print(f"Agent request timed out after {timeout_seconds} seconds.")
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
