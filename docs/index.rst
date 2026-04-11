journald-send Documentation
============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api

Introduction
=============

journald-send is a Python module for sending log messages to systemd-journald.
It provides a fast, native interface written in Rust using PyO3.

Features
--------

* Fast native implementation using Rust
* Direct communication with systemd-journald socket
* Support for standard journald fields (MESSAGE, PRIORITY, CODE_FILE, etc.)
* Custom field support
* Large payload support via memfd

Installation
------------

.. code-block:: bash

   pip install journald-send

Quick Start
-----------

.. code-block:: python

   import journald_send
   journald_send.send("Hello from journald-send!", PRIORITY="6")

Platform Support
----------------

* Linux (only platform with systemd-journald)
