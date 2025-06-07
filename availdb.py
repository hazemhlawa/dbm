import mysql.connector
from mysql.connector import Error
from collections import defaultdict
from utils import query_history, daily_query_stats, get_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

def check_database_availability():
    databases = [
        {
            "host": os.getenv("DB_HOST", "192.168.10.29"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", "Root@12345"),
            "database": os.getenv("DB_NAME", "employees")
        }
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