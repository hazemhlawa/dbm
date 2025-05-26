import mysql.connector
from mysql.connector import Error
import tailer
import re
from collections import deque, defaultdict
from datetime import datetime

# Use deque to maintain the last 100 queries
query_history = deque(maxlen=100)
daily_query_stats = defaultdict(lambda: defaultdict(int))
processed_queries = set()  # Keep track of processed queries
last_emitted_query = None  # Track the last emitted query

EXCLUDED_QUERIES = [
    "SELECT @@hostname AS device_hostname",
    "SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE",
    "SHOW INDEX",
    "SET GLOBAL general_log = 'OFF'",
    "SET GLOBAL general_log_file",
    "SET GLOBAL general_log = 'ON'",
    "SET autocommit=0",
    "SELECT st.* FROM performance_schema.events_waits_history_long st",
    "SET NAMES utf8mb4",
    "SHOW GLOBAL STATUS",
    "SHOW FULL COLUMNS",
    "SHOW"
]
EXCLUDED_PREFIXES = [
    "SET GLOBAL general_log_file",
    "SET autocommit",
    "SELECT st.* FROM performance_schema.events_waits_history_long",
    "SET NAMES",
    "SHOW INDEX",
    "SELECT st.*",
    "SHOW FULL COLUMNS",
    "SHOW"
]

def fetch_database_performance(database):
    performance_stats = defaultdict(int)

    try:
        db = mysql.connector.connect(
            host="10.77.77.20",  # Update with your Linux MySQL server IP
            user="root",
            password="Root@12345",
            database="employees"
        )
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
        db = mysql.connector.connect(
            host="10.77.77.20",
            user="root",
            password="Root@12345",
            database="employees"
        )
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
    query_lower = query.lower()
    if any(query_lower == excluded_query.lower() for excluded_query in EXCLUDED_QUERIES):
        return True
    if any(query_lower.startswith(prefix.lower()) for prefix in EXCLUDED_PREFIXES):
        return True
    return False

def fetch_process_list():
    try:
        db = mysql.connector.connect(
            host="10.77.77.20",
            user="root",
            password="Root@12345",
            database="employees"
        )
        cursor = db.cursor()

        cursor.execute("SET GLOBAL general_log = 'OFF';")
        cursor.execute("SET GLOBAL general_log_file = '/var/log/mysql/mysql.log';")
        cursor.execute("SET GLOBAL general_log = 'ON';")

        cursor.execute("SELECT @@hostname AS device_hostname;")
        hostname = cursor.fetchone()[0]

        cursor.execute("""
            SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE
            FROM INFORMATION_SCHEMA.PROCESSLIST;
        """)
        processes = cursor.fetchall()

        log_path = "/var/log/mysql/mysql.log"
        log_entries = tailer.tail(open(log_path, 'r'), 100)

        query_logs = []
        log_entry_pattern = re.compile(r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z)\s+(?P<id>\d+)\s+Query\s+(?P<query>.*)')
        non_query_pattern = re.compile(r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z)\s+(?P<id>\d+)\s+(?P<command>Connect|Quit)\s+(?P<details>.*)')

        global last_emitted_query
        new_entries = []

        combined_query = ""
        combined_time = ""
        combined_pid = ""

        for entry in log_entries:
            if entry in processed_queries:
                continue
            if "Query" in entry:
                if combined_query:
                    combined_query = combined_query.strip()
                    query_logs.append((hostname, combined_pid, combined_time, combined_query))
                    new_entries.append((hostname, combined_pid, combined_time, combined_query))
                    combined_query = ""
                    combined_time = ""
                    combined_pid = ""

                match = log_entry_pattern.search(entry)
                if match:
                    time, pid, query = match.groups()
                    formatted_time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
                    if is_excluded_query(query):
                        continue
                    processed_queries.add(entry)
                    combined_query = query
                    combined_time = formatted_time
                    combined_pid = pid

                    query_date = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
                    query_upper = query.upper()
                    if query_upper.startswith("SELECT"):
                        daily_query_stats[query_date]["SELECT"] += 1
                    elif query_upper.startswith("INSERT"):
                        daily_query_stats[query_date]["INSERT"] += 1
                    elif query_upper.startswith("UPDATE"):
                        daily_query_stats[query_date]["UPDATE"] += 1
                    elif query_upper.startswith("DELETE"):
                        daily_query_stats[query_date]["DELETE"] += 1
                    elif query_upper.startswith("CREATE"):
                        daily_query_stats[query_date]["CREATE"] += 1
                    elif query_upper.startswith("ALTER"):
                        daily_query_stats[query_date]["ALTER"] += 1
                    elif query_upper.startswith("DROP"):
                        daily_query_stats[query_date]["DROP"] += 1
            else:
                match = non_query_pattern.search(entry)
                if not match:
                    combined_query += " " + entry.strip()

        if combined_query:
            combined_query = combined_query.strip()
            query_logs.append((hostname, combined_pid, combined_time, combined_query))
            new_entries.append((hostname, combined_pid, combined_time, combined_query))

        enhanced_data = []
        for process in processes:
            pid = str(process[0])
            for log in new_entries:
                if log[1] == pid:
                    enhanced_data.append((hostname, *process, log[2], log[3]))
                    query_history.append((hostname, *process, log[2], log[3]))

        cursor.close()
        db.close()

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

