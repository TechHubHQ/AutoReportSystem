#!/usr/bin/env python3
"""
Quick Alembic Sync Script

This script provides quick options to sync Alembic with the current database state.
"""

import subprocess
import sys


def run_alembic_command(command):
    """Run an Alembic command and return the result."""
    try:
        print(f"🔄 Running: python -m alembic {' '.join(command)}")
        result = subprocess.run(
            ["python", "-m", "alembic"] + command,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Main function with quick sync options."""
    print("🚀 Quick Alembic Sync")
    print("=" * 40)
    
    print("Available options:")
    print("1. Check current migration status")
    print("2. Generate migration from current state")
    print("3. Stamp database as current head")
    print("4. Show migration history")
    print("5. Upgrade to head")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n📋 Checking current status...")
            run_alembic_command(["current"])
            
        elif choice == "2":
            print("\n🔄 Generating migration from current state...")
            migration_name = input("Enter migration name (or press Enter for default): ").strip()
            if not migration_name:
                migration_name = "sync_with_current_state"
            
            if run_alembic_command(["revision", "--autogenerate", "-m", migration_name]):
                print("✅ Migration generated successfully!")
                print("📝 Review the generated migration file before applying.")
            else:
                print("❌ Failed to generate migration")
                
        elif choice == "3":
            print("\n🏷️ Stamping database as current head...")
            if run_alembic_command(["stamp", "head"]):
                print("✅ Database stamped successfully!")
                print("📋 Alembic now considers the database up to date.")
            else:
                print("❌ Failed to stamp database")
                
        elif choice == "4":
            print("\n📚 Migration history:")
            run_alembic_command(["history", "--verbose"])
            
        elif choice == "5":
            print("\n🚀 Upgrading to head...")
            if run_alembic_command(["upgrade", "head"]):
                print("✅ Upgrade completed successfully!")
            else:
                print("❌ Upgrade failed")
                
        else:
            print("❌ Invalid choice")
            return
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        return
    
    print("\n🎉 Operation completed!")


if __name__ == "__main__":
    main()