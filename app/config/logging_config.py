import logging
import logging.config
import os
import sys
from pathlib import Path


class EnhancedConsoleHandler(logging.StreamHandler):
    """Enhanced console handler that ensures logs appear in console."""

    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)

    def emit(self, record):
        try:
            msg = self.format(record)
            # Force flush to ensure immediate console output
            self.stream.write(msg + '\n')
            self.stream.flush()
        except Exception:
            self.handleError(record)


class UnicodeFilter(logging.Filter):
    """Filter to handle Unicode characters safely in console log messages."""

    def filter(self, record):
        # For console output, keep emojis but ensure they're safe
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Only replace if they cause issues - most emojis are fine for console
            replacements = {
                # Add specific problematic characters here if needed
            }

            msg = record.msg
            for emoji, replacement in replacements.items():
                msg = msg.replace(emoji, replacement)
            record.msg = msg

        return True


class FileUnicodeFilter(logging.Filter):
    """Filter to handle Unicode characters safely in file log messages."""

    def filter(self, record):
        # For file output, replace emojis with text equivalents for better compatibility
        if hasattr(record, 'msg') and isinstance(record.msg, str):
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
                '⏰': '[ALARM]',
                '🎉': '[PARTY]',
                '🧵': '[THREAD]',
                '🐍': '[PYTHON]',
                '💓': '[HEARTBEAT]',
                '🏃': '[RUNNING]',
                '🛑': '[STOP]',
                '❌': '[X]',
                '⚠️': '[WARNING]'
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
                        '🔄': '[REFRESH]',
                        '🚀': '[ROCKET]',
                        '❌': '[X]',
                        '⚠️': '[WARNING]'
                    }.items():
                        safe_arg = safe_arg.replace(emoji, replacement)
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            record.args = tuple(safe_args)

        return True


def setup_logging():
    """Setup comprehensive logging configuration for the application"""

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

    # Comprehensive logging configuration
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'file': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'scheduler': {
                'format': '%(asctime)s [SCHEDULER] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            # Legacy formatters for backward compatibility
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
            'file_unicode_filter': {
                '()': FileUnicodeFilter,
            },
        },
        'handlers': {
            # Enhanced console handler
            'console': {
                'level': 'INFO',
                'formatter': 'console',
                'class': 'app.config.logging_config.EnhancedConsoleHandler',
                'filters': ['unicode_filter'],
            },
            # Legacy default handler for backward compatibility
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': ['unicode_filter'],
            },
            # File handlers
            'file': {
                'level': 'DEBUG',
                'formatter': 'file',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
                'filters': ['file_unicode_filter'],
            },
            'error_file': {
                'level': 'ERROR',
                'formatter': 'file',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
                'filters': ['file_unicode_filter'],
            },
            # Scheduler-specific handlers
            'scheduler_console': {
                'level': 'INFO',
                'formatter': 'scheduler',
                'class': 'app.config.logging_config.EnhancedConsoleHandler',
                'filters': ['unicode_filter'],
            },
            'scheduler_file': {
                'level': 'DEBUG',
                'formatter': 'scheduler',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/scheduler.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
                'filters': ['file_unicode_filter'],
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': False
            },
            'async_scheduler': {  # scheduler logger
                'handlers': ['scheduler_console', 'scheduler_file', 'file'],
                'level': 'DEBUG',
                'propagate': False
            },
            'app.core.jobs.scheduler': {  # scheduler module logger
                'handlers': ['scheduler_console', 'scheduler_file', 'file'],
                'level': 'DEBUG',
                'propagate': False
            },
            '__main__': {  # main application logger
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }

    logging.config.dictConfig(LOGGING_CONFIG)

    # Test the logging setup
    logger = logging.getLogger(__name__)
    logger.info("🚀 Consolidated logging configuration loaded successfully!")
    logger.info(f"📁 Log files location: {log_dir.absolute()}")
    logger.info("📋 Available log files:")
    logger.info("   • logs/app.log - General application logs")
    logger.info("   • logs/scheduler.log - Scheduler-specific logs")
    logger.info("   • logs/error.log - Error logs only")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    return logging.getLogger(name)


def log_to_console_and_file(message: str, level: str = "INFO"):
    """Utility function to force log to both console and file"""
    logger = logging.getLogger("console_logger")

    if level.upper() == "DEBUG":
        logger.debug(message)
    elif level.upper() == "INFO":
        logger.info(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message)
    else:
        logger.info(message)

    # Also force to stdout
    print(f"[{level}] {message}")
    sys.stdout.flush()