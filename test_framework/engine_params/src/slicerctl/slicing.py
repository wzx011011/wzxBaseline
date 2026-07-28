from __future__ import annotations

import time
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Dict, Optional


class SlicingWaitTimeout(TimeoutError):
    """Raised when the slicer does not reach a completed state in time."""


def _percentage_0_100(value: Any) -> Optional[float]:
    try:
        percentage = float(value)
    except (TypeError, ValueError):
        return None
    if 0.0 <= percentage <= 1.0:
        return percentage * 100.0
    return percentage


def is_slicing_done(progress: Dict[str, Any]) -> bool:
    """Interpret the stable and transient slicing states exposed by the app."""
    state = str(progress.get("state") or "").lower()
    if state in {"began", "progress", "cancelled"}:
        return False
    if state == "completed":
        return True
    return bool(progress.get("all_plate_finished"))


def wait_for_slicing_done(
    engine_injector,
    *,
    timeout: float = 600.0,
    poll_interval: float = 1.0,
    command_timeout: float = 60.0,
    stall_timeout: float = 120.0,
    require_transition: bool = False,
    accept_idle_after: Optional[float] = None,
) -> Dict[str, Any]:
    """Poll ``get_slicing_progress`` until the current slice is complete.

    ``require_transition`` is useful for a re-slice where a completed state
    from the previous slice may still be visible. The first slice after a
    reset/load should leave it disabled so very small models cannot finish
    before the first poll and then time out incorrectly.
    """
    started = time.monotonic()
    deadline = started + max(0.0, float(timeout))
    saw_unfinished = not require_transition
    last_progress: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    last_percentage: Optional[float] = None
    last_change = started
    idle_since: Optional[float] = None

    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        per_command_timeout = min(max(0.01, float(command_timeout)), remaining)
        try:
            future = engine_injector.submit(
                "get_slicing_progress",
                {},
                timeout=per_command_timeout,
            )
            response = future.result(timeout=per_command_timeout)
        except FutureTimeoutError as exc:
            last_error = f"get_slicing_progress timed out: {exc}"
        except Exception as exc:  # connection loss and engine failures
            raise RuntimeError(f"get_slicing_progress failed: {exc}") from exc
        else:
            if response.get("code") == 0:
                payload = response.get("payload") or {}
                raw_progress = payload.get("progress")
                if isinstance(raw_progress, dict):
                    progress = dict(raw_progress)
                    progress["all_plate_finished"] = payload.get("all_plate_finished")
                    last_progress = progress

                    now = time.monotonic()
                    percentage = _percentage_0_100(progress.get("percentage"))
                    state = str(progress.get("state") or "").lower()
                    is_empty_idle = (
                        state == "no_slicing"
                        and (percentage is None or percentage < 0)
                        and not progress.get("all_plate_finished")
                    )
                    if is_empty_idle:
                        if idle_since is None:
                            idle_since = now
                        if accept_idle_after is not None and now - idle_since >= max(0.0, accept_idle_after):
                            progress["empty_slice"] = True
                            return progress
                    else:
                        idle_since = None

                    if percentage is not None:
                        if last_percentage is None or percentage != last_percentage:
                            last_percentage = percentage
                            last_change = now
                        elif (
                            not is_slicing_done(progress)
                            and stall_timeout > 0
                            and now - last_change >= stall_timeout
                        ):
                            raise SlicingWaitTimeout(
                                "slicing progress stalled for "
                                f"{stall_timeout}s (percentage={percentage:.3f}, "
                                f"state={progress.get('state') or 'unknown'})"
                            )

                    if not is_slicing_done(progress):
                        saw_unfinished = True
                    elif saw_unfinished:
                        return progress
                else:
                    last_error = f"missing progress payload: {response}"
            else:
                last_error = str(response.get("error") or response)

        sleep_for = min(max(0.0, float(poll_interval)), max(0.0, deadline - time.monotonic()))
        if sleep_for:
            time.sleep(sleep_for)

    percentage = _percentage_0_100((last_progress or {}).get("percentage"))
    percentage_text = f"{percentage:.3f}" if percentage is not None else "unknown"
    state = str((last_progress or {}).get("state") or "unknown")
    detail = last_error or f"percentage={percentage_text}, state={state}"
    raise SlicingWaitTimeout(f"slicing not finished in {timeout}s ({detail})")
