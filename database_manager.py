import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import threading

@dataclass
class DatabaseConfig:
    name: str
    host: str
    port: int = 3306
    user: str = "root"
    password: str = ""
    databases: List[str] = None
    active: bool = True

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._databases: Dict[str, DatabaseConfig] = {}
                    cls._instance._current_db: Optional[str] = None
        return cls._instance
    
    def add_database(self, config: DatabaseConfig) -> None:
        """Add a new database configuration"""
        with self._lock:
            self._databases[config.name] = config
            if self._current_db is None:
                self._current_db = config.name
    
    def remove_database(self, name: str) -> None:
        """Remove a database configuration"""
        with self._lock:
            if name in self._databases:
                del self._databases[name]
                if self._current_db == name:
                    self._current_db = next(iter(self._databases.keys()), None) if self._databases else None
    
    def set_current_db(self, name: str) -> bool:
        """Set the currently active database"""
        with self._lock:
            if name in self._databases:
                self._current_db = name
                return True
            return False
    
    def get_current_db(self) -> Optional[DatabaseConfig]:
        """Get the current database configuration"""
        with self._lock:
            return self._databases.get(self._current_db) if self._current_db else None
    
    def get_all_databases(self) -> List[DatabaseConfig]:
        """Get all database configurations"""
        with self._lock:
            return list(self._databases.values())
    
    def get_connection(self, db_name: str = None) -> Optional[mysql.connector.MySQLConnection]:
        """Get a connection to the specified or current database"""
        config = self.get_current_db() if db_name is None else self._databases.get(db_name)
        if not config:
            return None
        
        try:
            return mysql.connector.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.databases[0] if config.databases else None
            )
        except Error as e:
            print(f"Error connecting to {config.name}: {e}")
            return None
