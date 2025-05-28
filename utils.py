import re
import tailer
from collections import deque, defaultdict
from datetime import datetime
from typing import List, Tuple, Dict, Any
from database_manager import DatabaseManager

# Initialize database manager
db_manager = DatabaseManager()

# Global data structures
query_history = deque(maxlen=100)
daily_query_stats = defaultdict(lambda: defaultdict(int))
processed_queries = set()
last_emitted_query = None

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

def is_excluded_query(query: str) -> bool:
    """Check if a query should be excluded from monitoring"""
    query_lower = query.lower()
    return (any(query_lower == excluded_query.lower() for excluded_query in EXCLUDED_QUERIES) or
            any(query_lower.startswith(prefix.lower()) for prefix in EXCLUDED_PREFIXES))

def fetch_database_performance(db_name: str = None) -> Dict[str, Any]:
    """Fetch performance metrics for the specified database"""
    performance_stats = defaultdict(int)
    conn = db_manager.get_connection(db_name)
    
    if not conn:
        return performance_stats
    
    try:
        cursor = conn.cursor()
        
        metrics = {
            'queries': "SHOW GLOBAL STATUS LIKE 'Queries'",
            'connections': "SHOW GLOBAL STATUS LIKE 'Connections'",
            'uptime': "SHOW GLOBAL STATUS LIKE 'Uptime'",
            'threads_connected': "SHOW STATUS LIKE 'Threads_connected'",
            'threads_running': "SHOW STATUS LIKE 'Threads_running'"
        }
        
        for key, query in metrics.items():
            cursor.execute(query)
            result = cursor.fetchone()
            performance_stats[key] = int(result[1]) if result else 0
        
        cursor.close()
        return performance_stats
    
    except Exception as e:
        print(f"Error fetching performance data: {e}")
        return performance_stats
    finally:
        if conn:
            conn.close()

def parse_query_log_entry(entry: str) -> Tuple[str, str, str, str]:
    """Parse a query log entry into its components"""
    log_entry_pattern = re.compile(
        r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z)\s+'
        r'(?P<id>\d+)\s+Query\s+(?P<query>.*)'
    )
    non_query_pattern = re.compile(
        r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z)\s+'
        r'(?P<id>\d+)\s+(?P<command>Connect|Quit)\s+(?P<details>.*)'
    )
    
    if "Query" in entry:
        match = log_entry_pattern.search(entry)
        if match:
            time, pid, query = match.groups()
            return time, pid, query, "query"
    else:
        match = non_query_pattern.search(entry)
        if match:
            time, pid, command, details = match.groups()
            return time, pid, f"{command}: {details}", "connection"
    
    return None, None, None, None

def process_query_logs(log_entries: List[str], hostname: str) -> Tuple[List[Tuple], Dict[str, Dict[str, int]]]:
    """Process raw log entries into structured data"""
    global last_emitted_query, processed_queries, daily_query_stats
    
    query_logs = []
    new_entries = []
    combined_query = ""
    combined_time = ""
    combined_pid = ""

    for entry in log_entries:
        if entry in processed_queries:
            continue
            
        time, pid, query, entry_type = parse_query_log_entry(entry)
        
        if not time:
            if combined_query:
                combined_query += " " + entry.strip()
            continue
            
        if combined_query and (entry_type == "query" or not query):
            combined_query = combined_query.strip()
            if combined_query and not is_excluded_query(combined_query):
                query_logs.append((hostname, combined_pid, combined_time, combined_query))
                new_entries.append((hostname, combined_pid, combined_time, combined_query))
                update_daily_stats(combined_time, combined_query)
            combined_query = ""
            combined_time = ""
            combined_pid = ""

        if entry_type == "query" and not is_excluded_query(query):
            processed_queries.add(entry)
            combined_query = query
            combined_time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
            combined_pid = pid
            update_daily_stats(time, query)

    if combined_query:
        combined_query = combined_query.strip()
        if not is_excluded_query(combined_query):
            query_logs.append((hostname, combined_pid, combined_time, combined_query))
            new_entries.append((hostname, combined_pid, combined_time, combined_query))
            update_daily_stats(combined_time, combined_query)

    return query_logs, new_entries

def update_daily_stats(timestamp: str, query: str) -> None:
    """Update daily query statistics"""
    global daily_query_stats
    
    try:
        query_date = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
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
    except Exception:
        pass

def fetch_process_list(db_name: str = None) -> Tuple[List[Tuple], List[Tuple], Dict[str, Dict[str, int]]]:
    """Fetch and process the MySQL process list and query logs"""
    global query_history, last_emitted_query
    
    conn = db_manager.get_connection(db_name)
    if not conn:
        return list(query_history), [], daily_query_stats
    
    try:
        cursor = conn.cursor()
        
        # Configure general logging
        cursor.execute("SET GLOBAL general_log = 'OFF';")
        cursor.execute("SET GLOBAL general_log_file = '/var/log/mysql/mysql.log';")
        cursor.execute("SET GLOBAL general_log = 'ON';")
        
        # Get hostname
        cursor.execute("SELECT @@hostname AS device_hostname;")
        hostname = cursor.fetchone()[0]
        
        # Get process list
        cursor.execute("""
            SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO
            FROM INFORMATION_SCHEMA.PROCESSLIST;
        """)
        processes = cursor.fetchall()
        
        # Get query logs
        log_path = "/var/log/mysql/mysql.log"
        log_entries = tailer.tail(open(log_path, 'r'), 100)
        
        # Process logs
        query_logs, new_entries = process_query_logs(log_entries, hostname)
        
        # Enhance process data with query info
        enhanced_data = []
        for process in processes:
            pid = str(process[0])
            for log in new_entries:
                if log[1] == pid:
                    enhanced_data.append((hostname, *process, log[2], log[3]))
                    query_history.append((hostname, *process, log[2], log[3]))
        
        # Update last emitted query
        if query_logs:
            if last_emitted_query is None:
                last_emitted_query = query_logs[-1]
            else:
                new_queries = [log for log in query_logs if log > last_emitted_query]
                if new_queries:
                    last_emitted_query = new_queries[-1]
        
        return list(query_history), query_logs, daily_query_stats
    
    except Exception as e:
        print(f"Error during fetch or emit: {e}")
        return list(query_history), [], daily_query_stats
    finally:
        if conn:
            conn.close()
