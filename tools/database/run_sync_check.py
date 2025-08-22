#!/usr/bin/env python3
"""
Quick sync check after adding JobEmailConfig model.
"""

import asyncio
import subprocess
from sqlalchemy import text
from app.database.db_connector import get_db


async def check_models_vs_db():
    """Check if models match database state."""
    db = None
    try:
        db = await get_db()
        
        print("🔍 Checking models vs database state...")
        
        # Check if JobEmailConfig table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'job_email_configs'
            )
        """))
        job_email_table_exists = result.scalar()
        print(f"📊 job_email_configs table exists in DB: {job_email_table_exists}")
        
        # Check if analysis_content is nullable
        result = await db.execute(text("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'task_notes' 
            AND column_name = 'analysis_content'
        """))
        is_nullable = result.scalar()
        nullable_status = is_nullable == 'YES' if is_nullable else False
        print(f"📝 task_notes.analysis_content nullable in DB: {nullable_status}")
        
        # Check current alembic version
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        print(f"📋 Current Alembic version: {current_version}")
        
        return job_email_table_exists, nullable_status, current_version
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False, False, None
    finally:
        if db:
            await db.close()


def run_alembic_command(command):
    """Run an Alembic command."""
    try:
        print(f"🔄 Running: python -m alembic {' '.join(command)}")
        result = subprocess.run(
            ["python", "-m", "alembic"] + command,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✅ Command successful")
            if result.stdout.strip():
                print("Output:", result.stdout.strip())
        else:
            print("❌ Command failed")
            if result.stderr.strip():
                print("Error:", result.stderr.strip())
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


async def main():
    """Main function to check and sync."""
    print("🚀 Model Sync Check")
    print("=" * 50)
    
    # Check current state
    job_email_exists, analysis_nullable, alembic_version = await check_models_vs_db()
    
    print("\n📋 Current State Summary:")
    print(f"  • JobEmailConfig table: {'✅ Exists' if job_email_exists else '❌ Missing'}")
    print(f"  • analysis_content nullable: {'✅ Yes' if analysis_nullable else '❌ No'}")
    print(f"  • Alembic version: {alembic_version}")
    
    print("\n" + "=" * 50)
    
    # Check if models are in sync
    models_in_sync = job_email_exists and analysis_nullable
    
    if models_in_sync:
        print("✅ Models appear to be in sync with database!")
        print("🏷️ Stamping database to mark as current...")
        
        if run_alembic_command(["stamp", "head"]):
            print("✅ Database stamped successfully!")
        else:
            print("❌ Failed to stamp database")
    else:
        print("⚠️ Models and database are out of sync!")
        print("🔄 Generating migration to sync...")
        
        if run_alembic_command(["revision", "--autogenerate", "-m", "sync_models_with_db"]):
            print("✅ Migration generated!")
            print("📝 Review the generated migration file")
            print("🚀 Run 'python -m alembic upgrade head' to apply it")
        else:
            print("❌ Failed to generate migration")
    
    print("\n" + "=" * 50)
    print("🎉 Sync check completed!")


if __name__ == "__main__":
    asyncio.run(main())