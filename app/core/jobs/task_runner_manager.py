"""
Task Runner Manager for AutomateReportSystem

Provides management interface for the dynamic task runner.
Can be used from UI to start/stop/monitor the task runner.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from app.core.jobs.dynamic_task_runner import dynamic_task_runner


class TaskRunnerManager:
    """Manages the dynamic task runner lifecycle"""

    def __init__(self):
        self._runner_thread = None
        self._runner_loop = None
        self._is_running = False

    def start_runner(self) -> bool:
        """Start the dynamic task runner in a separate thread"""
        if self._is_running:
            print("⚠️ Task runner is already running")
            return False

        try:
            print("🚀 Starting Dynamic Task Runner Manager...")

            # Create and start the runner thread
            self._runner_thread = threading.Thread(
                target=self._run_task_runner,
                daemon=True,
                name="task_runner"
            )
            self._runner_thread.start()

            self._is_running = True
            print("✅ Dynamic Task Runner Manager started successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to start task runner: {e}")
            return False

    def stop_runner(self) -> bool:
        """Stop the dynamic task runner"""
        if not self._is_running:
            print("⚠️ Task runner is not running")
            return False

        try:
            print("🛑 Stopping Dynamic Task Runner Manager...")

            # Stop the runner
            if self._runner_loop and not self._runner_loop.is_closed():
                # Schedule the stop coroutine
                future = asyncio.run_coroutine_threadsafe(
                    dynamic_task_runner.stop(),
                    self._runner_loop
                )
                future.result(timeout=10)  # Wait up to 10 seconds

            self._is_running = False
            print("✅ Dynamic Task Runner Manager stopped successfully")
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

            # Run the dynamic task runner
            self._runner_loop.run_until_complete(dynamic_task_runner.start())

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
                    dynamic_task_runner.get_job_status(),
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
        """Restart the dynamic task runner"""
        print("🔄 Restarting Dynamic Task Runner...")

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
                dynamic_task_runner.reload_jobs(),
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
        return self._is_running and (
            self._runner_thread.is_alive() if self._runner_thread else False
        )

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
    """Start the dynamic task runner"""
    return task_runner_manager.start_runner()


def stop_task_runner() -> bool:
    """Stop the dynamic task runner"""
    return task_runner_manager.stop_runner()


def restart_task_runner() -> bool:
    """Restart the dynamic task runner"""
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


# Auto-start functionality (optional)
def auto_start_task_runner():
    """Auto-start the task runner if not already running"""
    if not task_runner_manager.is_running():
        print("🔄 Auto-starting Dynamic Task Runner...")
        return task_runner_manager.start_runner()
    return True
