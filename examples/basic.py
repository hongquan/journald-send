"""Basic usage of journald-send."""

import journald_send


from journald_send import Priority
import journald_send

journald_send.send('Hello, journald!', priority=Priority.INFO)
