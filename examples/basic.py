#!/usr/bin/env python

"""Basic usage of journald-send."""

import journald_send
from journald_send import Priority


journald_send.send_compliant('Xin chào, journald! Đây là thư viện journald-send.', (('PRIORITY', str(Priority)),))
