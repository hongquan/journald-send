API Reference
=============

Standard send function
----------------------

.. autofunction:: journald_send.send

Compliant send function
-----------------------

.. autofunction:: journald_send.send_compliant

The ``send_compliant`` function accepts a message and a sequence of key-value tuples, allowing for repeated keys,
which is compliant with the journald native protocol. Keys are automatically sanitized and
converted to uppercase. The ``MESSAGE`` key in entries is ignored (use the ``message`` parameter instead).
Values can be ``str`` (encoded to UTF-8) or ``bytes``.

This function may differ from common Python usage patterns.

.. code-block:: python

   import journald_send
   journald_send.send_compliant('Hello World', (
       ('PRIORITY', b'6'),
       ('CUSTOM_FIELD', b'custom value'),
   ))

Standard fields
~~~~~~~~~~~~~~~

The following standard journald fields are supported:

* **MESSAGE**: The log message (required)
* **MESSAGE_ID**: Optional message identifier
* **CODE_FILE**: Optional source file path
* **CODE_LINE**: Optional source line number
* **CODE_FUNC**: Optional function name

Custom fields
~~~~~~~~~~~~~

Any additional keyword arguments are treated as custom journald fields.
Field names are automatically sanitized and converted to uppercase.

.. code-block:: python

   import journald_send
   journald_send.send(
       'Custom log entry',
       CUSTOM_FIELD='value',
       ANOTHER_FIELD=123
   )

Priority enum
-------------

.. autoclass:: journald_send.Priority
   :members:
   :undoc-members:


Priority levels can be set using the ``priority`` parameter with the :class:`~journald_send.Priority` enum:

.. code-block:: python

   import journald_send
   from journald_send import Priority

   journald_send.send('Error occurred', priority=Priority.ERROR)


Logging handler
---------------

.. autoclass:: journald_send.log_handler.JournalHandler
   :members:
