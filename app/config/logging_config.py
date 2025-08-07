import logging
import logging.config
import os
import sys
from pathlib import Path


class UnicodeFilter(logging.Filter):
    """Filter to handle Unicode characters safely in log messages."""
    
    def filter(self, record):
        # Replace problematic Unicode characters with safe alternatives
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Replace common emojis with text equivalents
            replacements = {
                '🌟': '[STAR]',
                '✅': '[CHECK]',
                '🔄': '[REFRESH]',
                '⚡': '[LIGHTNING]',
                '📊': '[CHART]',
                '🚀': '[ROCKET]',
                '🔧': '[WRENCH]',
                '📋': '[CLIPBOARD]',
                '📈': '[TRENDING_UP]',
                '🖥️': '[COMPUTER]',
                '🕐': '[CLOCK]',
                '📅': '[CALENDAR]',
                '📡': '[SATELLITE]',
                '⏱️': '[STOPWATCH]',
                '🛠️': '[HAMMER_WRENCH]',
                '🎨': '[PALETTE]',
                '🟢': '[GREEN_CIRCLE]',
                '🔴': '[RED_CIRCLE]',
                '⏸️': '[PAUSE]',
                '⏰': '[ALARM]'
            }
            
            msg = record.msg
            for emoji, replacement in replacements.items():
                msg = msg.replace(emoji, replacement)
            record.msg = msg
            
        # Also handle args if they contain Unicode
        if hasattr(record, 'args') and record.args:
            safe_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    safe_arg = arg
                    for emoji, replacement in {
                        '🌟': '[STAR]',
                        '✅': '[CHECK]', 
                        '🔄': '[REFRESH]'
                    }.items():
                        safe_arg = safe_arg.replace(emoji, replacement)
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            record.args = tuple(safe_args)
            
        return True


def setup_logging():
    """Setup logging configuration for the application"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Ensure stdout uses UTF-8 encoding
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Ignore if reconfigure fails

    # Logging configuration
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'class': 'logging.Formatter'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
                'class': 'logging.Formatter'
            },
            'safe': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'class': 'logging.Formatter'
            },
        },
        'filters': {
            'unicode_filter': {
                '()': UnicodeFilter,
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': ['unicode_filter'],
            },
            'file': {
                'level': 'DEBUG',
                'formatter': 'detailed',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
                'filters': ['unicode_filter'],
            },
            'error_file': {
                'level': 'ERROR',
                'formatter': 'detailed',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
                'filters': ['unicode_filter'],
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }

    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    return logging.getLogger(name)
