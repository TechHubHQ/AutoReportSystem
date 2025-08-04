"""
Startup Script for Task Runner

Initializes and starts the task runner when the application starts.
Can be called from main.py or other initialization scripts.
"""

import asyncio
import atexit
from app.core.jobs.task_runner_manager import task_runner_manager


def initialize_task_runner():
    """Initialize the task runner on application startup"""
    try:
        print("🚀 Initializing Task Runner...")

        # Start the task runner
        success = task_runner_manager.start_runner()

        if success:
            print("✅ Task Runner initialized successfully")

            # Register cleanup function for application shutdown
            atexit.register(cleanup_task_runner)

            return True
        else:
            print("❌ Failed to initialize Task Runner")
            return False

    except Exception as e:
        print(f"❌ Error initializing Task Runner: {e}")
        return False


def cleanup_task_runner():
    """Cleanup function called on application shutdown"""
    try:
        print("🛑 Shutting down Task Runner...")
        task_runner_manager.stop_runner()
        print("✅ Task Runner shutdown complete")
    except Exception as e:
        print(f"❌ Error during task runner shutdown: {e}")


def get_initialization_status():
    """Get the current initialization status"""
    return {
        'initialized': task_runner_manager.is_running(),
        'status': task_runner_manager.get_status(),
        'health': task_runner_manager.get_health_check()
    }


# Optional: Auto-initialize on module import
# Uncomment the following line if you want the task runner to start automatically
# initialize_task_runner()
