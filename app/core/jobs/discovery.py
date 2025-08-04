import os
import importlib
import inspect
from pathlib import Path
from .registry import job_registry


class JobDiscovery:
    @staticmethod
    async def discover_and_register_jobs():
        """Auto-discover jobs in the jobs directory and register them"""
        jobs_dir = Path(__file__).parent

        # Import all Python files in jobs directory
        for file_path in jobs_dir.glob("*.py"):
            if file_path.name.startswith("__") or file_path.name in ["discovery.py", "registry.py"]:
                continue

            module_name = f"app.core.jobs.{file_path.stem}"
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                print(f"Failed to import {module_name}: {e}")

        # Sync discovered jobs to database
        await job_registry.sync_to_database()
        return job_registry.get_jobs()


# Auto-discover jobs on module import
async def initialize_jobs():
    """Initialize job discovery and registration"""
    return await JobDiscovery.discover_and_register_jobs()
