"""
Email Configuration Manager

Provides interface for managing email configurations for scheduled jobs.
Allows runtime updates to email settings without restarting the application.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.config.logging_config import get_logger
from app.core.jobs.job_config import (
    JOB_CONFIG, EMAIL_CONFIG, 
    get_job_email_config, 
    update_job_email_config,
    get_available_email_options
)

logger = get_logger(__name__)

# Configuration file path
CONFIG_FILE_PATH = "config/email_job_config.json"


class EmailConfigManager:
    """Manager for email configuration of scheduled jobs"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE_PATH
        self._ensure_config_directory()
        self._load_saved_config()
    
    def _ensure_config_directory(self):
        """Ensure the config directory exists"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def _load_saved_config(self):
        """Load saved configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                
                # Apply saved configurations to job config
                for job_id, email_config in saved_config.get('jobs', {}).items():
                    update_job_email_config(job_id, email_config)
                
                logger.info(f"Loaded email configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading email configuration: {e}")
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                'last_updated': datetime.now().isoformat(),
                'jobs': {}
            }
            
            # Collect current email configs for all jobs
            for job in JOB_CONFIG:
                job_id = job['id']
                email_config = job.get('email_config', {})
                if email_config:
                    config_data['jobs'][job_id] = email_config
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved email configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving email configuration: {e}")
    
    def get_all_job_configs(self) -> Dict[str, Dict]:
        """Get email configuration for all jobs"""
        configs = {}
        for job in JOB_CONFIG:
            job_id = job['id']
            configs[job_id] = {
                'job_info': {
                    'id': job_id,
                    'description': f"{job_id.replace('_', ' ').title()} Job",
                    'trigger': str(job.get('trigger', 'Unknown')),
                    'enabled': job.get('email_config', {}).get('enabled', False)
                },
                'email_config': job.get('email_config', {}),
                'notification_config': job.get('notification_config', {})
            }
        return configs
    
    def get_job_config(self, job_id: str) -> Optional[Dict]:
        """Get email configuration for a specific job"""
        configs = self.get_all_job_configs()
        return configs.get(job_id)
    
    def update_job_config(self, job_id: str, email_config: Dict[str, Any]) -> bool:
        """Update email configuration for a specific job"""
        try:
            # Validate the configuration
            validation_result = self.validate_email_config(email_config)
            if not validation_result['valid']:
                logger.error(f"Invalid email configuration for job {job_id}: {validation_result['errors']}")
                return False
            
            # Update the configuration
            success = update_job_email_config(job_id, email_config)
            if success:
                self._save_config()
                logger.info(f"Updated email configuration for job {job_id}")
                return True
            else:
                logger.error(f"Failed to update email configuration for job {job_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating email configuration for job {job_id}: {e}")
            return False
    
    def validate_email_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email configuration"""
        errors = []
        warnings = []
        
        available_options = get_available_email_options()
        
        # Check for unknown keys
        for key in config.keys():
            if key not in available_options:
                warnings.append(f"Unknown configuration key: {key}")
        
        # Validate specific fields
        if 'enabled' in config:
            if not isinstance(config['enabled'], bool):
                errors.append("'enabled' must be a boolean value")
        
        if 'recipient' in config:
            if not isinstance(config['recipient'], str) or '@' not in config['recipient']:
                errors.append("'recipient' must be a valid email address")
        
        if 'subject' in config:
            if not isinstance(config['subject'], str) or len(config['subject'].strip()) == 0:
                errors.append("'subject' must be a non-empty string")
        
        if 'max_retries' in config:
            if not isinstance(config['max_retries'], int) or config['max_retries'] < 0:
                errors.append("'max_retries' must be a non-negative integer")
        
        if 'html_format' in config:
            if not isinstance(config['html_format'], bool):
                errors.append("'html_format' must be a boolean value")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def enable_job_email(self, job_id: str) -> bool:
        """Enable email functionality for a job"""
        return self.update_job_config(job_id, {'enabled': True})
    
    def disable_job_email(self, job_id: str) -> bool:
        """Disable email functionality for a job"""
        return self.update_job_config(job_id, {'enabled': False})
    
    def update_recipient(self, job_id: str, recipient: str) -> bool:
        """Update email recipient for a job"""
        return self.update_job_config(job_id, {'recipient': recipient})
    
    def update_subject(self, job_id: str, subject: str) -> bool:
        """Update email subject for a job"""
        return self.update_job_config(job_id, {'subject': subject})
    
    def reset_job_config(self, job_id: str) -> bool:
        """Reset job configuration to defaults"""
        try:
            # Find the job in JOB_CONFIG
            for job in JOB_CONFIG:
                if job['id'] == job_id:
                    # Reset to default email config based on job type
                    if job_id == 'weekly_reporter':
                        default_config = {
                            'enabled': True,
                            'recipient': EMAIL_CONFIG['default_recipient'],
                            'subject': EMAIL_CONFIG['weekly_subject'],
                            'template': EMAIL_CONFIG['template_config']['weekly_template'],
                            'recipient_name': EMAIL_CONFIG['template_config']['recipient_name'],
                            'send_empty_reports': EMAIL_CONFIG['email_settings']['send_empty_reports'],
                            'html_format': EMAIL_CONFIG['email_settings']['html_format'],
                            'retry_failed_sends': EMAIL_CONFIG['email_settings']['retry_failed_sends'],
                            'max_retries': EMAIL_CONFIG['email_settings']['max_retries'],
                        }
                    elif job_id == 'monthly_reporter':
                        default_config = {
                            'enabled': True,
                            'recipient': EMAIL_CONFIG['default_recipient'],
                            'subject': EMAIL_CONFIG['monthly_subject'],
                            'template': EMAIL_CONFIG['template_config']['monthly_template'],
                            'recipient_name': EMAIL_CONFIG['template_config']['recipient_name'],
                            'send_empty_reports': EMAIL_CONFIG['email_settings']['send_empty_reports'],
                            'html_format': EMAIL_CONFIG['email_settings']['html_format'],
                            'retry_failed_sends': EMAIL_CONFIG['email_settings']['retry_failed_sends'],
                            'max_retries': EMAIL_CONFIG['email_settings']['max_retries'],
                        }
                    else:
                        default_config = {'enabled': False}
                    
                    return self.update_job_config(job_id, default_config)
            
            logger.error(f"Job {job_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error resetting configuration for job {job_id}: {e}")
            return False
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get all available email configuration options"""
        return get_available_email_options()
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration"""
        return {
            'export_time': datetime.now().isoformat(),
            'jobs': self.get_all_job_configs(),
            'global_defaults': EMAIL_CONFIG
        }
    
    def import_config(self, config_data: Dict[str, Any]) -> bool:
        """Import configuration from data"""
        try:
            jobs_config = config_data.get('jobs', {})
            success_count = 0
            
            for job_id, job_data in jobs_config.items():
                email_config = job_data.get('email_config', {})
                if self.update_job_config(job_id, email_config):
                    success_count += 1
            
            logger.info(f"Successfully imported configuration for {success_count} jobs")
            return success_count > 0
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False


# Global instance
email_config_manager = EmailConfigManager()


# Convenience functions
def get_email_config_manager() -> EmailConfigManager:
    """Get the global email configuration manager instance"""
    return email_config_manager


def update_job_email_settings(job_id: str, **kwargs) -> bool:
    """Update email settings for a job using keyword arguments"""
    return email_config_manager.update_job_config(job_id, kwargs)


def get_job_email_settings(job_id: str) -> Optional[Dict]:
    """Get email settings for a job"""
    return email_config_manager.get_job_config(job_id)


def list_all_job_email_settings() -> Dict[str, Dict]:
    """List email settings for all jobs"""
    return email_config_manager.get_all_job_configs()