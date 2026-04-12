"""Custom fields example."""

import journald_send
from journald_send import Priority


journald_send.send(
    'User logged in',
    priority=Priority.NOTICE,
    USER_ID='12345',
    USERNAME='john_doe',
    SESSION_ID='abc123',
)
