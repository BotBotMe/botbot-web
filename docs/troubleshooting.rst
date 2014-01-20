Troubleshooting
================

Log messages
------------

**plugins.1 | DoesNotExist: Channel matching query does not exist.**

If you edit or add channels this condition can occur. It is due to a bug where
stale config data is in Redis. This bug will be resolved in a future release.

.. warning:
    You can resolve this by flushing your Redis DB. **Not recommended for production environments. You will lose all plugin data**