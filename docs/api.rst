API Reference
=============

journald_send.send
------------------

.. autofunction:: journald_send.send

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

Standard syslog priority levels can be set using the PRIORITY field:

* 0: Emergency
* 1: Alert
* 2: Critical
* 3: Error
* 4: Warning
* 5: Notice
* 6: Informational (default)
* 7: Debug
