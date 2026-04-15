#!/usr/bin/env python

"""Usage of the compliant send function with repeated keys support."""

import journald_send
from journald_send import Priority


# Basic usage with single entries
journald_send.send_compliant(
    'Hello, journald!',
    (('PRIORITY', str(Priority.INFO)),),
)

# Using repeated keys (unique feature of send_compliant)
# This allows multiple values for the same key
journald_send.send_compliant(
    'User action with multiple tags',
    (
        ('PRIORITY', str(Priority.NOTICE)),
        ('USER_ID', b'12345'),
        ('TAG', b'login'),
        ('TAG', b'successful'),  # Repeated TAG key
        ('TAG', b'verified'),  # Repeated TAG key again
    ),
)

# Mix of string and bytes values
journald_send.send_compliant(
    'Mixed value types',
    (
        ('PRIORITY', '6'),  # String value
        ('CUSTOM_FIELD', b'bytes'),  # Bytes value
        ('ANOTHER_FIELD', 'string'),  # String value (will be encoded to UTF-8)
    ),
)

# With code location information
journald_send.send_compliant(
    'Processing request',
    (
        ('CODE_FILE', __file__.encode()),
        ('CODE_LINE', b'32'),
        ('CODE_FUNC', b'main'),
        ('REQUEST_ID', b'req-12345'),
    ),
)
