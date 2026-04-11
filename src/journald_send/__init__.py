"""Send messages to journald."""

from ._core import send as _send  # type: ignore[misc, import-not-found]


def send(
    message: str,
    /,
    *,
    message_id: str | None = None,
    code_file: str | None = None,
    code_line: int | None = None,
    code_func: str | None = None,
    **kwargs: object,
) -> None:
    """Send a message to journald.

    Args:
        message: The log message (MESSAGE field).
        message_id: Optional message ID (MESSAGE_ID field).
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

    _send(
        message,
        message_id=message_id,
        code_file=code_file,
        code_line=code_line,
        code_func=code_func,
        **kwargs,
    )


__all__ = ["send"]
