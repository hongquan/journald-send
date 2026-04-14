#!/usr/bin/env python

"""Custom fields example."""

import journald_send
from journald_send import Priority


journald_send.send_compliant(
    'Có người đăng nhập',
    (
        ('PRIORITY', str(Priority)),
        ('USER_ID', b'12345'),
        ('USERNAME', 'Tèo'.encode()),
        ('SESSION_ID', b'abc123'),
    ),
)
