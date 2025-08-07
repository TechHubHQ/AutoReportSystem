"""
Git Auto-Commit Configuration

This module contains configuration settings for the Git auto-commit functionality.
"""

import os
from typing import Dict, Any

# Git Auto-Commit Configuration
GIT_AUTO_COMMIT_CONFIG = {
    # Enable/disable auto-commit functionality
    "enabled": True,
    
    # Auto-push to remote repository after commit
    "auto_push": False,
    
    # Remote repository name (usually 'origin')
    "remote_name": "origin",
    
    # Branch to push to (None = current branch)
    "branch_name": None,
    
    # Commit message templates
    "commit_templates": {
        "create": "feat(templates): Add new email template '{template_name}'",
        "update": "chore(templates): Update email template '{template_name}'", 
        "delete": "chore(templates): Remove email template '{template_name}'",
        "sync": "chore(templates): Sync email templates from files"
    },
    
    # Files and directories to include in commits
    "include_patterns": [
        "app/integrations/email/templates/*.html",
        "app/integrations/email/templates/**/*.html"
    ],
    
    # Files and directories to exclude from commits
    "exclude_patterns": [
        "*.tmp",
        "*.bak",
        "*~",
        ".DS_Store"
    ],
    
    # Git command timeout (seconds)
    "command_timeout": 30,
    
    # Whether to include detailed change information in commit messages
    "include_change_details": True,
    
    # Whether to include timestamp in commit messages
    "include_timestamp": True,
    
    # Maximum length for commit message summary line
    "max_summary_length": 72,
    
    # Whether to validate Git repository before attempting operations
    "validate_repository": True,
    
    # Whether to check for uncommitted changes before new operations
    "check_working_directory": True
}


def get_git_config() -> Dict[str, Any]:
    """
    Get Git auto-commit configuration.
    
    Configuration can be overridden by environment variables:
    - GIT_AUTO_COMMIT_ENABLED: Enable/disable auto-commit
    - GIT_AUTO_PUSH: Enable/disable auto-push
    - GIT_REMOTE_NAME: Remote repository name
    - GIT_BRANCH_NAME: Branch name to push to
    
    Returns:
        Dict containing Git configuration
    """
    config = GIT_AUTO_COMMIT_CONFIG.copy()
    
    # Override with environment variables if present
    if "GIT_AUTO_COMMIT_ENABLED" in os.environ:
        config["enabled"] = os.environ["GIT_AUTO_COMMIT_ENABLED"].lower() in ("true", "1", "yes", "on")
    
    if "GIT_AUTO_PUSH" in os.environ:
        config["auto_push"] = os.environ["GIT_AUTO_PUSH"].lower() in ("true", "1", "yes", "on")
    
    if "GIT_REMOTE_NAME" in os.environ:
        config["remote_name"] = os.environ["GIT_REMOTE_NAME"]
    
    if "GIT_BRANCH_NAME" in os.environ:
        config["branch_name"] = os.environ["GIT_BRANCH_NAME"]
    
    return config


def is_auto_commit_enabled() -> bool:
    """Check if auto-commit is enabled."""
    return get_git_config()["enabled"]


def is_auto_push_enabled() -> bool:
    """Check if auto-push is enabled."""
    return get_git_config()["auto_push"]


def get_commit_template(action: str) -> str:
    """
    Get commit message template for a specific action.
    
    Args:
        action: Action type (create, update, delete, sync)
        
    Returns:
        Commit message template
    """
    config = get_git_config()
    return config["commit_templates"].get(action, "chore(templates): Template change")


def get_remote_config() -> Dict[str, str]:
    """
    Get remote repository configuration.
    
    Returns:
        Dict with remote_name and branch_name
    """
    config = get_git_config()
    return {
        "remote_name": config["remote_name"],
        "branch_name": config["branch_name"]
    }