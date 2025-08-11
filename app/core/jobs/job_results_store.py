"""
Global job results storage system.

This module provides a thread-safe way to store and retrieve job execution results
that works across different execution contexts (scheduler threads, Streamlit threads, etc.)
"""

import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Global storage for job results
_job_results_lock = threading.Lock()
_job_results: Dict[str, Dict[str, Any]] = {}
_job_results_history: List[Dict[str, Any]] = []

# Maximum number of results to keep in history
MAX_HISTORY_SIZE = 100


def store_job_result(job_id: str, result: Dict[str, Any]) -> None:
    """Store a job execution result globally."""
    global _job_results, _job_results_history
    
    # Add logging to debug storage
    import logging
    logger = logging.getLogger("job_results_store")
    
    with _job_results_lock:
        # Store latest result for this job
        _job_results[job_id] = result.copy()
        
        # Add to history
        history_entry = result.copy()
        history_entry['stored_at'] = datetime.now()
        _job_results_history.append(history_entry)
        
        # Keep only the most recent results
        if len(_job_results_history) > MAX_HISTORY_SIZE:
            _job_results_history = _job_results_history[-MAX_HISTORY_SIZE:]
        
        logger.info(f"Stored job result for {job_id}: status={result.get('status')}, total_stored={len(_job_results)}")
        logger.debug(f"Job result details: {result}")


def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest result for a specific job."""
    with _job_results_lock:
        return _job_results.get(job_id, None)


def get_all_job_results() -> Dict[str, Dict[str, Any]]:
    """Get all latest job results."""
    with _job_results_lock:
        return _job_results.copy()


def get_job_results_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get job results history, sorted by execution time (most recent first)."""
    with _job_results_lock:
        # Sort by execution time, most recent first
        sorted_history = sorted(
            _job_results_history,
            key=lambda x: x.get('execution_time', datetime.min),
            reverse=True
        )
        return sorted_history[:limit]


def clear_job_results() -> None:
    """Clear all job results."""
    global _job_results, _job_results_history
    
    with _job_results_lock:
        _job_results.clear()
        _job_results_history.clear()


def clear_job_result(job_id: str) -> bool:
    """Clear result for a specific job. Returns True if result was found and cleared."""
    with _job_results_lock:
        if job_id in _job_results:
            del _job_results[job_id]
            return True
        return False


def get_job_results_summary() -> Dict[str, Any]:
    """Get a summary of job results."""
    with _job_results_lock:
        total_results = len(_job_results)
        
        if not _job_results:
            return {
                'total_jobs': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'partial_success': 0,
                'last_execution': None
            }
        
        status_counts = defaultdict(int)
        latest_execution = None
        
        for result in _job_results.values():
            status = result.get('status', 'unknown')
            status_counts[status] += 1
            
            execution_time = result.get('execution_time')
            if execution_time and (latest_execution is None or execution_time > latest_execution):
                latest_execution = execution_time
        
        return {
            'total_jobs': total_results,
            'successful': status_counts.get('success', 0),
            'failed': status_counts.get('error', 0),
            'skipped': status_counts.get('skipped', 0),
            'partial_success': status_counts.get('partial_success', 0),
            'last_execution': latest_execution,
            'status_breakdown': dict(status_counts)  # For debugging
        }


def debug_storage_state() -> Dict[str, Any]:
    """Get debug information about the storage state."""
    with _job_results_lock:
        return {
            'total_results': len(_job_results),
            'total_history': len(_job_results_history),
            'job_ids': list(_job_results.keys()),
            'latest_results': {k: v.get('status') for k, v in _job_results.items()}
        }