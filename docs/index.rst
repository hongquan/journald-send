journald-send Documentation
============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api


Introduction
============

`journald_send` is a Python module for sending log messages to `journald`_.
It provides a fast, native interface written in `Rust`_ using `PyO3`_.

Features
--------

* Fast native implementation using `Rust`
* Direct communication with :code:`systemd-journald` socket
* Support for standard `journald`_ fields ( ``MESSAGE``, ``PRIORITY``, ``CODE_FILE``, etc.)
* Custom field support
* Large payload support via `memfd`

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
   journald_send.send("Hello from journald-send!", PRIORITY="6")

Platform Support
----------------

* Linux (only platform with `systemd`_)

.. _systemd: https://systemd.io/
.. _journald: https://www.freedesktop.org/wiki/Software/systemd/journal-files/
.. _Rust: https://www.rust-lang.org
.. _PyO3: https://github.com/PyO3