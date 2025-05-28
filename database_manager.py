import mysql.connector
from mysql.connector import Error
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading

@dataclass
class DatabaseConfig:
    name: str
    host: str
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""
    active: bool = False

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    CONFIG_FILE = "/app/config/databases.json"  # Inside Docker container
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._databases: Dict[str, DatabaseConfig] = {}
                    cls._instance._current_db: Optional[str] = None
                    cls._instance.load_databases()
        return cls._instance
    
    def load_databases(self) -> None:
        """Load database configurations from JSON file"""
        try:
            config_path = Path(self.CONFIG_FILE)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self._databases = {name: DatabaseConfig(**config) for name, config in data['databases'].items()}
                    self._current_db = data.get('current_db')
        except Exception as e:
            print(f"Error loading databases: {e}")
    
    def save_databases(self) -> None:
        """Save database configurations to JSON file"""
        try:
            config_path = Path(self.CONFIG_FILE)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({
                    'databases': {name: asdict(config) for name, config in self._databases.items()},
                    'current_db': self._current_db
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving databases: {e}")
    
    def add_database(self, config: DatabaseConfig) -> bool:
        """Add a new database configuration"""
        with self._lock:
            if config.name in self._databases:
                return False
            
            # Test connection first
            if not self.test_connection(config):
                return False
            
            self._databases[config.name] = config
            if self._current_db is None:
                self._current_db = config.name
                config.active = True
            self.save_databases()
            return True
    
    def remove_database(self, name: str) -> bool:
        """Remove a database configuration"""
        with self._lock:
            if name in self._databases:
                if self._current_db == name:
                    self._current_db = next(iter(self._databases.keys()), None)
                    if self._current_db:
                        self._databases[self._current_db].active = True
                del self._databases[name]
                self.save_databases()
                return True
            return False
    
    def set_current_db(self, name: str) -> bool:
        """Set the currently active database"""
        with self._lock:
            if name in self._databases:
                if self._current_db:
                    self._databases[self._current_db].active = False
                self._current_db = name
                self._databases[name].active = True
                self.save_databases()
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
    
    def test_connection(self, config: DatabaseConfig) -> bool:
        """Test if a database connection can be established"""
        try:
            conn = mysql.connector.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database
            )
            conn.close()
            return True
        except Error as e:
            print(f"Connection test failed for {config.name}: {e}")
            return False
    
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
                database=config.database
            )
        except Error as e:
            print(f"Error connecting to {config.name}: {e}")
            return None