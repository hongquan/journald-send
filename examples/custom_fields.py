#!/usr/bin/env python

"""Custom fields example."""

import journald_send
from journald_send import Priority


journald_send.send_compliant(
    'Có người đăng nhập',
    (
        ('PRIORITY', str(Priority.NOTICE)),
        ('USER_ID', '12345'),
        ('USERNAME', 'Tèo'),
        ('SESSION_ID', 'abc123'),
    ),
)
