#!/usr/bin/env python3
"""
Migration Runner
Executes database migrations for the Habit Tracker application
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database_config import DatabaseConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """
    Handles execution of database migrations with tracking and rollback support.
    """
    
    def __init__(self):
        """Initialize the migration runner."""
        self.db_config = DatabaseConfig()
        self.engine = None
        self.migrations_table = 'schema_migrations'
    
    def _get_engine(self):
        """Get SQLAlchemy engine for database operations."""
        if not self.engine:
            database_uri = self.db_config.get_database_uri()
            connection_params = self.db_config.get_connection_params()
            
            # Filter out PostgreSQL-specific parameters for SQLite
            if database_uri.startswith('sqlite://'):
                filtered_params = {
                    'pool_pre_ping': connection_params.get('pool_pre_ping', True),
                    'connect_args': connection_params.get('connect_args', {})
                }
            else:
                filtered_params = connection_params
            
            self.engine = create_engine(database_uri, **filtered_params)
        return self.engine
    
    def _ensure_migrations_table(self):
        """
        Ensure the migrations tracking table exists.
        """
        try:
            engine = self._get_engine()
            
            with engine.connect() as connection:
                # Check if migrations table exists
                is_postgresql = 'postgresql' in str(engine.url)
                
                if is_postgresql:
                    # PostgreSQL check
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = :table_name
                        )
                    """), {'table_name': self.migrations_table})
                    
                    table_exists = result.scalar()
                else:
                    # SQLite check
                    result = connection.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name = :table_name
                    """), {'table_name': self.migrations_table})
                    
                    table_exists = result.fetchone() is not None
                
                if not table_exists:
                    logger.info(f"Creating migrations table: {self.migrations_table}")
                    
                    # Begin transaction
                    trans = connection.begin()
                    
                    try:
                        # Create migrations table
                        connection.execute(text(f"""
                            CREATE TABLE {self.migrations_table} (
                                id SERIAL PRIMARY KEY,
                                revision VARCHAR(50) NOT NULL UNIQUE,
                                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                description TEXT
                            )
                        """ if is_postgresql else f"""
                            CREATE TABLE {self.migrations_table} (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                revision VARCHAR(50) NOT NULL UNIQUE,
                                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                description TEXT
                            )
                        """))
                        
                        trans.commit()
                        logger.info("Migrations table created successfully")
                        
                    except Exception as e:
                        trans.rollback()
                        raise
                
        except Exception as e:
            logger.error(f"Error ensuring migrations table: {str(e)}")
            raise
    
    def _get_applied_migrations(self):
        """
        Get list of applied migrations.
        
        Returns:
            set: Set of applied migration revisions
        """
        try:
            engine = self._get_engine()
            
            with engine.connect() as connection:
                result = connection.execute(text(f"""
                    SELECT revision FROM {self.migrations_table} ORDER BY applied_at
                """))
                
                return {row[0] for row in result.fetchall()}
                
        except Exception as e:
            logger.error(f"Error getting applied migrations: {str(e)}")
            return set()
    
    def _record_migration(self, revision, description=""):
        """
        Record a migration as applied.
        
        Args:
            revision: Migration revision ID
            description: Optional description
        """
        try:
            engine = self._get_engine()
            
            with engine.connect() as connection:
                trans = connection.begin()
                
                try:
                    connection.execute(text(f"""
                        INSERT INTO {self.migrations_table} (revision, description, applied_at)
                        VALUES (:revision, :description, :applied_at)
                    """), {
                        'revision': revision,
                        'description': description,
                        'applied_at': datetime.now(timezone.utc)
                    })
                    
                    trans.commit()
                    logger.info(f"Recorded migration: {revision}")
                    
                except Exception as e:
                    trans.rollback()
                    raise
                
        except Exception as e:
            logger.error(f"Error recording migration {revision}: {str(e)}")
            raise
    
    def _remove_migration_record(self, revision):
        """
        Remove a migration record (for rollback).
        
        Args:
            revision: Migration revision ID
        """
        try:
            engine = self._get_engine()
            
            with engine.connect() as connection:
                trans = connection.begin()
                
                try:
                    connection.execute(text(f"""
                        DELETE FROM {self.migrations_table} WHERE revision = :revision
                    """), {'revision': revision})
                    
                    trans.commit()
                    logger.info(f"Removed migration record: {revision}")
                    
                except Exception as e:
                    trans.rollback()
                    raise
                
        except Exception as e:
            logger.error(f"Error removing migration record {revision}: {str(e)}")
            raise
    
    def _load_migration_module(self, migration_file):
        """
        Dynamically load a migration module.
        
        Args:
            migration_file: Path to migration file
            
        Returns:
            module: Loaded migration module
        """
        try:
            import importlib.util
            
            spec = importlib.util.spec_from_file_location("migration", migration_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            logger.error(f"Error loading migration {migration_file}: {str(e)}")
            raise
    
    def run_migrations(self, target_revision=None):
        """
        Run pending migrations up to target revision.
        
        Args:
            target_revision: Optional target revision (runs all if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting migration process")
            
            # Ensure migrations table exists
            self._ensure_migrations_table()
            
            # Get applied migrations
            applied_migrations = self._get_applied_migrations()
            logger.info(f"Applied migrations: {applied_migrations}")
            
            # Find migration files
            migrations_dir = project_root / "migrations" / "versions"
            migration_files = sorted([
                f for f in migrations_dir.glob("*.py") 
                if f.name != "__init__.py"
            ])
            
            if not migration_files:
                logger.info("No migration files found")
                return True
            
            # Process each migration
            migrations_applied = 0
            
            for migration_file in migration_files:
                try:
                    # Load migration module
                    migration_module = self._load_migration_module(migration_file)
                    
                    # Get revision from module
                    revision = getattr(migration_module, 'revision', None)
                    if not revision:
                        logger.warning(f"Migration {migration_file.name} has no revision, skipping")
                        continue
                    
                    # Check if already applied
                    if revision in applied_migrations:
                        logger.info(f"Migration {revision} already applied, skipping")
                        continue
                    
                    # Check target revision
                    if target_revision and revision != target_revision:
                        # If we haven't reached target yet, continue
                        # If we've passed target, stop
                        if revision > target_revision:
                            break
                        continue
                    
                    # Run migration
                    logger.info(f"Applying migration {revision}: {migration_file.name}")
                    
                    engine = self._get_engine()
                    
                    # Get migration info if available
                    description = ""
                    if hasattr(migration_module, 'get_migration_info'):
                        info = migration_module.get_migration_info()
                        description = info.get('description', '')
                    
                    # Execute upgrade
                    migration_module.upgrade(engine)
                    
                    # Record migration
                    self._record_migration(revision, description)
                    
                    migrations_applied += 1
                    logger.info(f"Migration {revision} applied successfully")
                    
                    # If this was the target revision, stop
                    if target_revision and revision == target_revision:
                        break
                        
                except Exception as e:
                    logger.error(f"Failed to apply migration {migration_file.name}: {str(e)}")
                    raise
            
            if migrations_applied > 0:
                logger.info(f"Applied {migrations_applied} migrations successfully")
            else:
                logger.info("No new migrations to apply")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration process failed: {str(e)}")
            return False
    
    def rollback_migration(self, target_revision):
        """
        Rollback migrations to target revision.
        
        Args:
            target_revision: Target revision to rollback to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Starting rollback to revision {target_revision}")
            
            # Ensure migrations table exists
            self._ensure_migrations_table()
            
            # Get applied migrations in reverse order
            engine = self._get_engine()
            
            with engine.connect() as connection:
                result = connection.execute(text(f"""
                    SELECT revision FROM {self.migrations_table} 
                    ORDER BY applied_at DESC
                """))
                
                applied_migrations = [row[0] for row in result.fetchall()]
            
            # Find migrations to rollback
            migrations_to_rollback = []
            for revision in applied_migrations:
                if revision == target_revision:
                    break
                migrations_to_rollback.append(revision)
            
            if not migrations_to_rollback:
                logger.info("No migrations to rollback")
                return True
            
            # Find migration files
            migrations_dir = project_root / "migrations" / "versions"
            
            # Rollback each migration
            rollbacks_applied = 0
            
            for revision in migrations_to_rollback:
                try:
                    # Find migration file
                    migration_file = None
                    for f in migrations_dir.glob("*.py"):
                        if f.name != "__init__.py":
                            module = self._load_migration_module(f)
                            if getattr(module, 'revision', None) == revision:
                                migration_file = f
                                break
                    
                    if not migration_file:
                        logger.error(f"Migration file for revision {revision} not found")
                        continue
                    
                    # Load and execute downgrade
                    logger.info(f"Rolling back migration {revision}")
                    
                    migration_module = self._load_migration_module(migration_file)
                    migration_module.downgrade(engine)
                    
                    # Remove migration record
                    self._remove_migration_record(revision)
                    
                    rollbacks_applied += 1
                    logger.info(f"Migration {revision} rolled back successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to rollback migration {revision}: {str(e)}")
                    raise
            
            logger.info(f"Rolled back {rollbacks_applied} migrations successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback process failed: {str(e)}")
            return False
    
    def show_migration_status(self):
        """
        Show current migration status.
        """
        try:
            logger.info("Migration Status")
            logger.info("=" * 50)
            
            # Ensure migrations table exists
            self._ensure_migrations_table()
            
            # Get applied migrations
            applied_migrations = self._get_applied_migrations()
            
            # Find all migration files
            migrations_dir = project_root / "migrations" / "versions"
            migration_files = sorted([
                f for f in migrations_dir.glob("*.py") 
                if f.name != "__init__.py"
            ])
            
            if not migration_files:
                logger.info("No migration files found")
                return
            
            # Show status for each migration
            for migration_file in migration_files:
                try:
                    migration_module = self._load_migration_module(migration_file)
                    revision = getattr(migration_module, 'revision', 'Unknown')
                    
                    status = "APPLIED" if revision in applied_migrations else "PENDING"
                    
                    # Get description if available
                    description = ""
                    if hasattr(migration_module, 'get_migration_info'):
                        info = migration_module.get_migration_info()
                        description = info.get('description', '')
                    
                    logger.info(f"{revision:10} {status:10} {description}")
                    
                except Exception as e:
                    logger.error(f"Error reading migration {migration_file.name}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error showing migration status: {str(e)}")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Runner")
    parser.add_argument('command', choices=['migrate', 'rollback', 'status'], 
                       help='Migration command to execute')
    parser.add_argument('--target', help='Target revision for migrate/rollback')
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    
    try:
        if args.command == 'migrate':
            success = runner.run_migrations(args.target)
            sys.exit(0 if success else 1)
        elif args.command == 'rollback':
            if not args.target:
                print("Error: --target required for rollback")
                sys.exit(1)
            success = runner.rollback_migration(args.target)
            sys.exit(0 if success else 1)
        elif args.command == 'status':
            runner.show_migration_status()
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration runner error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()