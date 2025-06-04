import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'monitor.db')

def init_db():
    """Initialize SQLite database and create tables."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with open('schema.sql', 'r') as f:
                conn.executescript(f.read())
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")

def save_query(query_entry):
    """Save a single query entry to the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO queries (
                    hostname, pid, user, database, query_time, query,
                    query_type, execution_time_ms, executed_tool
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_entry['hostname'],
                query_entry['pid'],
                query_entry['user'],
                query_entry['database'],
                query_entry['query_time'],
                query_entry['query'],
                query_entry['query_type'],
                query_entry['execution_time_ms'],
                query_entry['executed_tool']
            ))
            conn.commit()
    except Exception as e:
        print(f"Error saving query: {e}")

def clean_old_queries(days=30):
    """Delete queries older than specified days to manage database size."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(days=days)
            cursor.execute("DELETE FROM queries WHERE created_at < ?", (cutoff,))
            conn.commit()
            print(f"Cleaned {cursor.rowcount} old queries")
    except Exception as e:
        print(f"Error cleaning old queries: {e}")

def get_query_history(limit=100):
    """Retrieve recent query history from SQLite."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hostname, pid, user, database, query_time, query,
                       query_type, execution_time_ms, executed_tool
                FROM queries
                ORDER BY query_time DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [{
                'hostname': row[0], 'pid': row[1], 'user': row[2],
                'database': row[3], 'query_time': row[4], 'query': row[5],
                'query_type': row[6], 'execution_time_ms': row[7],
                'executed_tool': row[8]
            } for row in rows]
    except Exception as e:
        print(f"Error fetching query history: {e}")
        return []
