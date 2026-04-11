"""Custom fields example."""

import journald_send

journald_send.send(
    'User logged in',
    USER_ID='12345',
    USERNAME='john_doe',
    SESSION_ID='abc123',
)
