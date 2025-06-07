CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    pid TEXT NOT NULL,
    user TEXT,
    database TEXT,
    query_time DATETIME NOT NULL,
    query TEXT NOT NULL,
    query_type TEXT NOT NULL,
    execution_time_ms REAL,
    executed_tool TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_time ON queries (query_time);
CREATE INDEX IF NOT EXISTS idx_query_type ON queries (query_type);
