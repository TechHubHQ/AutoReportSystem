"""
Task Runner Manager for AutomateReportSystem

Provides management interface for the task runner.
Can be used from UI to start/stop/monitor the task runner.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from app.core.jobs.task_runner import task_runner


class TaskRunnerManager:
    """Manages the task runner lifecycle"""

    def __init__(self):
        self._runner_thread = None
        self._runner_loop = None
        self._is_running = self._load_runner_status()

    def start_runner(self) -> bool:
        """Start the task runner in a separate thread"""
        if self._is_running:
            print("⚠️ Task runner is already running")
            return False

        try:
            print("🚀 Starting Task Runner Manager...")
            print(
                "📅 Task runner will now schedule jobs based on configured times from the UI")

            # Create and start the runner thread
            self._runner_thread = threading.Thread(
                target=self._run_task_runner,
                daemon=True,
                name="task_runner"
            )
            self._runner_thread.start()

            self._is_running = True
            # Store status in a persistent way
            self._save_runner_status(True)
            print("✅ Task Runner Manager started successfully")
            print(
                "ℹ️ All active jobs will be scheduled according to their configured times")
            return True

        except Exception as e:
            print(f"❌ Failed to start task runner: {e}")
            return False

    def stop_runner(self) -> bool:
        """Stop the task runner"""
        if not self._is_running:
            print("⚠️ Task runner is not running")
            return False

        try:
            print("🛑 Stopping Task Runner Manager...")

            # Stop the runner
            if self._runner_loop and not self._runner_loop.is_closed():
                # Schedule the stop coroutine
                future = asyncio.run_coroutine_threadsafe(
                    task_runner.stop(),
                    self._runner_loop
                )
                future.result(timeout=10)  # Wait up to 10 seconds

            self._is_running = False
            # Store status in a persistent way
            self._save_runner_status(False)
            print("✅ Task Runner Manager stopped successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to stop task runner: {e}")
            return False

    def _run_task_runner(self):
        """Run the task runner in its own event loop"""
        try:
            # Create new event loop for this thread
            self._runner_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._runner_loop)

            # Run the task runner
            self._runner_loop.run_until_complete(task_runner.start())

        except Exception as e:
            print(f"❌ Task runner thread error: {e}")
        finally:
            if self._runner_loop and not self._runner_loop.is_closed():
                self._runner_loop.close()
            self._is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the task runner"""
        try:
            if not self._is_running or not self._runner_loop:
                return {
                    'running': False,
                    'thread_alive': False,
                    'jobs': [],
                    'error': 'Task runner not running'
                }

            # Get status from the runner
            if self._runner_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    task_runner.get_job_status(),
                    self._runner_loop
                )
                status = future.result(timeout=5)

                status.update({
                    'thread_alive': self._runner_thread.is_alive() if self._runner_thread else False,
                    'loop_running': self._runner_loop.is_running()
                })

                return status
            else:
                return {
                    'running': False,
                    'thread_alive': self._runner_thread.is_alive() if self._runner_thread else False,
                    'loop_running': False,
                    'jobs': [],
                    'error': 'Event loop not running'
                }

        except Exception as e:
            return {
                'running': self._is_running,
                'thread_alive': self._runner_thread.is_alive() if self._runner_thread else False,
                'error': str(e),
                'jobs': []
            }

    def restart_runner(self) -> bool:
        """Restart the task runner"""
        print("🔄 Restarting Task Runner...")

        # Stop if running
        if self._is_running:
            if not self.stop_runner():
                return False

        # Wait a moment
        import time
        time.sleep(2)

        # Start again
        return self.start_runner()

    def reload_jobs(self) -> bool:
        """Reload jobs configuration"""
        if not self._is_running or not self._runner_loop:
            print("⚠️ Cannot reload jobs - task runner not running")
            return False

        try:
            print("🔄 Reloading jobs configuration...")

            future = asyncio.run_coroutine_threadsafe(
                task_runner.reload_jobs(),
                self._runner_loop
            )
            future.result(timeout=10)

            print("✅ Jobs configuration reloaded successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to reload jobs: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the task runner is currently running"""
        # Check both memory status and thread status
        memory_status = self._load_runner_status()
        thread_alive = self._runner_thread.is_alive() if self._runner_thread else False
        
        # If memory says running but thread is dead, update status
        if memory_status and not thread_alive:
            self._save_runner_status(False)
            self._is_running = False
            return False
            
        return memory_status and thread_alive

    def get_health_check(self) -> Dict[str, Any]:
        """Get health check information"""
        return {
            'manager_running': self._is_running,
            'thread_exists': self._runner_thread is not None,
            'thread_alive': self._runner_thread.is_alive() if self._runner_thread else False,
            'loop_exists': self._runner_loop is not None,
            'loop_running': self._runner_loop.is_running() if self._runner_loop else False,
            'loop_closed': self._runner_loop.is_closed() if self._runner_loop else True
        }


# Global task runner manager instance
task_runner_manager = TaskRunnerManager()


# Convenience functions for easy access
def start_task_runner() -> bool:
    """Start the task runner"""
    return task_runner_manager.start_runner()


def stop_task_runner() -> bool:
    """Stop the task runner"""
    return task_runner_manager.stop_runner()


def restart_task_runner() -> bool:
    """Restart the task runner"""
    return task_runner_manager.restart_runner()


def get_task_runner_status() -> Dict[str, Any]:
    """Get task runner status"""
    return task_runner_manager.get_status()


def reload_task_runner_jobs() -> bool:
    """Reload jobs in the task runner"""
    return task_runner_manager.reload_jobs()


def is_task_runner_running() -> bool:
    """Check if task runner is running"""
    return task_runner_manager.is_running()


def get_task_runner_health() -> Dict[str, Any]:
    """Get task runner health check"""
    return task_runner_manager.get_health_check()


    def _save_runner_status(self, is_running: bool):
        """Save runner status to a persistent file"""
        try:
            import os
            import json
            status_file = os.path.join(os.getcwd(), '.task_runner_status')
            with open(status_file, 'w') as f:
                json.dump({'is_running': is_running}, f)
        except Exception as e:
            print(f"Warning: Could not save runner status: {e}")

    def _load_runner_status(self) -> bool:
        """Load runner status from persistent file"""
        try:
            import os
            import json
            status_file = os.path.join(os.getcwd(), '.task_runner_status')
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    return data.get('is_running', False)
        except Exception as e:
            print(f"Warning: Could not load runner status: {e}")
        return False


# Auto-start functionality (disabled by default)
def auto_start_task_runner():
    """Auto-start the task runner if not already running (disabled by default)"""
    # Auto-start is disabled - task runner should only start when user clicks the button
    print("⚠️ Auto-start is disabled. Use the 'Start Runner' button in Job Management to start the task runner.")
    return False


# Add methods to TaskRunnerManager class
TaskRunnerManager._save_runner_status = lambda self, is_running: self._save_runner_status_impl(is_running)
TaskRunnerManager._load_runner_status = lambda self: self._load_runner_status_impl()

def _save_runner_status_impl(self, is_running: bool):
    """Save runner status to a persistent file"""
    try:
        import os
        import json
        status_file = os.path.join(os.getcwd(), '.task_runner_status')
        with open(status_file, 'w') as f:
            json.dump({'is_running': is_running}, f)
    except Exception as e:
        print(f"Warning: Could not save runner status: {e}")

def _load_runner_status_impl(self) -> bool:
    """Load runner status from persistent file"""
    try:
        import os
        import json
        status_file = os.path.join(os.getcwd(), '.task_runner_status')
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                data = json.load(f)
                return data.get('is_running', False)
    except Exception as e:
        print(f"Warning: Could not load runner status: {e}")
    return False

TaskRunnerManager._save_runner_status_impl = _save_runner_status_impl
TaskRunnerManager._load_runner_status_impl = _load_runner_status_impl
