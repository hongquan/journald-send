"""Basic usage of journald-send."""

import journald_send
from journald_send import Priority


journald_send.send('Hello, journald!', priority=Priority.INFO)
