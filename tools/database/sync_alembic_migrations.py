#!/usr/bin/env python3
"""
Sync Alembic Migrations with Current Database State

This script helps synchronize Alembic migration history with the actual
database schema, especially after manual fixes or partial migrations.
"""

import asyncio
import sys
import subprocess
from sqlalchemy import text, MetaData
from app.database.db_connector import get_db
from app.database.models import Base
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def check_current_alembic_version():
    """Check the current Alembic version in the database."""
    db = None
    try:
        db = await get_db()
        
        # Check if alembic_version table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("❌ alembic_version table does not exist")
            return None
        
        # Get current version
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        
        return current_version
        
    except Exception as e:
        print(f"❌ Error checking Alembic version: {e}")
        return None
    finally:
        if db:
            await db.close()


async def check_database_tables():
    """Check what tables currently exist in the database."""
    db = None
    try:
        db = await get_db()
        
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        return tables
        
    except Exception as e:
        print(f"❌ Error checking database tables: {e}")
        return []
    finally:
        if db:
            await db.close()


def get_model_tables():
    """Get table names from SQLAlchemy models."""
    model_tables = []
    for table_name, table in Base.metadata.tables.items():
        model_tables.append(table_name)
    return sorted(model_tables)


def run_alembic_command(command):
    """Run an Alembic command and return the result."""
    try:
        result = subprocess.run(
            ["python", "-m", "alembic"] + command,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


async def check_specific_schema_elements():
    """Check specific schema elements that we know should exist."""
    db = None
    try:
        db = await get_db()
        
        checks = {}
        
        # Check if analysis_content is nullable
        result = await db.execute(text("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'task_notes' 
            AND column_name = 'analysis_content'
        """))
        is_nullable = result.scalar()
        checks['task_notes.analysis_content_nullable'] = is_nullable == 'YES'
        
        # Check if job_email_configs table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'job_email_configs'
            )
        """))
        checks['job_email_configs_exists'] = result.scalar()
        
        # Check if timeline_content column exists in task_notes
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'task_notes' 
                AND column_name = 'timeline_content'
            )
        """))
        checks['task_notes.timeline_content_exists'] = result.scalar()
        
        return checks
        
    except Exception as e:
        print(f"❌ Error checking schema elements: {e}")
        return {}
    finally:
        if db:
            await db.close()


async def generate_current_migration():
    """Generate a new migration based on current model state."""
    print("🔄 Generating migration from current model state...")
    
    success, stdout, stderr = run_alembic_command([
        "revision", "--autogenerate", "-m", "sync_with_current_db_state"
    ])
    
    if success:
        print("✅ Successfully generated sync migration")
        print("📝 Migration output:")
        print(stdout)
        return True
    else:
        print("❌ Failed to generate migration")
        print("Error:", stderr)
        return False


async def stamp_database():
    """Stamp the database with the current head revision."""
    print("🏷️ Stamping database with current head...")
    
    success, stdout, stderr = run_alembic_command(["stamp", "head"])
    
    if success:
        print("✅ Successfully stamped database")
        return True
    else:
        print("❌ Failed to stamp database")
        print("Error:", stderr)
        return False


async def main():
    """Main function to sync Alembic migrations."""
    print("🚀 Alembic Migration Sync Tool")
    print("=" * 60)
    
    # Step 1: Check current state
    print("🔍 Checking current database state...")
    
    current_version = await check_current_alembic_version()
    print(f"📋 Current Alembic version: {current_version}")
    
    db_tables = await check_database_tables()
    model_tables = get_model_tables()
    
    print(f"📊 Database tables ({len(db_tables)}): {', '.join(db_tables)}")
    print(f"🏗️ Model tables ({len(model_tables)}): {', '.join(model_tables)}")
    
    # Check for missing tables
    missing_tables = set(model_tables) - set(db_tables)
    extra_tables = set(db_tables) - set(model_tables) - {'alembic_version'}
    
    if missing_tables:
        print(f"❌ Missing tables in DB: {', '.join(missing_tables)}")
    if extra_tables:
        print(f"⚠️ Extra tables in DB: {', '.join(extra_tables)}")
    
    # Step 2: Check specific schema elements
    print("\n🔍 Checking specific schema elements...")
    schema_checks = await check_specific_schema_elements()
    
    for check_name, result in schema_checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {result}")
    
    print("\n" + "=" * 60)
    
    # Step 3: Check Alembic history
    print("📚 Checking Alembic migration history...")
    success, stdout, stderr = run_alembic_command(["history", "--verbose"])
    
    if success:
        print("Migration history:")
        print(stdout)
    else:
        print("❌ Failed to get migration history")
        print("Error:", stderr)
    
    print("\n" + "=" * 60)
    
    # Step 4: Provide sync options
    print("🔧 Sync Options:")
    print("1. Generate new migration from current state")
    print("2. Stamp database with current head")
    print("3. Show current status only")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🔄 Option 1: Generating new migration...")
            if await generate_current_migration():
                print("✅ New migration generated successfully!")
                print("📝 Review the generated migration file before applying it.")
                print("🚀 Run 'python -m alembic upgrade head' to apply it.")
            
        elif choice == "2":
            print("\n🏷️ Option 2: Stamping database...")
            if await stamp_database():
                print("✅ Database stamped successfully!")
                print("📋 Alembic now considers the database up to date.")
            
        elif choice == "3":
            print("\n📊 Current status displayed above.")
            
        else:
            print("❌ Invalid choice. Exiting.")
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return
    
    print("\n" + "=" * 60)
    print("🎉 Sync operation completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)