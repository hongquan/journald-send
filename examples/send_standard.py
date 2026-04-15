#!/usr/bin/env python

"""Basic usage of the standard send function."""

import journald_send
from journald_send import Priority


# Simple message with default priority
journald_send.send('Hello, journald!')

# Message with priority
journald_send.send('This is a warning', priority=Priority.WARNING)

# Message with custom fields
journald_send.send(
    'User logged in',
    priority=Priority.INFO,
    USER_ID='12345',
    USERNAME='john_doe',
    SESSION_ID='abc123',
)

# Message with code location
journald_send.send(
    'Processing data',
    priority=Priority.DEBUG,
    code_file=__file__,
    code_line=26,
    code_func='main',
)
