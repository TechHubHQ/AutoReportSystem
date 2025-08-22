"""
Email Settings Configuration

This file contains email configuration settings for scheduled jobs.
You can modify these settings to customize email functionality.
"""

# Global Email Settings
GLOBAL_EMAIL_SETTINGS = {
    "default_recipient": "santhosh.bommana@medicasapp.com",
    "admin_email": "admin@medicasapp.com",
    "default_sender_name": "AutoReport System",
    "retry_attempts": 3,
    "timeout_seconds": 30,
}

# Weekly Reporter Email Configuration
WEEKLY_REPORTER_CONFIG = {
    "enabled": True,
    "recipient": "santhosh.bommana@medicasapp.com",
    "subject": "Weekly Progress Report",
    "template": "weekly_update_template.html",
    "recipient_name": "Santosh",
    "send_empty_reports": False,
    "html_format": True,
    "retry_failed_sends": True,
    "max_retries": 3,
}

# Monthly Reporter Email Configuration
MONTHLY_REPORTER_CONFIG = {
    "enabled": True,
    "recipient": "santhosh.bommana@medicasapp.com",
    "subject": "Monthly Progress Report",
    "template": "monthly_update_template.html",
    "recipient_name": "Santosh",
    "send_empty_reports": False,
    "html_format": True,
    "retry_failed_sends": True,
    "max_retries": 3,
}

# Task Lifecycle Manager Email Configuration
TASK_LIFECYCLE_CONFIG = {
    "enabled": False,  # No email functionality for task lifecycle
    "notification_on_failure": True,
    "admin_email": "admin@medicasapp.com",
}

# Notification Settings
NOTIFICATION_SETTINGS = {
    "notify_on_success": False,
    "notify_on_failure": True,
    "admin_email": "admin@medicasapp.com",
    "include_logs": True,
    "max_log_lines": 50,
}

# Email Template Settings
TEMPLATE_SETTINGS = {
    "template_directory": "app/integrations/email/templates",
    "default_encoding": "utf-8",
    "include_css": True,
    "responsive_design": True,
}

# SMTP Settings (Override defaults if needed)
SMTP_OVERRIDE_SETTINGS = {
    "use_tls": True,
    "use_ssl": False,
    "timeout": 30,
    "debug_level": 0,  # 0=no debug, 1=basic, 2=verbose
}

# Advanced Email Features
ADVANCED_FEATURES = {
    "email_tracking": False,
    "read_receipts": False,
    "priority": "normal",  # low, normal, high
    "delivery_confirmation": False,
    "auto_reply_detection": True,
}

# Rate Limiting
RATE_LIMITING = {
    "max_emails_per_hour": 100,
    "max_emails_per_day": 500,
    "delay_between_emails": 1,  # seconds
}

# Email Content Customization
CONTENT_CUSTOMIZATION = {
    "include_company_logo": True,
    "include_footer": True,
    "footer_text": "This is an automated report from AutoReport System",
    "include_unsubscribe_link": False,
    "custom_css": None,  # Path to custom CSS file
}

# Backup and Fallback Settings
BACKUP_SETTINGS = {
    "backup_recipient": "backup@medicasapp.com",
    "fallback_template": "default_template.html",
    "save_failed_emails": True,
    "failed_emails_directory": "logs/failed_emails",
}


def get_job_email_config(job_id: str) -> dict:
    """Get email configuration for a specific job"""
    config_map = {
        "weekly_reporter": WEEKLY_REPORTER_CONFIG,
        "monthly_reporter": MONTHLY_REPORTER_CONFIG,
        "task_lifecycle_manager": TASK_LIFECYCLE_CONFIG,
    }
    
    return config_map.get(job_id, {})


def update_job_email_config(job_id: str, updates: dict) -> bool:
    """Update email configuration for a specific job"""
    config_map = {
        "weekly_reporter": WEEKLY_REPORTER_CONFIG,
        "monthly_reporter": MONTHLY_REPORTER_CONFIG,
        "task_lifecycle_manager": TASK_LIFECYCLE_CONFIG,
    }
    
    if job_id in config_map:
        config_map[job_id].update(updates)
        return True
    return False


def get_all_email_configs() -> dict:
    """Get all email configurations"""
    return {
        "global_settings": GLOBAL_EMAIL_SETTINGS,
        "weekly_reporter": WEEKLY_REPORTER_CONFIG,
        "monthly_reporter": MONTHLY_REPORTER_CONFIG,
        "task_lifecycle_manager": TASK_LIFECYCLE_CONFIG,
        "notifications": NOTIFICATION_SETTINGS,
        "templates": TEMPLATE_SETTINGS,
        "smtp_override": SMTP_OVERRIDE_SETTINGS,
        "advanced_features": ADVANCED_FEATURES,
        "rate_limiting": RATE_LIMITING,
        "content_customization": CONTENT_CUSTOMIZATION,
        "backup_settings": BACKUP_SETTINGS,
    }


# Configuration validation
def validate_email_config(config: dict) -> dict:
    """Validate email configuration"""
    errors = []
    warnings = []
    
    # Check required fields
    if config.get("enabled", False):
        if not config.get("recipient"):
            errors.append("Recipient email is required when email is enabled")
        elif "@" not in config.get("recipient", ""):
            errors.append("Invalid recipient email format")
        
        if not config.get("subject"):
            warnings.append("Email subject is empty")
        
        if not config.get("template"):
            warnings.append("No email template specified")
    
    # Check retry settings
    max_retries = config.get("max_retries", 0)
    if max_retries < 0 or max_retries > 10:
        warnings.append("max_retries should be between 0 and 10")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# Quick configuration functions
def enable_weekly_reports(recipient: str = None):
    """Enable weekly reports with optional recipient override"""
    WEEKLY_REPORTER_CONFIG["enabled"] = True
    if recipient:
        WEEKLY_REPORTER_CONFIG["recipient"] = recipient


def disable_weekly_reports():
    """Disable weekly reports"""
    WEEKLY_REPORTER_CONFIG["enabled"] = False


def enable_monthly_reports(recipient: str = None):
    """Enable monthly reports with optional recipient override"""
    MONTHLY_REPORTER_CONFIG["enabled"] = True
    if recipient:
        MONTHLY_REPORTER_CONFIG["recipient"] = recipient


def disable_monthly_reports():
    """Disable monthly reports"""
    MONTHLY_REPORTER_CONFIG["enabled"] = False


def set_global_recipient(email: str):
    """Set global recipient for all reports"""
    WEEKLY_REPORTER_CONFIG["recipient"] = email
    MONTHLY_REPORTER_CONFIG["recipient"] = email
    GLOBAL_EMAIL_SETTINGS["default_recipient"] = email


def set_admin_email(email: str):
    """Set admin email for notifications"""
    NOTIFICATION_SETTINGS["admin_email"] = email
    TASK_LIFECYCLE_CONFIG["admin_email"] = email
    GLOBAL_EMAIL_SETTINGS["admin_email"] = email


# Example usage and documentation
USAGE_EXAMPLES = """
# Example usage:

# 1. Change recipient for weekly reports
WEEKLY_REPORTER_CONFIG["recipient"] = "newuser@company.com"

# 2. Disable monthly reports
MONTHLY_REPORTER_CONFIG["enabled"] = False

# 3. Enable empty report sending
WEEKLY_REPORTER_CONFIG["send_empty_reports"] = True

# 4. Change email subject
WEEKLY_REPORTER_CONFIG["subject"] = "Custom Weekly Report"

# 5. Enable retry on failure
WEEKLY_REPORTER_CONFIG["retry_failed_sends"] = True
WEEKLY_REPORTER_CONFIG["max_retries"] = 5

# 6. Use helper functions
enable_weekly_reports("manager@company.com")
disable_monthly_reports()
set_global_recipient("team@company.com")
"""