"""Send messages to journald.

This module re-exports a simple `send` function and provides the `Priority`
IntEnum to name journald priority levels (0-7) per the systemd/journald API.
"""

from enum import IntEnum
from uuid import UUID

from . import _core  # type: ignore[misc, import-not-found, attr-defined]  # compiled extension


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
__version__ = _core._VERSION


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

    :param message: The log message (MESSAGE field).
    :param priority: Log priority level (0–7).
    :param code_file: Source file (CODE_FILE field).
    :param code_line: Source line (CODE_LINE field).
    :param code_func: Function name (CODE_FUNC field).
    :param kwargs: Additional fields to include in the journal entry.
        Field names are uppercased and sanitized per journald conventions.
        Values are converted to strings.  ``CODE_LINE`` must be an integer,
        ``MESSAGE_ID`` must be a string or :class:`uuid.UUID`.

    When both an explicit parameter and the corresponding keyword argument
    (e.g. ``priority`` vs ``PRIORITY``) are given, the explicit parameter
    takes precedence.  When the explicit parameter is ``None``, the value
    from *kwargs* is used as a fallback.

    :raises OSError: If not on Linux or if sending to journald fails.
    :raises ValueError: If *priority* (or ``PRIORITY`` in *kwargs*) is out of range,
        *code_line* (or ``CODE_LINE`` in *kwargs*) is not an integer,
        or *MESSAGE_ID* in *kwargs* is not a string or :class:`uuid.UUID`.

    Example::

        import journald_send
        journald_send.send("Hello World", priority=6, MY_FIELD="custom")
    """

    # Validate that the explicit priority (IntEnum) is in range
    if priority is not None and not (0 <= priority <= 7):
        raise ValueError('priority must be an integer between 0 and 7')

    # Validate PRIORITY in kwargs (accepts int or str, but not Priority enum)
    extra_priority = kwargs.get('PRIORITY')
    if extra_priority is not None:
        try:
            p = int(str(extra_priority))
        except (ValueError, TypeError):
            raise ValueError('PRIORITY must be an integer between 0 and 7') from None
        if not (0 <= p <= 7):
            raise ValueError('PRIORITY must be an integer between 0 and 7')

    # Validate code_line (explicit) and CODE_LINE (kwargs)
    extra_code_line = kwargs.get('CODE_LINE')
    if code_line is not None and not isinstance(code_line, int):
        raise ValueError('code_line must be an integer')
    if extra_code_line is not None:
        try:
            int(str(extra_code_line))
        except (ValueError, TypeError):
            raise ValueError('CODE_LINE must be an integer') from None

    # Validate MESSAGE_ID in kwargs (string or UUID)
    extra_message_id = kwargs.get('MESSAGE_ID')
    if extra_message_id is not None and not isinstance(extra_message_id, (str, UUID)):
        raise ValueError('MESSAGE_ID must be a string or uuid.UUID')

    _core.send(
        message,
        priority=priority,
        code_file=code_file,
        code_line=code_line,
        code_func=code_func,
        **kwargs,
    )


__all__ = ['send', 'Priority', '__version__']
