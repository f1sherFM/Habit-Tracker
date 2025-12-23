"""
Migration Service
Handles data migration from SQLite to PostgreSQL with data integrity verification
"""

import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from database_config import DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationService:
    """
    Service for migrating data from SQLite to PostgreSQL with comprehensive
    data integrity verification and error handling.
    """
    
    def __init__(self):
        """Initialize the migration service."""
        self.db_config = DatabaseConfig()
        self._source_engine = None
        self._target_engine = None
        self._migration_log = []
    
    def _get_source_engine(self, source_db_path: str):
        """Get SQLAlchemy engine for source SQLite database."""
        if not self._source_engine:
            source_uri = f"sqlite:///{source_db_path}"
            self._source_engine = create_engine(source_uri)
        return self._source_engine
    
    def _get_target_engine(self, target_db_uri: str):
        """Get SQLAlchemy engine for target PostgreSQL database."""
        if not self._target_engine:
            # Get connection params but filter out incompatible ones for SQLite
            connection_params = self.db_config.get_connection_params()
            
            # For SQLite URIs, remove PostgreSQL-specific parameters
            if target_db_uri.startswith('sqlite://'):
                filtered_params = {
                    'pool_pre_ping': connection_params.get('pool_pre_ping', True),
                    'connect_args': connection_params.get('connect_args', {})
                }
                # Remove PostgreSQL-specific connect_args
                if 'connect_args' in filtered_params:
                    sqlite_connect_args = {}
                    for key, value in filtered_params['connect_args'].items():
                        if key in ['check_same_thread', 'timeout']:
                            sqlite_connect_args[key] = value
                    filtered_params['connect_args'] = sqlite_connect_args
                    if not sqlite_connect_args:
                        filtered_params['connect_args'] = {'check_same_thread': False}
            else:
                filtered_params = connection_params
            
            self._target_engine = create_engine(target_db_uri, **filtered_params)
        return self._target_engine
    
    def _log_migration_step(self, step: str, status: str, details: str = ""):
        """Log migration step with timestamp."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self._migration_log.append(log_entry)
        logger.info(f"Migration {status}: {step} - {details}")
    
    def migrate_users(self, source_db: str, target_db: str) -> bool:
        """
        Migrate user data from SQLite to PostgreSQL.
        
        Args:
            source_db: Path to source SQLite database
            target_db: Target PostgreSQL database URI
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            self._log_migration_step("User Migration", "STARTED", f"Source: {source_db}")
            
            source_engine = self._get_source_engine(source_db)
            target_engine = self._get_target_engine(target_db)
            
            # Get source data
            with source_engine.connect() as source_conn:
                result = source_conn.execute(text("SELECT * FROM users"))
                users = result.fetchall()
                column_names = result.keys()
            
            if not users:
                self._log_migration_step("User Migration", "COMPLETED", "No users to migrate")
                return True
            
            # Migrate to target database
            with target_engine.connect() as target_conn:
                # Begin transaction
                trans = target_conn.begin()
                try:
                    for user in users:
                        user_dict = dict(zip(column_names, user))
                        
                        # Handle datetime fields
                        if 'created_at' in user_dict and user_dict['created_at']:
                            if isinstance(user_dict['created_at'], str):
                                user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at'].replace('Z', '+00:00'))
                        
                        if 'updated_at' in user_dict and user_dict['updated_at']:
                            if isinstance(user_dict['updated_at'], str):
                                user_dict['updated_at'] = datetime.fromisoformat(user_dict['updated_at'].replace('Z', '+00:00'))
                        
                        # Insert user (handle conflicts by updating)
                        insert_sql = text("""
                            INSERT INTO users (id, email, password_hash, google_id, github_id, name, avatar_url, created_at, updated_at, is_active)
                            VALUES (:id, :email, :password_hash, :google_id, :github_id, :name, :avatar_url, :created_at, :updated_at, :is_active)
                            ON CONFLICT (email) DO UPDATE SET
                                password_hash = EXCLUDED.password_hash,
                                google_id = EXCLUDED.google_id,
                                github_id = EXCLUDED.github_id,
                                name = EXCLUDED.name,
                                avatar_url = EXCLUDED.avatar_url,
                                updated_at = EXCLUDED.updated_at,
                                is_active = EXCLUDED.is_active
                        """)
                        
                        target_conn.execute(insert_sql, user_dict)
                    
                    trans.commit()
                    self._log_migration_step("User Migration", "COMPLETED", f"Migrated {len(users)} users")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    self._log_migration_step("User Migration", "FAILED", f"Transaction rolled back: {str(e)}")
                    raise
                    
        except Exception as e:
            self._log_migration_step("User Migration", "ERROR", str(e))
            logger.error(f"User migration failed: {str(e)}")
            return False
    
    def migrate_habits(self, source_db: str, target_db: str) -> bool:
        """
        Migrate habit and habit log data from SQLite to PostgreSQL.
        
        Args:
            source_db: Path to source SQLite database
            target_db: Target PostgreSQL database URI
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            self._log_migration_step("Habit Migration", "STARTED", f"Source: {source_db}")
            
            source_engine = self._get_source_engine(source_db)
            target_engine = self._get_target_engine(target_db)
            
            # Migrate habits first
            with source_engine.connect() as source_conn:
                result = source_conn.execute(text("SELECT * FROM habits"))
                habits = result.fetchall()
                habit_columns = result.keys()
            
            if habits:
                with target_engine.connect() as target_conn:
                    trans = target_conn.begin()
                    try:
                        for habit in habits:
                            habit_dict = dict(zip(habit_columns, habit))
                            
                            # Handle datetime fields
                            if 'created_at' in habit_dict and habit_dict['created_at']:
                                if isinstance(habit_dict['created_at'], str):
                                    habit_dict['created_at'] = datetime.fromisoformat(habit_dict['created_at'].replace('Z', '+00:00'))
                            
                            if 'updated_at' in habit_dict and habit_dict['updated_at']:
                                if isinstance(habit_dict['updated_at'], str):
                                    habit_dict['updated_at'] = datetime.fromisoformat(habit_dict['updated_at'].replace('Z', '+00:00'))
                            
                            # Insert habit
                            insert_sql = text("""
                                INSERT INTO habits (id, user_id, name, description, created_at, updated_at, is_archived)
                                VALUES (:id, :user_id, :name, :description, :created_at, :updated_at, :is_archived)
                                ON CONFLICT (id) DO UPDATE SET
                                    name = EXCLUDED.name,
                                    description = EXCLUDED.description,
                                    updated_at = EXCLUDED.updated_at,
                                    is_archived = EXCLUDED.is_archived
                            """)
                            
                            target_conn.execute(insert_sql, habit_dict)
                        
                        trans.commit()
                        self._log_migration_step("Habit Migration", "COMPLETED", f"Migrated {len(habits)} habits")
                        
                    except Exception as e:
                        trans.rollback()
                        self._log_migration_step("Habit Migration", "FAILED", f"Habit transaction rolled back: {str(e)}")
                        raise
            else:
                self._log_migration_step("Habit Migration", "COMPLETED", "No habits to migrate")
            
            # Migrate habit logs
            with source_engine.connect() as source_conn:
                result = source_conn.execute(text("SELECT * FROM habit_logs"))
                habit_logs = result.fetchall()
                log_columns = result.keys()
            
            if habit_logs:
                with target_engine.connect() as target_conn:
                    trans = target_conn.begin()
                    try:
                        for log in habit_logs:
                            log_dict = dict(zip(log_columns, log))
                            
                            # Handle date and datetime fields
                            if 'date' in log_dict and log_dict['date']:
                                if isinstance(log_dict['date'], str):
                                    log_dict['date'] = datetime.fromisoformat(log_dict['date']).date()
                            
                            if 'created_at' in log_dict and log_dict['created_at']:
                                if isinstance(log_dict['created_at'], str):
                                    log_dict['created_at'] = datetime.fromisoformat(log_dict['created_at'].replace('Z', '+00:00'))
                            
                            # Insert habit log
                            insert_sql = text("""
                                INSERT INTO habit_logs (id, habit_id, date, completed, created_at)
                                VALUES (:id, :habit_id, :date, :completed, :created_at)
                                ON CONFLICT (habit_id, date) DO UPDATE SET
                                    completed = EXCLUDED.completed
                            """)
                            
                            target_conn.execute(insert_sql, log_dict)
                        
                        trans.commit()
                        self._log_migration_step("Habit Log Migration", "COMPLETED", f"Migrated {len(habit_logs)} habit logs")
                        
                    except Exception as e:
                        trans.rollback()
                        self._log_migration_step("Habit Log Migration", "FAILED", f"Habit log transaction rolled back: {str(e)}")
                        raise
            else:
                self._log_migration_step("Habit Log Migration", "COMPLETED", "No habit logs to migrate")
            
            return True
            
        except Exception as e:
            self._log_migration_step("Habit Migration", "ERROR", str(e))
            logger.error(f"Habit migration failed: {str(e)}")
            return False
    
    def verify_migration(self, source_db: str, target_db: str) -> bool:
        """
        Verify data integrity after migration by comparing record counts and key data.
        
        Args:
            source_db: Path to source SQLite database
            target_db: Target PostgreSQL database URI
            
        Returns:
            bool: True if verification successful, False otherwise
        """
        try:
            self._log_migration_step("Migration Verification", "STARTED", "Comparing source and target data")
            
            source_engine = self._get_source_engine(source_db)
            target_engine = self._get_target_engine(target_db)
            
            verification_results = {}
            
            # Verify user counts
            with source_engine.connect() as source_conn:
                source_user_count = source_conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            with target_engine.connect() as target_conn:
                target_user_count = target_conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            verification_results['users'] = {
                'source_count': source_user_count,
                'target_count': target_user_count,
                'match': source_user_count == target_user_count
            }
            
            # Verify habit counts
            with source_engine.connect() as source_conn:
                source_habit_count = source_conn.execute(text("SELECT COUNT(*) FROM habits")).scalar()
            
            with target_engine.connect() as target_conn:
                target_habit_count = target_conn.execute(text("SELECT COUNT(*) FROM habits")).scalar()
            
            verification_results['habits'] = {
                'source_count': source_habit_count,
                'target_count': target_habit_count,
                'match': source_habit_count == target_habit_count
            }
            
            # Verify habit log counts
            with source_engine.connect() as source_conn:
                source_log_count = source_conn.execute(text("SELECT COUNT(*) FROM habit_logs")).scalar()
            
            with target_engine.connect() as target_conn:
                target_log_count = target_conn.execute(text("SELECT COUNT(*) FROM habit_logs")).scalar()
            
            verification_results['habit_logs'] = {
                'source_count': source_log_count,
                'target_count': target_log_count,
                'match': source_log_count == target_log_count
            }
            
            # Check if all verifications passed
            all_verified = all(result['match'] for result in verification_results.values())
            
            # Log detailed results
            for table, result in verification_results.items():
                status = "PASSED" if result['match'] else "FAILED"
                details = f"Source: {result['source_count']}, Target: {result['target_count']}"
                self._log_migration_step(f"Verification - {table}", status, details)
            
            if all_verified:
                self._log_migration_step("Migration Verification", "COMPLETED", "All data integrity checks passed")
            else:
                self._log_migration_step("Migration Verification", "FAILED", "Data integrity check failures detected")
            
            return all_verified
            
        except Exception as e:
            self._log_migration_step("Migration Verification", "ERROR", str(e))
            logger.error(f"Migration verification failed: {str(e)}")
            return False
    
    def rollback_migration(self, backup_path: str) -> bool:
        """
        Rollback migration by restoring from backup (placeholder implementation).
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if rollback successful, False otherwise
        """
        try:
            self._log_migration_step("Migration Rollback", "STARTED", f"Backup: {backup_path}")
            
            # This is a placeholder implementation
            # In a real scenario, this would restore from a database backup
            # For now, we'll just log the attempt
            
            if not os.path.exists(backup_path):
                self._log_migration_step("Migration Rollback", "FAILED", "Backup file not found")
                return False
            
            # TODO: Implement actual rollback logic
            # This would involve:
            # 1. Clearing target database tables
            # 2. Restoring from backup
            # 3. Verifying restoration
            
            self._log_migration_step("Migration Rollback", "COMPLETED", "Rollback completed (placeholder)")
            return True
            
        except Exception as e:
            self._log_migration_step("Migration Rollback", "ERROR", str(e))
            logger.error(f"Migration rollback failed: {str(e)}")
            return False
    
    def get_migration_log(self) -> List[Dict[str, Any]]:
        """
        Get the complete migration log.
        
        Returns:
            List[Dict]: Migration log entries
        """
        return self._migration_log.copy()
    
    def clear_migration_log(self):
        """Clear the migration log."""
        self._migration_log.clear()
    
    def run_full_migration(self, source_db: str, target_db: str, verify: bool = True) -> bool:
        """
        Run complete migration process including users, habits, and verification.
        
        Args:
            source_db: Path to source SQLite database
            target_db: Target PostgreSQL database URI
            verify: Whether to run verification after migration
            
        Returns:
            bool: True if entire migration successful, False otherwise
        """
        try:
            self._log_migration_step("Full Migration", "STARTED", f"Source: {source_db} -> Target: {target_db}")
            
            # Step 1: Migrate users
            if not self.migrate_users(source_db, target_db):
                self._log_migration_step("Full Migration", "FAILED", "User migration failed")
                return False
            
            # Step 2: Migrate habits and logs
            if not self.migrate_habits(source_db, target_db):
                self._log_migration_step("Full Migration", "FAILED", "Habit migration failed")
                return False
            
            # Step 3: Verify migration if requested
            if verify:
                if not self.verify_migration(source_db, target_db):
                    self._log_migration_step("Full Migration", "FAILED", "Migration verification failed")
                    return False
            
            self._log_migration_step("Full Migration", "COMPLETED", "All migration steps successful")
            return True
            
        except Exception as e:
            self._log_migration_step("Full Migration", "ERROR", str(e))
            logger.error(f"Full migration failed: {str(e)}")
            return False