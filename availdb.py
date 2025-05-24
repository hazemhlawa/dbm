import mysql.connector
from mysql.connector import Error
from collections import defaultdict
from utils import query_history, daily_query_stats

def check_database_availability():
    databases = [
        {"host": "localhost", "user": "root", "password": "rootroot", "database": "employees"}
        # Add more database configurations here
    ]

    availability_status = defaultdict(dict)

    for db in databases:
        db_host = db["host"]
        db_name = db["database"]

        try:
            connection = mysql.connector.connect(
                host=db["host"],
                user=db["user"],
                password=db["password"],
                database=db["database"]
            )
            if connection.is_connected():
                availability_status[db_host][db_name] = "Available"
                connection.close()
            else:
                availability_status[db_host][db_name] = "Unavailable"
        except Error as err:
            availability_status[db_host][db_name] = f"Unavailable: {err}"
            print(f"Error connecting to {db_host}/{db_name}: {err}")

    return availability_status

def fetch_database_availability():
    availability_status = check_database_availability()
    return query_history, availability_status, daily_query_stats

