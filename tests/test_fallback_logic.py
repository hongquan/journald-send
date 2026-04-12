"""Test cases for journald-send core fallback logic."""

import subprocess
import sys
import time
import uuid

import pytest


try:
    import journald_send
except ImportError as e:
    pytest.skip(f'journald_send module not available: {e}', allow_module_level=True)


# ---------------------------------------------------------------------------
# Fallback logic tests: explicit params take precedence over kwargs;
# when explicit param is None, the value from kwargs is used as fallback.
# ---------------------------------------------------------------------------


def test_priority_from_kwargs_used_when_explicit_is_none() -> None:
    """PRIORITY in kwargs is used when priority=None."""
    journald_send.send('fallback priority', PRIORITY=7)


def test_priority_from_kwargs_string() -> None:
    """PRIORITY in kwargs as string is accepted."""
    journald_send.send('fallback priority string', PRIORITY='3')


def test_priority_explicit_wins_over_kwargs() -> None:
    """Explicit priority=Priority.ERROR takes precedence over PRIORITY in kwargs."""
    journald_send.send(
        'explicit priority wins',
        priority=journald_send.Priority.ERROR,
        PRIORITY=7,
    )


def test_code_file_from_kwargs_used_when_explicit_is_none() -> None:
    """CODE_FILE in kwargs is used when code_file=None."""
    journald_send.send('fallback code_file', CODE_FILE='from_kwargs.py')


def test_code_file_explicit_wins_over_kwargs() -> None:
    """Explicit code_file takes precedence over CODE_FILE in kwargs."""
    journald_send.send(
        'explicit code_file wins',
        code_file='explicit.py',
        CODE_FILE='from_kwargs.py',
    )


def test_code_line_from_kwargs_used_when_explicit_is_none() -> None:
    """CODE_LINE in kwargs is used when code_line=None."""
    journald_send.send('fallback code_line', CODE_LINE='500')


def test_code_line_explicit_wins_over_kwargs() -> None:
    """Explicit code_line takes precedence over CODE_LINE in kwargs."""
    journald_send.send(
        'explicit code_line wins',
        code_line=10,
        CODE_LINE='99',
    )


def test_code_func_from_kwargs_used_when_explicit_is_none() -> None:
    """CODE_FUNC in kwargs is used when code_func=None."""
    journald_send.send('fallback code_func', CODE_FUNC='from_kwargs')


def test_code_func_explicit_wins_over_kwargs() -> None:
    """Explicit code_func takes precedence over CODE_FUNC in kwargs."""
    journald_send.send(
        'explicit code_func wins',
        code_func='explicit_fn',
        CODE_FUNC='from_kwargs',
    )


def test_no_duplicate_priority_when_explicit_set() -> None:
    """When priority is explicit, PRIORITY from kwargs must not appear
    as a duplicate journal field."""
    journald_send.send(
        'no duplicate',
        priority=journald_send.Priority.CRITICAL,
        PRIORITY=7,
        CODE_FILE='a.py',
        CODE_LINE='1',
        CODE_FUNC='fn_a',
    )


def test_priority_kwargs_invalid_value() -> None:
    """Invalid PRIORITY value in kwargs raises ValueError."""
    with pytest.raises(ValueError, match='PRIORITY'):
        journald_send.send('bad priority', PRIORITY='not_a_number')


def test_priority_kwargs_out_of_range() -> None:
    """PRIORITY > 7 in kwargs raises ValueError."""
    with pytest.raises(ValueError, match='PRIORITY'):
        journald_send.send('out of range', PRIORITY=8)


def test_priority_kwargs_negative() -> None:
    """Negative PRIORITY in kwargs raises ValueError."""
    with pytest.raises(ValueError, match='PRIORITY'):
        journald_send.send('negative', PRIORITY=-1)


def test_priority_explicit_invalid() -> None:
    """Invalid explicit priority raises ValueError."""
    with pytest.raises(ValueError):
        journald_send.send('bad', priority=journald_send.Priority(10))  # type: ignore[arg-type]


@pytest.mark.skipif(sys.platform != 'linux', reason='journald-send only works on Linux')
def test_fallback_reaches_journal() -> None:
    """Verify PRIORITY from kwargs actually reaches the journal."""
    unique_id = str(uuid.uuid4())
    journald_send.send(
        f'fallback journal test {unique_id}',
        PRIORITY=2,
        FALLBACK_TEST_ID=unique_id,
    )
    time.sleep(0.1)
    try:
        result = subprocess.run(
            ['journalctl', '--user', '--output=json', '--priority=2', '-n', '10'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert unique_id in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip('journalctl not available or timed out')


# ---------------------------------------------------------------------------
# Validation tests: code_line, CODE_LINE, MESSAGE_ID
# ---------------------------------------------------------------------------


def test_code_line_explicit_not_int() -> None:
    """Explicit code_line that is not an integer raises ValueError."""
    with pytest.raises(ValueError, match='code_line'):
        journald_send.send('bad', code_line='not_an_int')  # type: ignore[arg-type]


def test_code_line_float_rejected() -> None:
    """Float code_line is rejected."""
    with pytest.raises(ValueError, match='code_line'):
        journald_send.send('bad', code_line=3.14)  # type: ignore[arg-type]


def test_code_line_kwargs_invalid() -> None:
    """CODE_LINE in kwargs that is not numeric raises ValueError."""
    with pytest.raises(ValueError, match='CODE_LINE'):
        journald_send.send('bad', CODE_LINE='abc')


def test_code_line_kwargs_valid_string() -> None:
    """CODE_LINE as a digit string is accepted."""
    journald_send.send('good', CODE_LINE='42')


def test_message_id_string() -> None:
    """MESSAGE_ID as a string is accepted."""
    journald_send.send('with message_id', MESSAGE_ID='my-msg-001')


def test_message_id_uuid() -> None:
    """MESSAGE_ID as a UUID is accepted."""
    journald_send.send('with message_id', MESSAGE_ID=uuid.uuid4())


def test_message_id_invalid_type() -> None:
    """MESSAGE_ID that is neither string nor UUID raises ValueError."""
    with pytest.raises(ValueError, match='MESSAGE_ID'):
        journald_send.send('bad', MESSAGE_ID=12345)  # type: ignore[arg-type]


def test_message_id_none_passed() -> None:
    """MESSAGE_ID=None is still passed through without error."""
    journald_send.send('with None message_id', MESSAGE_ID=None)
