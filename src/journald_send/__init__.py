"""Send messages to journald.

This module re-exports a simple `send` function and provides the `Priority`
IntEnum to name journald priority levels (0-7) per the systemd/journald API.
"""

from . import _core
from .base import Priority, send, send_compliant


__version__ = _core._VERSION


__all__ = ['send', 'send_compliant', 'Priority', '__version__']
