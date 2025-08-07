"""
Git Auto-Commit Module for Email Templates

This module handles automatic Git commits when email templates are modified
through the UI. It provides functionality to:
- Automatically stage template files
- Create meaningful commit messages
- Push changes to the repository
"""

import os
import subprocess
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.config.logging_config import get_logger
from app.integrations.git.config import get_git_config, is_auto_commit_enabled, is_auto_push_enabled

logger = get_logger(__name__)


class GitAutoCommit:
    """Handles automatic Git commits for template changes."""
    
    def __init__(self, repo_path: str = None):
        """
        Initialize GitAutoCommit.
        
        Args:
            repo_path: Path to the Git repository. If None, uses current directory.
        """
        self.repo_path = repo_path or os.getcwd()
        self.template_dir = "app/integrations/email/templates"
        
    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Run a Git command and return the result.
        
        Args:
            command: List of command arguments
            
        Returns:
            Dict with success status, output, and error
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout.strip(),
                'error': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            logger.error("Git command timed out")
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            logger.error(f"Error running Git command: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
    
    def is_git_repository(self) -> bool:
        """Check if the current directory is a Git repository."""
        result = self._run_git_command(['git', 'rev-parse', '--git-dir'])
        return result['success']
    
    def get_git_status(self) -> Dict[str, Any]:
        """Get the current Git status."""
        if not self.is_git_repository():
            return {'success': False, 'error': 'Not a Git repository'}
        
        result = self._run_git_command(['git', 'status', '--porcelain'])
        if result['success']:
            lines = result['output'].split('\\n') if result['output'] else []
            modified_files = []
            new_files = []
            deleted_files = []
            
            for line in lines:
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    
                    if status.strip() == 'M' or status.strip() == 'MM':
                        modified_files.append(filename)
                    elif status.strip() == 'A' or status.strip() == '??':
                        new_files.append(filename)
                    elif status.strip() == 'D':
                        deleted_files.append(filename)
            
            return {
                'success': True,
                'modified_files': modified_files,
                'new_files': new_files,
                'deleted_files': deleted_files,
                'has_changes': bool(modified_files or new_files or deleted_files)
            }
        
        return result
    
    def stage_template_files(self, specific_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Stage template files for commit.
        
        Args:
            specific_files: List of specific files to stage. If None, stages all template files.
            
        Returns:
            Dict with success status and details
        """
        if not self.is_git_repository():
            return {'success': False, 'error': 'Not a Git repository'}
        
        try:
            if specific_files:
                # Stage specific files
                for file_path in specific_files:
                    result = self._run_git_command(['git', 'add', file_path])
                    if not result['success']:
                        logger.error(f"Failed to stage file {file_path}: {result['error']}")
                        return result
            else:
                # Stage all template files
                template_path = os.path.join(self.repo_path, self.template_dir)
                if os.path.exists(template_path):
                    result = self._run_git_command(['git', 'add', self.template_dir])
                    if not result['success']:
                        return result
                else:
                    return {'success': False, 'error': 'Template directory not found'}
            
            return {'success': True, 'message': 'Files staged successfully'}
            
        except Exception as e:
            logger.error(f"Error staging files: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_commit_message(self, action: str, template_name: str, details: Optional[str] = None) -> str:
        """
        Create a standardized commit message for template changes.
        
        Args:
            action: Type of action (create, update, delete)
            template_name: Name of the template
            details: Additional details about the change
            
        Returns:
            Formatted commit message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Base commit message
        if action.lower() == 'create':
            message = f"feat(templates): Add new email template '{template_name}'"
        elif action.lower() == 'update':
            message = f"chore(templates): Update email template '{template_name}'"
        elif action.lower() == 'delete':
            message = f"chore(templates): Remove email template '{template_name}'"
        else:
            message = f"chore(templates): Modify email template '{template_name}'"
        
        # Add details if provided
        if details:
            message += f"\\n\\n{details}"
        
        # Add metadata
        message += f"\\n\\nAuto-committed via Template Designer UI\\nTimestamp: {timestamp}"
        
        return message
    
    def commit_changes(self, message: str) -> Dict[str, Any]:
        """
        Commit staged changes with the provided message.
        
        Args:
            message: Commit message
            
        Returns:
            Dict with success status and commit details
        """
        if not self.is_git_repository():
            return {'success': False, 'error': 'Not a Git repository'}
        
        result = self._run_git_command(['git', 'commit', '-m', message])
        
        if result['success']:
            # Get commit hash
            hash_result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
            commit_hash = hash_result['output'][:8] if hash_result['success'] else 'unknown'
            
            return {
                'success': True,
                'commit_hash': commit_hash,
                'message': 'Changes committed successfully',
                'output': result['output']
            }
        
        return result
    
    def push_changes(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        """
        Push committed changes to remote repository.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            
        Returns:
            Dict with success status and push details
        """
        if not self.is_git_repository():
            return {'success': False, 'error': 'Not a Git repository'}
        
        # Get current branch if not specified
        if not branch:
            branch_result = self._run_git_command(['git', 'branch', '--show-current'])
            if branch_result['success']:
                branch = branch_result['output']
            else:
                return {'success': False, 'error': 'Could not determine current branch'}
        
        # Push changes
        result = self._run_git_command(['git', 'push', remote, branch])
        
        if result['success']:
            return {
                'success': True,
                'message': f'Changes pushed to {remote}/{branch}',
                'output': result['output']
            }
        
        return result
    
    async def auto_commit_template_change(
        self,
        action: str,
        template_name: str,
        file_paths: Optional[List[str]] = None,
        details: Optional[str] = None,
        push_to_remote: bool = False
    ) -> Dict[str, Any]:
        """
        Automatically commit template changes.
        
        Args:
            action: Type of action (create, update, delete)
            template_name: Name of the template
            file_paths: Specific file paths to commit
            details: Additional details about the change
            push_to_remote: Whether to push changes to remote repository
            
        Returns:
            Dict with operation results
        """
        try:
            # Check if auto-commit is enabled
            if not is_auto_commit_enabled():
                logger.debug("Git auto-commit is disabled - skipping")
                return {'success': True, 'message': 'Auto-commit disabled'}
            
            logger.info(f"Starting auto-commit for template '{template_name}' (action: {action})")
            
            # Check if Git repository
            if not self.is_git_repository():
                logger.warning("Not a Git repository - skipping auto-commit")
                return {'success': False, 'error': 'Not a Git repository'}
            
            # Check for changes
            status = self.get_git_status()
            if not status['success']:
                return status
            
            if not status['has_changes']:
                logger.info("No changes detected - skipping commit")
                return {'success': True, 'message': 'No changes to commit'}
            
            # Stage files
            stage_result = self.stage_template_files(file_paths)
            if not stage_result['success']:
                logger.error(f"Failed to stage files: {stage_result['error']}")
                return stage_result
            
            # Create commit message
            commit_message = self.create_commit_message(action, template_name, details)
            
            # Commit changes
            commit_result = self.commit_changes(commit_message)
            if not commit_result['success']:
                logger.error(f"Failed to commit changes: {commit_result['error']}")
                return commit_result
            
            logger.info(f"Successfully committed changes: {commit_result['commit_hash']}")
            
            result = {
                'success': True,
                'commit_hash': commit_result['commit_hash'],
                'message': 'Template changes committed successfully',
                'commit_message': commit_message
            }
            
            # Push to remote if requested or auto-push is enabled
            should_push = push_to_remote or is_auto_push_enabled()
            if should_push:
                push_result = self.push_changes()
                if push_result['success']:
                    result['pushed'] = True
                    result['push_message'] = push_result['message']
                    logger.info("Changes pushed to remote repository")
                else:
                    result['pushed'] = False
                    result['push_error'] = push_result['error']
                    logger.warning(f"Failed to push changes: {push_result['error']}")
            else:
                result['pushed'] = False
                result['push_message'] = "Auto-push disabled"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto-commit process: {e}")
            return {'success': False, 'error': str(e)}


# Global instance for easy access
git_auto_commit = GitAutoCommit()


async def auto_commit_template_change(
    action: str,
    template_name: str,
    file_paths: Optional[List[str]] = None,
    details: Optional[str] = None,
    push_to_remote: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for auto-committing template changes.
    
    Args:
        action: Type of action (create, update, delete)
        template_name: Name of the template
        file_paths: Specific file paths to commit
        details: Additional details about the change
        push_to_remote: Whether to push changes to remote repository
        
    Returns:
        Dict with operation results
    """
    return await git_auto_commit.auto_commit_template_change(
        action, template_name, file_paths, details, push_to_remote
    )