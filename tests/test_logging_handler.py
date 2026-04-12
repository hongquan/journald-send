"""Tests for journald_send.log_handler."""

from __future__ import annotations

import logging
import uuid

import pytest

from journald_send.log_handler import JournalHandler


def make_logger(
    name: str = 'test_logger',
    handler: JournalHandler | None = None,
) -> logging.Logger:
    """Create a logger with the given handler attached."""
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    if handler is not None:
        logger.addHandler(handler)
    return logger


def test_emit_calls_send() -> None:
    """Basic emit should call the sender with MESSAGE and PRIORITY."""
    call_kwargs: dict[str, str] = {}

    def fake_sender(message: str, **kwargs: str) -> None:
        call_kwargs.update(kwargs)

    handler = JournalHandler(sender=fake_sender)
    logger = make_logger(handler=handler)
    logger.info('hello world')

    assert call_kwargs['LOGGER'] == 'test_logger'


def test_syslog_identifier_default() -> None:
    """SYSLOG_IDENTIFIER defaults to sys.argv[0]."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    make_logger(handler=handler).info('test')

    assert calls[0][1]['SYSLOG_IDENTIFIER']


def test_syslog_identifier_custom() -> None:
    """SYSLOG_IDENTIFIER can be overridden."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender, SYSLOG_IDENTIFIER='my-app')
    make_logger(handler=handler).info('test')

    assert calls[0][1]['SYSLOG_IDENTIFIER'] == 'my-app'


def test_code_location_fields() -> None:
    """CODE_FILE, CODE_LINE, CODE_FUNC should be taken from the LogRecord."""
    call_kwargs: dict[str, str | None] = {}

    def fake_sender(
        message: str,  # noqa: ARG001
        code_file: str | None = None,
        code_line: int | None = None,
        code_func: str | None = None,
        **_kwargs: str,
    ) -> None:
        call_kwargs['code_file'] = code_file
        call_kwargs['code_line'] = str(code_line)
        call_kwargs['code_func'] = code_func

    handler = JournalHandler(sender=fake_sender)
    make_logger(handler=handler).info('test')

    assert call_kwargs['code_file'] is not None
    code_line = call_kwargs['code_line']
    assert code_line is not None and int(code_line) > 0
    assert call_kwargs['code_func'] == 'test_code_location_fields'


def test_message_id_from_extra() -> None:
    """MESSAGE_ID should be forwarded from record extras."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    logger = make_logger(handler=handler)
    mid = uuid.UUID('0123456789ABCDEF0123456789ABCDEF')
    logger.warning('msg with id', extra={'MESSAGE_ID': mid})

    _, fields = calls[0]
    assert 'MESSAGE_ID' in fields


def test_exception_text_attached() -> None:
    """EXCEPTION_TEXT should contain formatted exception info."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    logger = make_logger(handler=handler)

    try:
        raise ValueError('boom')
    except ValueError:
        logger.exception('failed')

    _, fields = calls[0]
    assert 'EXCEPTION_TEXT' in fields
    assert 'ValueError' in fields['EXCEPTION_TEXT']


def test_record_non_upper_attrs_excluded() -> None:
    """Non-uppercase LogRecord attributes should not leak into journal fields."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    make_logger(handler=handler).info('test')

    _, fields = calls[0]
    for key in ('name', 'levelno', 'pathname', 'funcName', 'threadName'):
        assert key not in fields


def test_extra_fields_preserved() -> None:
    """Uppercase extras should be forwarded."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    logger = make_logger(handler=handler)
    logger.info('test', extra={'REQUEST_ID': 'abc123'})

    _, fields = calls[0]
    assert fields.get('REQUEST_ID') == 'abc123'


def test_handler_extra_overridden_by_record() -> None:
    """Record extras should override handler-level extras."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender, SOURCE='handler_default')
    logger = make_logger(handler=handler)
    logger.info('test', extra={'SOURCE': 'record_value'})

    _, fields = calls[0]
    assert fields['SOURCE'] == 'record_value'


def test_invalid_field_name() -> None:
    """Invalid field names in kwargs should raise ValueError."""
    with pytest.raises(ValueError, match='Invalid journal field name'):
        exec("JournalHandler(**{'invalid-field': 'x'})", {'JournalHandler': JournalHandler})


def test_with_args() -> None:
    """with_args should create a handler from a config dict."""
    handler = JournalHandler.with_args(
        {'SYSLOG_IDENTIFIER': 'my-app', 'level': logging.DEBUG},
    )
    assert handler._extra['SYSLOG_IDENTIFIER'] == 'my-app'


def test_with_args_empty() -> None:
    """with_args with None/empty dict should work."""
    handler = JournalHandler.with_args(None)
    assert handler is not None
    handler2 = JournalHandler.with_args({})
    assert handler2 is not None


def test_thread_and_process_names() -> None:
    """THREAD_NAME and PROCESS_NAME should be set."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    make_logger(handler=handler).info('test')

    _, fields = calls[0]
    assert 'THREAD_NAME' in fields
    assert 'PROCESS_NAME' in fields


def test_formatted_message() -> None:
    """Handler should use the formatter."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_sender(message: str, **kwargs: str) -> None:
        calls.append((message, {k: v for k, v in kwargs.items()}))

    handler = JournalHandler(sender=fake_sender)
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger = make_logger(handler=handler)
    logger.warning('warning msg')

    assert calls[0][0].startswith('[WARNING]')
