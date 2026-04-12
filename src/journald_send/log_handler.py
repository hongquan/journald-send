"""Journal handler for the Python logging framework."""

from __future__ import annotations

import logging as _logging
import sys as _sys
from collections.abc import Callable
from typing import Any

from . import Priority, send as _send


class JournalHandler(_logging.Handler):
    """Handler for the Python standard logging framework.

    It is model after systemd-python's ``JournalHandler``,
    but using our :func:`journald_send.send` to forward the logs to ``journald``.

    Example usage::

        import logging
        from journald_send.log_handler import JournalHandler

        log = logging.getLogger("my-app")
        log.addHandler(JournalHandler(SYSLOG_IDENTIFIER="my-app"))
        log.warning("Something happened: %s", "detail")

    Fields attached to all messages can be specified as keyword arguments::

        JournalHandler(SYSLOG_IDENTIFIER="my-cool-app")

    The following journal fields are automatically included:
    ``MESSAGE``, ``PRIORITY``, ``LOGGER``, ``THREAD_NAME``,
    ``PROCESS_NAME``, ``CODE_FILE``, ``CODE_LINE``, ``CODE_FUNC``.

    A ``MESSAGE_ID`` can be supplied via the ``extra`` dict::

        import uuid

        mid = uuid.UUID("0123456789ABCDEF0123456789ABCDEF")
        log.warning("Message with ID", extra={"MESSAGE_ID": mid})
    """

    def __init__(
        self,
        level: int | str = _logging.NOTSET,
        *,
        sender: Callable[..., None] = _send,
        **kwargs: str,
    ) -> None:
        """Create a :class:`JournalHandler`.

        :param level: The logging level for this handler.
        :param sender: Callable used to send messages
            (default: :func:`journald_send.send`).
            Useful for testing.
        :param kwargs: Extra journal fields attached to every message
            (e.g. ``SYSLOG_IDENTIFIER="my-app"``).
        """
        super().__init__(level)

        for name in kwargs:
            if not name.replace('_', '').isalnum() or not name[0:1].isupper():
                raise ValueError(f'Invalid journal field name: {name!r}')

        if 'SYSLOG_IDENTIFIER' not in kwargs:
            kwargs['SYSLOG_IDENTIFIER'] = _sys.argv[0] if _sys.argv else 'python'

        self._extra = kwargs
        self._sender = sender

    @classmethod
    def with_args(cls, config: dict[str, Any] | None = None) -> JournalHandler:
        """Create a :class:`JournalHandler` from a configuration dictionary.

        Useful when the logging configuration syntax (e.g. ``dictConfig``) does
        not allow positional or keyword arguments in the usual way.

        :param config: Dictionary of arguments passed to the
            :class:`JournalHandler` constructor.
        """
        return cls(**(config or {}))

    def emit(self, record: _logging.LogRecord) -> None:
        """Write *record* to journald.

        ``MESSAGE`` is taken from the formatted log message, and
        ``PRIORITY``, ``LOGGER``, ``THREAD_NAME``, ``PROCESS_NAME``,
        ``CODE_FILE``, ``CODE_LINE``, ``CODE_FUNC`` are appended
        automatically.  ``MESSAGE_ID`` is used when present in *record*.

        :meta private:
        """
        try:
            msg = self.format(record)
            pri = self.map_priority(record.levelno)

            # Start with handler-level defaults
            extras: dict[str, Any] = dict(self._extra)

            # Attach exception text if available.
            # ``self.format(record)`` above already calls ``formatException``
            # internally so ``record.exc_text`` is populated.
            if record.exc_text:
                extras['EXCEPTION_TEXT'] = record.exc_text

            # Merge record extras (highest priority)
            extras.update((key, value) for key, value in record.__dict__.items() if key.isupper())

            # Resolve caller location if not already provided
            code_file = extras.pop('CODE_FILE', record.pathname)
            code_line = extras.pop('CODE_LINE', record.lineno)
            code_func = extras.pop('CODE_FUNC', record.funcName)

            # Extract optional MESSAGE_ID
            message_id = extras.pop('MESSAGE_ID', None)
            if message_id is not None:
                extras['MESSAGE_ID'] = str(message_id)

            # Filter out internal logging attributes that should not become
            # journald fields
            _internal = {
                'args',
                'asctime',
                'created',
                'exc_info',
                'exc_text',
                'filename',
                'funcName',
                'getMessage',
                'levelname',
                'levelno',
                'lineno',
                'module',
                'msecs',
                'msg',
                'name',
                'pathname',
                'process',
                'processName',
                'relativeCreated',
                'stack_info',
                'taskName',
                'thread',
                'threadName',
            }
            extras = {k: v for k, v in extras.items() if k not in _internal and k.isupper()}

            self._sender(
                msg,
                priority=Priority(pri),
                code_file=code_file,
                code_line=code_line,
                code_func=code_func,
                LOGGER=record.name,
                THREAD_NAME=record.threadName,
                PROCESS_NAME=record.processName,
                **extras,
            )
        # Follow `systemd-python` to catch general Exception.
        except Exception:  # noqa: BLE001
            self.handleError(record)

    @staticmethod
    def map_priority(levelno: int) -> int:
        """Map Python logging levels to journald priorities.

        Python levels (sparse): DEBUG=10, INFO=20, WARNING=30, ERROR=40,
        CRITICAL=50.

        Journald priorities (syslog): 0=EMERGENCY … 7=DEBUG.

        :meta private:
        """
        if levelno <= _logging.DEBUG:
            return Priority.DEBUG
        if levelno <= _logging.INFO:
            return Priority.INFO
        if levelno <= _logging.WARNING:
            return Priority.WARNING
        if levelno <= _logging.ERROR:
            return Priority.ERROR
        if levelno <= _logging.CRITICAL:
            return Priority.CRITICAL
        return Priority.ALERT
