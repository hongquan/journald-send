journald-send Documentation
============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api


Introduction
============

A lightweight Python library to send messages to `journald`_ (Linux system logging) using journald's native protocol.

Features
--------

* Simple function to log messages directly to `journald`_ using its native protocol
* Best for structured logging
* No dependencies on `systemd`_ or C-based ``libsystemd`` (only writes to journald, does not read or interact with systemd)

Installation
------------

Install via ``pip``:

.. code-block:: bash

   pip install journald-send

Or using ``uv``:

.. code-block:: bash

   uv add journald-send

Quick Start
-----------

.. code-block:: python

   import journald_send
   journald_send.send("Hello, journald!")

Platform Support
----------------

* Linux (only platform with `systemd`_)

.. _systemd: https://systemd.io/
.. _journald: https://www.freedesktop.org/wiki/Software/systemd/journal-files/