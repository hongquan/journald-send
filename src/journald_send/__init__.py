"""Send messages to journald.

This module re-exports a simple `send` function and provides the `Priority`
IntEnum to name journald priority levels (0-7) per the systemd/journald API.
"""

from enum import IntEnum

from . import _core  # type: ignore[misc, import-not-found]  # compiled extension


# Read underscore-prefixed constants from the compiled extension directly.
# Access attributes directly — absence indicates a developer error and should raise at import time.
_PRI_EMERGENCY = _core._PRI_EMERGENCY
_PRI_ALERT = _core._PRI_ALERT
_PRI_CRITICAL = _core._PRI_CRITICAL
_PRI_ERROR = _core._PRI_ERROR
_PRI_WARNING = _core._PRI_WARNING
_PRI_NOTICE = _core._PRI_NOTICE
_PRI_INFO = _core._PRI_INFO
_PRI_DEBUG = _core._PRI_DEBUG


class Priority(IntEnum):
    """Integer enum representing journald priority levels backed by the native constants."""

    EMERGENCY = _PRI_EMERGENCY
    ALERT = _PRI_ALERT
    CRITICAL = _PRI_CRITICAL
    ERROR = _PRI_ERROR
    WARNING = _PRI_WARNING
    NOTICE = _PRI_NOTICE
    INFO = _PRI_INFO
    DEBUG = _PRI_DEBUG


def send(
    message: str,
    /,
    *,
    priority: Priority | None = None,
    code_file: str | None = None,
    code_line: int | None = None,
    code_func: str | None = None,
    **kwargs: object,
) -> None:
    """Send a message to journald.

    Args:
        message: The log message (MESSAGE field).
        code_file: Optional source file (CODE_FILE field).
        code_line: Optional source line (CODE_LINE field).
        code_func: Optional function name (CODE_FUNC field).
        **kwargs: Additional fields to include in the journal entry.
            Field names are uppercased and sanitized per journald conventions.
            Values are converted to strings.

    Raises:
        OSError: If not on Linux or if sending to journald fails.

    Example:
        >>> import journald_send
        >>> journald_send.send("Hello World", PRIORITY=6, MY_FIELD="custom")
    """

    # Validate that priority value is in valid range (0-7)
    if priority is not None and not (0 <= priority <= 7):
        raise ValueError("priority must be an integer between 0 and 7")

    _core.send(
        message,
        priority=priority,
        code_file=code_file,
        code_line=code_line,
        code_func=code_func,
        **kwargs,
    )


__all__ = ["send", "Priority"]
