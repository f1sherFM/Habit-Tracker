"""
Migration: Add new fields to habits table

Revision ID: 001
Revises: 
Create Date: 2024-01-24

Adds new fields to support enhanced habit tracking:
- execution_time: Time in seconds to complete habit (default: 60)
- frequency: Frequency in days (default: 1 - daily)
- habit_type: Type of habit (useful/pleasant, default: useful)
- reward: Reward for completing habit (nullable)
- related_habit_id: Foreign key to related habit (nullable)
"""

from sqlalchemy import text, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Migration metadata
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(engine):
    """
    Add new fields to habits table with proper defaults for existing records.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        logger.info("Starting migration 001: Adding new habit fields")
        
        with engine.connect() as connection:
            # Begin transaction
            trans = connection.begin()
            
            try:
                # Check if we're using PostgreSQL or SQLite
                is_postgresql = 'postgresql' in str(engine.url)
                
                if is_postgresql:
                    # PostgreSQL migration
                    logger.info("Applying PostgreSQL migration")
                    
                    # Create enum type for habit_type if it doesn't exist
                    connection.execute(text("""
                        DO $$ BEGIN
                            CREATE TYPE habit_type_enum AS ENUM ('useful', 'pleasant');
                        EXCEPTION
                            WHEN duplicate_object THEN null;
                        END $$;
                    """))
                    
                    # Add new columns
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS execution_time INTEGER DEFAULT 60
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS frequency INTEGER DEFAULT 1
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS habit_type habit_type_enum DEFAULT 'useful'
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS reward VARCHAR(200)
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS related_habit_id INTEGER
                    """))
                    
                    # Add foreign key constraint for related_habit_id
                    connection.execute(text("""
                        DO $$ BEGIN
                            ALTER TABLE habits 
                            ADD CONSTRAINT fk_habits_related 
                            FOREIGN KEY (related_habit_id) REFERENCES habits(id);
                        EXCEPTION
                            WHEN duplicate_object THEN null;
                        END $$;
                    """))
                    
                else:
                    # SQLite migration (more limited ALTER TABLE support)
                    logger.info("Applying SQLite migration")
                    
                    # For SQLite, we need to check if columns exist before adding them
                    # Get current table schema
                    result = connection.execute(text("PRAGMA table_info(habits)"))
                    existing_columns = {row[1] for row in result.fetchall()}
                    
                    # Add columns that don't exist
                    if 'execution_time' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN execution_time INTEGER DEFAULT 60
                        """))
                    
                    if 'frequency' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN frequency INTEGER DEFAULT 1
                        """))
                    
                    if 'habit_type' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN habit_type TEXT DEFAULT 'useful'
                        """))
                    
                    if 'reward' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN reward TEXT
                        """))
                    
                    if 'related_habit_id' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN related_habit_id INTEGER
                        """))
                
                # Update existing records with default values (for both PostgreSQL and SQLite)
                logger.info("Setting default values for existing records")
                
                # Set execution_time to 60 seconds for records where it's NULL
                connection.execute(text("""
                    UPDATE habits 
                    SET execution_time = 60 
                    WHERE execution_time IS NULL
                """))
                
                # Set frequency to 1 (daily) for records where it's NULL
                connection.execute(text("""
                    UPDATE habits 
                    SET frequency = 1 
                    WHERE frequency IS NULL
                """))
                
                # Set habit_type to 'useful' for records where it's NULL
                connection.execute(text("""
                    UPDATE habits 
                    SET habit_type = 'useful' 
                    WHERE habit_type IS NULL
                """))
                
                # Create indexes for better performance
                logger.info("Creating indexes for new fields")
                
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_habits_user_type 
                        ON habits(user_id, habit_type)
                    """))
                except SQLAlchemyError:
                    # Index might already exist, continue
                    pass
                
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_habits_frequency 
                        ON habits(frequency)
                    """))
                except SQLAlchemyError:
                    # Index might already exist, continue
                    pass
                
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_habits_related 
                        ON habits(related_habit_id)
                    """))
                except SQLAlchemyError:
                    # Index might already exist, continue
                    pass
                
                # Commit transaction
                trans.commit()
                logger.info("Migration 001 completed successfully")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Migration 001 failed: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Migration 001 error: {str(e)}")
        raise


def downgrade(engine):
    """
    Remove new fields from habits table.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        logger.info("Starting downgrade 001: Removing habit fields")
        
        with engine.connect() as connection:
            # Begin transaction
            trans = connection.begin()
            
            try:
                # Check if we're using PostgreSQL or SQLite
                is_postgresql = 'postgresql' in str(engine.url)
                
                if is_postgresql:
                    # PostgreSQL downgrade
                    logger.info("Applying PostgreSQL downgrade")
                    
                    # Drop foreign key constraint first
                    connection.execute(text("""
                        ALTER TABLE habits DROP CONSTRAINT IF EXISTS fk_habits_related
                    """))
                    
                    # Drop columns
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS related_habit_id
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS reward
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS habit_type
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS frequency
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS execution_time
                    """))
                    
                    # Drop enum type
                    connection.execute(text("""
                        DROP TYPE IF EXISTS habit_type_enum
                    """))
                    
                else:
                    # SQLite doesn't support DROP COLUMN easily
                    # We would need to recreate the table, which is complex
                    logger.warning("SQLite downgrade not fully supported - columns will remain but be unused")
                    
                    # For SQLite, we can only set columns to NULL or default values
                    # Full column removal would require table recreation
                    connection.execute(text("""
                        UPDATE habits SET 
                            execution_time = NULL,
                            frequency = NULL,
                            habit_type = NULL,
                            reward = NULL,
                            related_habit_id = NULL
                    """))
                
                # Drop indexes
                logger.info("Dropping indexes")
                
                try:
                    connection.execute(text("DROP INDEX IF EXISTS idx_habits_user_type"))
                    connection.execute(text("DROP INDEX IF EXISTS idx_habits_frequency"))
                    connection.execute(text("DROP INDEX IF EXISTS idx_habits_related"))
                except SQLAlchemyError:
                    # Indexes might not exist, continue
                    pass
                
                # Commit transaction
                trans.commit()
                logger.info("Downgrade 001 completed successfully")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Downgrade 001 failed: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Downgrade 001 error: {str(e)}")
        raise


def get_migration_info():
    """
    Get information about this migration.
    
    Returns:
        dict: Migration metadata
    """
    return {
        'revision': revision,
        'down_revision': down_revision,
        'branch_labels': branch_labels,
        'depends_on': depends_on,
        'description': 'Add new fields to habits table for enhanced tracking',
        'tables_affected': ['habits'],
        'columns_added': [
            'execution_time',
            'frequency', 
            'habit_type',
            'reward',
            'related_habit_id'
        ],
        'indexes_added': [
            'idx_habits_user_type',
            'idx_habits_frequency', 
            'idx_habits_related'
        ],
        'constraints_added': [
            'fk_habits_related'
        ]
    }