"""
Database transaction helpers for safe PostgreSQL operations.

Provides context managers and utilities to prevent "current transaction is aborted" errors.
"""

from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

from backend.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@contextmanager
def db_transaction(db_connection):
    """
    Context manager for safe database transactions.
    
    Automatically handles rollback on errors and ensures clean transaction state.
    
    Usage:
        with db_transaction(db) as cursor:
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchone()
        # Automatically commits on success
        
    Args:
        db_connection: psycopg2 connection object
        
    Yields:
        cursor: Database cursor for executing queries
    """
    cursor = None
    try:
        # Ensure clean transaction state before starting
        try:
            db_connection.rollback()
        except Exception:
            pass  # Ignore if transaction is already clean
        
        cursor = db_connection.cursor()
        yield cursor
        
        # Commit only if no exception occurred
        db_connection.commit()
        
    except Exception as e:
        # Rollback on any error
        try:
            db_connection.rollback()
        except Exception as rollback_error:
            logger.error(f"[DB] Error during rollback: {rollback_error}")
        raise  # Re-raise the original exception
        
    finally:
        # Always close cursor
        if cursor:
            try:
                cursor.close()
            except Exception as close_error:
                logger.error(f"[DB] Error closing cursor: {close_error}")


def execute_read_query(db_connection, query: str, params: Optional[tuple] = None) -> Optional[Any]:
    """
    Safely execute a read-only query with automatic transaction management.
    
    Args:
        db_connection: psycopg2 connection object
        query: SQL query string
        params: Optional query parameters
        
    Returns:
        Query result or None on error
    """
    try:
        with db_transaction(db_connection) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"[DB] Read query failed: {e}", exc_info=True)
        return None


def execute_write_query(db_connection, query: str, params: Optional[tuple] = None) -> bool:
    """
    Safely execute a write query (INSERT/UPDATE/DELETE) with automatic transaction management.
    
    Args:
        db_connection: psycopg2 connection object
        query: SQL query string
        params: Optional query parameters
        
    Returns:
        True on success, False on error
    """
    try:
        with db_transaction(db_connection) as cursor:
            cursor.execute(query, params or ())
            return True
    except Exception as e:
        logger.error(f"[DB] Write query failed: {e}", exc_info=True)
        return False

