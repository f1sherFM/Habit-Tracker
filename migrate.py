#!/usr/bin/env python3
"""
Migration CLI Command
Command-line interface for running database migrations with progress tracking and logging
"""

import argparse
import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from migration_service import MigrationService
from database_config import DatabaseConfig


def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("  HabitTracker Database Migration Tool")
    print("=" * 60)
    print()


def print_progress(step: str, current: int, total: int):
    """Print progress bar for migration steps."""
    percentage = int((current / total) * 100)
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\r{step}: |{bar}| {percentage}% ({current}/{total})", end='', flush=True)
    if current == total:
        print()  # New line when complete


def validate_source_database(source_path: str) -> bool:
    """
    Validate that the source database exists and contains expected tables.
    
    Args:
        source_path: Path to source SQLite database
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(source_path):
        print(f"❌ Error: Source database not found at {source_path}")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect(source_path)
        cursor = conn.cursor()
        
        # Check for required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'habits', 'habit_logs']
        missing_tables = [table for table in required_tables if table not in tables]
        
        conn.close()
        
        if missing_tables:
            print(f"❌ Error: Missing required tables in source database: {missing_tables}")
            return False
        
        print(f"✅ Source database validated: {source_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error validating source database: {str(e)}")
        return False


def validate_target_database(target_uri: str) -> bool:
    """
    Validate that the target database is accessible.
    
    Args:
        target_uri: Target database URI
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        db_config = DatabaseConfig()
        
        # Test connection
        from sqlalchemy import create_engine, text
        engine = create_engine(target_uri, **db_config.get_connection_params())
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        print(f"✅ Target database connection validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating target database: {str(e)}")
        return False


def create_backup(source_path: str) -> str:
    """
    Create a backup of the source database.
    
    Args:
        source_path: Path to source database
        
    Returns:
        str: Path to backup file
    """
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = f"{source_path}.backup_{timestamp}"
        
        import shutil
        shutil.copy2(source_path, backup_path)
        
        print(f"✅ Backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return ""


def save_migration_log(log_entries: list, output_path: str = None):
    """
    Save migration log to file.
    
    Args:
        log_entries: List of log entries
        output_path: Optional custom output path
    """
    try:
        if not output_path:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = f"migration_log_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(log_entries, f, indent=2, default=str)
        
        print(f"✅ Migration log saved: {output_path}")
        
    except Exception as e:
        print(f"❌ Error saving migration log: {str(e)}")


def run_migration(args):
    """
    Run the database migration process.
    
    Args:
        args: Parsed command line arguments
    """
    print_banner()
    
    # Validate inputs
    if not validate_source_database(args.source):
        return False
    
    if not validate_target_database(args.target):
        return False
    
    # Create backup if requested
    backup_path = ""
    if args.backup:
        backup_path = create_backup(args.source)
        if not backup_path:
            print("❌ Backup creation failed. Aborting migration.")
            return False
    
    # Initialize migration service
    migration_service = MigrationService()
    
    print("\n🚀 Starting migration process...")
    print(f"   Source: {args.source}")
    print(f"   Target: {args.target}")
    print(f"   Verify: {'Yes' if args.verify else 'No'}")
    print()
    
    try:
        # Step 1: Migrate users
        print("📊 Step 1/3: Migrating users...")
        print_progress("Users", 0, 1)
        
        if not migration_service.migrate_users(args.source, args.target):
            print("\n❌ User migration failed!")
            return False
        
        print_progress("Users", 1, 1)
        print(" ✅ Users migrated successfully")
        
        # Step 2: Migrate habits and logs
        print("\n📊 Step 2/3: Migrating habits and logs...")
        print_progress("Habits", 0, 1)
        
        if not migration_service.migrate_habits(args.source, args.target):
            print("\n❌ Habit migration failed!")
            return False
        
        print_progress("Habits", 1, 1)
        print(" ✅ Habits and logs migrated successfully")
        
        # Step 3: Verify migration
        if args.verify:
            print("\n🔍 Step 3/3: Verifying migration...")
            print_progress("Verification", 0, 1)
            
            if not migration_service.verify_migration(args.source, args.target):
                print("\n❌ Migration verification failed!")
                return False
            
            print_progress("Verification", 1, 1)
            print(" ✅ Migration verification completed successfully")
        else:
            print("\n⏭️  Step 3/3: Skipping verification (--no-verify specified)")
        
        # Save migration log
        if args.log_file:
            save_migration_log(migration_service.get_migration_log(), args.log_file)
        elif not args.no_log:
            save_migration_log(migration_service.get_migration_log())
        
        print("\n🎉 Migration completed successfully!")
        print(f"   Backup: {backup_path if backup_path else 'Not created'}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Migration failed with error: {str(e)}")
        return False


def run_verification_only(args):
    """
    Run verification only without migration.
    
    Args:
        args: Parsed command line arguments
    """
    print_banner()
    print("🔍 Running verification only...")
    
    if not validate_source_database(args.source):
        return False
    
    if not validate_target_database(args.target):
        return False
    
    migration_service = MigrationService()
    
    try:
        if migration_service.verify_migration(args.source, args.target):
            print("✅ Verification completed successfully!")
            return True
        else:
            print("❌ Verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed with error: {str(e)}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HabitTracker Database Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic migration
  python migrate.py --source habits.db --target postgresql://user:pass@host/db
  
  # Migration with backup and custom log file
  python migrate.py --source habits.db --target $DATABASE_URL --backup --log-file migration.json
  
  # Verification only
  python migrate.py --source habits.db --target $DATABASE_URL --verify-only
  
  # Migration without verification
  python migrate.py --source habits.db --target $DATABASE_URL --no-verify
        """
    )
    
    parser.add_argument(
        '--source', '-s',
        required=True,
        help='Path to source SQLite database file'
    )
    
    parser.add_argument(
        '--target', '-t',
        help='Target PostgreSQL database URI (can use $DATABASE_URL environment variable)'
    )
    
    parser.add_argument(
        '--backup', '-b',
        action='store_true',
        help='Create backup of source database before migration'
    )
    
    parser.add_argument(
        '--verify', '--verify-migration',
        action='store_true',
        default=True,
        help='Verify migration after completion (default: True)'
    )
    
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip migration verification'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only run verification, do not migrate'
    )
    
    parser.add_argument(
        '--log-file',
        help='Custom path for migration log file'
    )
    
    parser.add_argument(
        '--no-log',
        action='store_true',
        help='Do not save migration log to file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without actually doing it'
    )
    
    args = parser.parse_args()
    
    # Handle --no-verify flag
    if args.no_verify:
        args.verify = False
    
    # Get target database URI
    if not args.target:
        args.target = os.getenv('DATABASE_URL')
        if not args.target:
            print("❌ Error: Target database URI required. Use --target or set DATABASE_URL environment variable.")
            sys.exit(1)
    
    # Handle environment variable expansion
    if args.target.startswith('$'):
        env_var = args.target[1:]
        args.target = os.getenv(env_var)
        if not args.target:
            print(f"❌ Error: Environment variable {env_var} not set.")
            sys.exit(1)
    
    # Dry run mode
    if args.dry_run:
        print_banner()
        print("🔍 DRY RUN MODE - No changes will be made")
        print(f"   Source: {args.source}")
        print(f"   Target: {args.target}")
        print(f"   Backup: {'Yes' if args.backup else 'No'}")
        print(f"   Verify: {'Yes' if args.verify else 'No'}")
        print("\nValidating databases...")
        
        if validate_source_database(args.source) and validate_target_database(args.target):
            print("✅ Dry run validation successful. Ready for migration.")
            sys.exit(0)
        else:
            print("❌ Dry run validation failed.")
            sys.exit(1)
    
    # Run verification only
    if args.verify_only:
        success = run_verification_only(args)
        sys.exit(0 if success else 1)
    
    # Run full migration
    success = run_migration(args)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()