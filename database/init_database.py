#!/usr/bin/env python3
"""
Database initialization script for Tiger System
Author: Window-1
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Initialize and setup PostgreSQL database for Tiger System"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize database connection parameters"""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'database.yaml'
        self.config = self._load_config()
        self.connection = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from file or use defaults"""
        default_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'tiger_system',
            'user': 'postgres',
            'password': 'postgres',
            'app_user': 'tiger_app',
            'app_password': 'tiger_secure_password_2024'
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    default_config.update(loaded_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Could not load config file: {e}. Using defaults.")
        
        return default_config
    
    def _connect_postgres(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL server (not specific database)"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("Connected to PostgreSQL server")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _connect_database(self) -> psycopg2.extensions.connection:
        """Connect to Tiger System database"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            logger.info(f"Connected to database: {self.config['database']}")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_database(self) -> bool:
        """Create the Tiger System database if it doesn't exist"""
        conn = self._connect_postgres()
        cursor = conn.cursor()
        
        try:
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config['database'],)
            )
            
            if cursor.fetchone():
                logger.info(f"Database '{self.config['database']}' already exists")
                return True
            
            # Create database
            cursor.execute(f"CREATE DATABASE {self.config['database']}")
            logger.info(f"Created database: {self.config['database']}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to create database: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def execute_sql_file(self, sql_file_path: str) -> bool:
        """Execute SQL commands from file"""
        if not Path(sql_file_path).exists():
            logger.error(f"SQL file not found: {sql_file_path}")
            return False
        
        conn = self._connect_database()
        cursor = conn.cursor()
        
        try:
            with open(sql_file_path, 'r') as f:
                sql_content = f.read()
            
            # Execute the SQL commands
            cursor.execute(sql_content)
            conn.commit()
            logger.info(f"Successfully executed SQL file: {sql_file_path}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to execute SQL file: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def verify_tables(self) -> bool:
        """Verify that all required tables are created"""
        required_tables = [
            'market_data',
            'chain_data',
            'social_sentiment',
            'news_events',
            'trader_actions',
            'signals',
            'trades',
            'system_logs',
            'learning_data'
        ]
        
        conn = self._connect_database()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = []
            for table in required_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
                else:
                    logger.info(f"✓ Table '{table}' exists")
            
            if missing_tables:
                logger.error(f"Missing tables: {', '.join(missing_tables)}")
                return False
            
            logger.info("All required tables are present")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to verify tables: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def test_connection(self) -> bool:
        """Test database connection and basic operations"""
        try:
            conn = self._connect_database()
            cursor = conn.cursor()
            
            # Test insert
            cursor.execute("""
                INSERT INTO system_logs (window_id, log_level, component, message)
                VALUES (1, 'info', 'DatabaseInitializer', 'Database connection test')
            """)
            
            # Test select
            cursor.execute("SELECT COUNT(*) FROM system_logs WHERE window_id = 1")
            count = cursor.fetchone()[0]
            
            conn.commit()
            logger.info(f"Database connection test successful. Records in system_logs: {count}")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def initialize(self) -> bool:
        """Run complete database initialization"""
        logger.info("=" * 50)
        logger.info("Starting Tiger System Database Initialization")
        logger.info("=" * 50)
        
        # Step 1: Create database
        if not self.create_database():
            return False
        
        # Step 2: Execute schema SQL
        sql_file = Path(__file__).parent / 'create_database.sql'
        if not self.execute_sql_file(str(sql_file)):
            return False
        
        # Step 3: Verify tables
        if not self.verify_tables():
            return False
        
        # Step 4: Test connection
        if not self.test_connection():
            return False
        
        # Step 5: Save configuration
        self.save_config()
        
        logger.info("=" * 50)
        logger.info("Database initialization completed successfully!")
        logger.info("=" * 50)
        return True
    
    def save_config(self):
        """Save database configuration to file"""
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Don't save passwords in plain text in production
        safe_config = {
            'host': self.config['host'],
            'port': self.config['port'],
            'database': self.config['database'],
            'user': self.config['app_user'],
            # In production, use environment variables or secret management
            'password': '${TIGER_DB_PASSWORD}',
            'connection_string': f"postgresql://{self.config['app_user']}:PASSWORD@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(safe_config, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {self.config_path}")

def main():
    """Main execution function"""
    initializer = DatabaseInitializer()
    
    try:
        success = initializer.initialize()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()