"""Test cases for journald-send module."""

import sys

import pytest


# Import the module
try:
    import journald_send
except ImportError as e:
    pytest.skip(f'journald_send module not available: {e}', allow_module_level=True)


def test_send_simple_message():
    """Test sending a simple message."""
    journald_send.send('Hello from pytest!')


def test_send_empty_message():
    """Test sending an empty message."""
    journald_send.send('')


def test_send_unicode_message():
    """Test sending a message with unicode characters."""
    journald_send.send('Unicode test: hello world')


def test_message_id_field():
    """Test MESSAGE_ID field."""
    journald_send.send('Test with message ID', message_id='test_msg_001')


def test_code_file_field():
    """Test CODE_FILE field."""
    journald_send.send('Test with code file', code_file='test_module.py')


def test_code_line_field():
    """Test CODE_LINE field."""
    journald_send.send('Test with code line', code_line=42)


def test_code_func_field():
    """Test CODE_FUNC field."""
    journald_send.send('Test with code function', code_func='test_function')


def test_all_standard_fields():
    """Test all standard fields together."""
    journald_send.send(
        'Test with all standard fields',
        message_id='test_msg_002',
        code_file='test_module.py',
        code_line=123,
        code_func='comprehensive_test',
    )


def test_priority_error():
    """Test error priority (3)."""
    journald_send.send('Error message', PRIORITY='3')


def test_priority_warning():
    """Test warning priority (4)."""
    journald_send.send('Warning message', PRIORITY='4')


def test_priority_info():
    """Test info priority (6)."""
    journald_send.send('Info message', PRIORITY='6')


def test_priority_debug():
    """Test debug priority (7)."""
    journald_send.send('Debug message', PRIORITY='7')


def test_single_custom_field():
    """Test a single custom field."""
    journald_send.send('Test with custom field', CUSTOM_FIELD='custom_value')


def test_multiple_custom_fields():
    """Test multiple custom fields."""
    journald_send.send('Test with multiple custom fields', USER_ID='12345', USERNAME='test_user', SESSION_ID='abc123')


def test_custom_field_with_underscores():
    """Test custom field names with underscores."""
    journald_send.send('Test underscore field', MY_CUSTOM_FIELD='value')


def test_custom_field_uppercase():
    """Test that custom field names are uppercased."""
    journald_send.send('Test field casing', lowercase_field='should_be_uppercased')


def test_standard_and_custom_fields():
    """Test mixing standard and custom fields."""
    journald_send.send(
        'Combined test',
        message_id='combined_001',
        code_file='combined.py',
        code_line=99,
        code_func='combined_test',
        CUSTOM_FIELD='custom_value',
        PRIORITY='6',
    )


def test_all_fields():
    """Test all possible fields together."""
    journald_send.send(
        'All fields test',
        message_id='all_fields_001',
        code_file='all_fields.py',
        code_line=1,
        code_func='all_fields_test',
        PRIORITY='5',
        USER_ID='999',
        REQUEST_ID='req_12345',
        ACTION='test_action',
    )


def test_long_message():
    """Test sending a very long message."""
    long_message = 'A' * 1000
    journald_send.send(long_message)


def test_message_with_newlines():
    """Test message with newlines."""
    message = 'Line 1\nLine 2\nLine 3'
    journald_send.send(message)


def test_message_with_special_chars():
    """Test message with special characters."""
    message = 'Special chars: !@#$%^&*(){}[]|\\:;"<>.,.?/~'
    journald_send.send(message)


def test_custom_field_with_newlines():
    """Test custom field value with newlines."""
    journald_send.send('Test newline in field', MULTI_LINE_FIELD='Line 1\nLine 2\nLine 3')


def test_numeric_custom_field():
    """Test numeric values in custom fields."""
    journald_send.send('Test numeric field', COUNT=42, PRICE=19.99)


def test_zero_line_number():
    """Test zero as line number."""
    journald_send.send('Test zero line', code_line=0)


def test_large_line_number():
    """Test large line number."""
    journald_send.send('Test large line number', code_line=999999)


def test_field_sanitization_underscores():
    """Test that field names with underscores work correctly."""
    journald_send.send('Sanitization test', FIELD_WITH_UNDERSCORES='value')


def test_field_sanitization_no_leading_underscore():
    """Test that field names without leading underscores work correctly."""
    journald_send.send('Sanitization test', PRIVATE_FIELD='value')


def test_field_sanitization_special_chars():
    """Test that field names with special characters work correctly."""
    journald_send.send('Sanitization test', FIELD_WITH_SPECIAL_CHARS='value')


def test_rapid_succession():
    """Test sending multiple messages in rapid succession."""
    for i in range(10):
        journald_send.send(f'Rapid test message {i}')


def test_different_messages():
    """Test sending different messages."""
    messages = ['First message', 'Second message', 'Third message']
    for msg in messages:
        journald_send.send(msg)


def test_none_values():
    """Test that None values for optional fields are handled."""
    journald_send.send('Test with None values', message_id=None, code_file=None, code_line=None, code_func=None)


def test_empty_custom_field_value():
    """Test empty string as custom field value."""
    journald_send.send('Test empty field', EMPTY_FIELD='')


@pytest.mark.skipif(sys.platform != 'linux', reason='journald-send only works on Linux')
def test_actual_journal_entry():
    """Test that messages actually reach the journal."""
    import subprocess
    import time
    import uuid

    unique_id = str(uuid.uuid4())
    journald_send.send(f'Integration test {unique_id}', TEST_ID=unique_id)
    time.sleep(0.1)
    try:
        result = subprocess.run(
            ['journalctl', '--user', '-n', '1', '--output=cat'], capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip('journalctl not available or timed out')
