import sqlite3
import mysql.connector
from mysql.connector import Error
import tailer
import re
from collections import deque, defaultdict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from db_utils import save_query
from db_utils import DB_PATH

load_dotenv()

query_history = deque(maxlen=100)
daily_query_stats = defaultdict(lambda: defaultdict(int))
processed_queries = set()
last_emitted_query = None
known_query_types = set()

EXCLUDED_QUERIES = [
    "SELECT @@hostname AS device_hostname",
    "SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE",
    "select @@version_comment limit 1",
    "SHOW INDEX",
    "SET GLOBAL general_log = 'OFF'",
    "SET GLOBAL general_log_file",
    "SET GLOBAL general_log = 'ON'",
    "SET @@session.autocommit = OFF",
    "SET @@session.autocommit = ON",
    "SET autocommit=0",
    "SELECT st.* FROM performance_schema.events_waits_history_long st",
    "SET NAMES utf8mb4",
    "SHOW GLOBAL STATUS",
    "SHOW FULL COLUMNS",
    "SELECT @@session.transaction_read_only",
    "SET character_set_results = NULL",
    "SET autocommit=1",
    "use employees"
]

EXCLUDED_PREFIXES = [
    "SET GLOBAL general_log_file",
    "SET autocommit",
    "SET @@session.autocommit",
    "SELECT st.* FROM performance_schema.events_waits_history_long",
    "SET NAMES",
    "SHOW INDEX",
    "SELECT st.*",
    "SHOW FULL COLUMNS",
    "SELECT @@session.",
    "SELECT @@character_set_",
    "SELECT @@auto_increment_increment"
]

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "192.168.10.29"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Root@12345"),
            database=os.getenv("DB_NAME", "employees")
        )
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def fetch_database_performance(database):
    performance_stats = defaultdict(int)
    try:
        db = get_db_connection()
        if not db:
            return performance_stats
        cursor = db.cursor()
        cursor.execute("SHOW GLOBAL STATUS LIKE 'Queries'")
        result = cursor.fetchone()
        performance_stats['queries'] = int(result[1]) if result else 0
        cursor.execute("SHOW GLOBAL STATUS LIKE 'Connections'")
        result = cursor.fetchone()
        performance_stats['connections'] = int(result[1]) if result else 0
        cursor.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
        result = cursor.fetchone()
        performance_stats['uptime'] = int(result[1]) if result else 0
        cursor.close()
        db.close()
    except Error as e:
        print(f"Error fetching performance data for {database}: {e}")
    return performance_stats

def fetch_database_status(database):
    status_stats = defaultdict(int)
    try:
        db = get_db_connection()
        if not db:
            return status_stats
        cursor = db.cursor()
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        result = cursor.fetchone()
        status_stats['threads_connected'] = int(result[1]) if result else 0
        cursor.execute("SHOW STATUS LIKE 'Threads_running'")
        result = cursor.fetchone()
        status_stats['threads_running'] = int(result[1]) if result else 0
        cursor.execute("SHOW STATUS LIKE 'Uptime'")
        result = cursor.fetchone()
        status_stats['uptime'] = int(result[1]) if result else 0
        cursor.close()
        db.close()
    except Error as e:
        print(f"Error fetching status data for {database}: {e}")
    return status_stats

def is_excluded_query(query):
    query_lower = query.lower().strip()
    if any(query_lower == excluded_query.lower() for excluded_query in EXCLUDED_QUERIES):
        return True
    if any(query_lower.startswith(prefix.lower()) for prefix in EXCLUDED_PREFIXES):
        return True
    return False

def extract_tool_and_query(raw_query):
    comment_pattern = re.compile(r'/\*\s*ApplicationName=([^\s]+)\s*([^\*]*)\*/\s*(.*)')
    match = comment_pattern.match(raw_query)
    if match:
        app_name = match.group(1)
        version = match.group(2).strip('- ')
        version = re.sub(r'- SQLEditor <.*>', '', version).strip()
        tool = f"{app_name} {version}" if version else app_name
        query = match.group(3).strip()
        return tool, query
    return "Unknown", raw_query.strip()

def get_query_type(query):
    query_upper = query.upper().strip()
    first_word = query_upper.split()[0] if query_upper else "UNKNOWN"
    known_query_types.add(first_word)
    return first_word

def fetch_process_list(page=1, per_page=10):
    try:
        db = get_db_connection()
        if not db:
            print("Failed to connect to database")
            return list(query_history), [], daily_query_stats

        cursor = db.cursor()

#        cursor.execute("SET GLOBAL general_log = 'OFF';")
#        cursor.execute("SET GLOBAL general_log_file = '/var/log/mysql/mysql.log';")
#        cursor.execute("SET GLOBAL general_log = 'ON';")

        cursor.execute("SELECT @@hostname AS device_hostname;")
        result = cursor.fetchone()
        hostname = result[0] if result and result[0] else "unknown"

        cursor.execute("""
            SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE
            FROM INFORMATION_SCHEMA.PROCESSLIST
            LIMIT %s OFFSET %s;
        """, (per_page, (page - 1) * per_page))
        processes = cursor.fetchall()

        log_path = "/var/log/mysql/mysql.log"
        try:
            with open(log_path, 'r') as f:
                log_entries = tailer.tail(f, 100)
        except FileNotFoundError:
            print(f"Log file {log_path} not found")
            return list(query_history), [], daily_query_stats

        query_logs = []
        log_entry_pattern = re.compile(r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}(?:Z|[+-]\d{2}:\d{2}))\s+(?P<id>\d+)\s+Query\s+(?P<query>.*)')
        non_query_pattern = re.compile(r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}(?:Z|[+-]\d{2}:\d{2}))\s+(?P<id>\d+)\s+(?P<command>Connect|Quit)\s+(?P<details>.*)')

        global last_emitted_query
        new_entries = []
        timestamps_by_pid = defaultdict(list)

        combined_query = ""
        combined_time = ""
        combined_pid = ""
        default_tz = datetime.now().astimezone().tzinfo  # Fallback timezone

        for entry in log_entries:
            if entry in processed_queries:
                continue
            if "Query" in entry:
                if combined_query:
                    combined_query = combined_query.strip()
                    if not is_excluded_query(combined_query):
                        query_logs.append((hostname, combined_pid, combined_time, combined_query))
                        new_entries.append((hostname, combined_pid, combined_time, combined_query))
                    combined_query = ""
                    combined_time = ""
                    combined_pid = ""

                match = log_entry_pattern.search(entry)
                if match:
                    time, pid, raw_query = match.groups()
                    timestamp = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f%z')
                    formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    timestamps_by_pid[pid].append(timestamp)
                    if is_excluded_query(raw_query):
                        continue
                    processed_queries.add(entry)
                    combined_query = raw_query
                    combined_time = formatted_time
                    combined_pid = pid

                    executed_tool, query = extract_tool_and_query(raw_query)
                    exec_time_ms = 0
                    if len(timestamps_by_pid[pid]) > 1:
                        exec_time_ms = (timestamps_by_pid[pid][-1] - timestamps_by_pid[pid][-2]).total_seconds() * 1000

                    query_type = get_query_type(query)

                    query_entry = {
                        "hostname": hostname,
                        "pid": pid,
                        "user": "",
                        "database": "employees",
                        "query_time": formatted_time,
                        "query": query,
                        "query_type": query_type,
                        "execution_time_ms": round(exec_time_ms, 2),
                        "executed_tool": executed_tool
                    }
                    query_history.append(query_entry)
                    save_query(query_entry)  # Save to SQLite
                    query_logs.append((hostname, pid, formatted_time, query))
                    new_entries.append((hostname, pid, formatted_time, query))

                    query_date = timestamp.strftime('%Y-%m-%d')
                    query_second = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    daily_query_stats[query_date][query_type] += 1
                    daily_query_stats[query_second][query_type] += 1

            else:
                match = non_query_pattern.search(entry)
                if not match and combined_query:
                    combined_query += " " + entry.strip()

        if combined_query:
            combined_query = combined_query.strip()
            if not is_excluded_query(combined_query):
                query_logs.append((hostname, combined_pid, combined_time, combined_query))
                new_entries.append((hostname, combined_pid, combined_time, combined_query))

        for process in processes:
            pid = str(process[0])
            for log in new_entries:
                if log[1] == pid:
                    for i, entry in enumerate(query_history):
                        if entry["pid"] == pid and entry["query_time"] == log[2] and entry["query"] == log[3]:
                            query_history[i].update({
                                "user": process[1] if process[1] else "N/A",
                                "database": process[3] if process[3] else "employees"
                            })
                            # Update SQLite with user and database
                            try:
                                with sqlite3.connect(DB_PATH) as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE queries
                                        SET user = ?, database = ?
                                        WHERE pid = ? AND query_time = ? AND query = ?
                                    """, (
                                        process[1] if process[1] else "N/A",
                                        process[3] if process[3] else "employees",
                                        pid, log[2], log[3]
                                    ))
                                    conn.commit()
                            except Exception as e:
                                print(f"Error updating query in SQLite: {e}")
                            break

        cursor.close()
        db.close()

        # Clean up per-second stats older than 5 minutes
        cutoff = (datetime.now(tz=default_tz) - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        for key in list(daily_query_stats.keys()):
            if ':' in key and key < cutoff:
                del daily_query_stats[key]

        if last_emitted_query is None:
            last_emitted_query = query_logs[-1] if query_logs else None
        else:
            new_queries = [log for log in query_logs if log > last_emitted_query]
            if new_queries:
                last_emitted_query = new_queries[-1]

        return list(query_history), query_logs, daily_query_stats

    except Error as e:
        print(f"Error during fetch or emit: {e}")
        return list(query_history), [], daily_query_stats