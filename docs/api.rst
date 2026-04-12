API Reference
=============

journald_send.send
------------------

.. autofunction:: journald_send.send

journald_send.Priority
----------------------

.. autoclass:: journald_send.Priority
   :members:

Standard Fields
----------------

The following standard journald fields are supported:

* **MESSAGE**: The log message (required)
* **MESSAGE_ID**: Optional message identifier
* **CODE_FILE**: Optional source file path
* **CODE_LINE**: Optional source line number
* **CODE_FUNC**: Optional function name

Custom Fields
-------------

Any additional keyword arguments are treated as custom journald fields.
Field names are automatically sanitized and converted to uppercase.

.. code-block:: python

   import journald_send
   journald_send.send(
       "Custom log entry",
       CUSTOM_FIELD="value",
       ANOTHER_FIELD=123
   )

Priority Levels
---------------

Priority levels can be set using the ``priority`` parameter with the :class:`~journald_send.Priority` enum:

.. code-block:: python

   import journald_send
   from journald_send import Priority

   journald_send.send("Error occurred", priority=Priority.ERROR)

Available priority levels:

* ``Priority.EMERGENCY`` (0): Emergency
* ``Priority.ALERT`` (1): Alert
* ``Priority.CRITICAL`` (2): Critical
* ``Priority.ERROR`` (3): Error
* ``Priority.WARNING`` (4): Warning
* ``Priority.NOTICE`` (5): Notice
* ``Priority.INFO`` (6): Informational (default)
* ``Priority.DEBUG`` (7): Debug
