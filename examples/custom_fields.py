"""Custom fields example."""

from journald_send import Priority
import journald_send


journald_send.send(
    'User logged in',
    priority=Priority.NOTICE,
    USER_ID='12345',
    USERNAME='john_doe',
    SESSION_ID='abc123',
)
