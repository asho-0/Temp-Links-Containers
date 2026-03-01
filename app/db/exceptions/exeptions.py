class DBError(Exception):
    """Base class for all database errors raised by this module."""


class DBPoolError(DBError):
    """Raised when pool creation, closure, or acquisition fails."""


class DBConnectionError(DBError):
    """Raised when no connection is present in the current context."""


class DBTransactionError(DBError):
    """Raised when a transaction cannot be started, committed, or rolled back."""


class DBQueryError(DBError):
    """Raised when a query fails.  Wraps the original asyncpg exception."""

    def __init__(self, query: str, original: Exception) -> None:
        self.query = query
        self.original = original
        super().__init__(
            f"Query failed: {original!r}  |  query='{query[:120]}'"
        )


class DBSessionError(DBError):
    """Raised when a transaction cannot be started, committed, or rolled back."""
