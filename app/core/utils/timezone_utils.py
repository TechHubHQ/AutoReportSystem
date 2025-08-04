"""
Timezone Utilities for AutomateReportSystem

Provides timezone conversion utilities for IST (Indian Standard Time) support.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz

# IST timezone (UTC+5:30)
IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC


def get_ist_timezone():
    """Get IST timezone object"""
    return IST


def get_utc_timezone():
    """Get UTC timezone object"""
    return UTC


def now_ist() -> datetime:
    """Get current time in IST"""
    return datetime.now(IST)


def now_utc() -> datetime:
    """Get current time in UTC"""
    return datetime.now(UTC)


def ist_to_utc(ist_datetime: datetime) -> datetime:
    """Convert IST datetime to UTC"""
    if ist_datetime.tzinfo is None:
        # Assume it's IST if no timezone info
        ist_datetime = IST.localize(ist_datetime)
    elif ist_datetime.tzinfo != IST:
        # Convert to IST first if it's in a different timezone
        ist_datetime = ist_datetime.astimezone(IST)
    
    return ist_datetime.astimezone(UTC)


def utc_to_ist(utc_datetime: datetime) -> datetime:
    """Convert UTC datetime to IST"""
    if utc_datetime.tzinfo is None:
        # Assume it's UTC if no timezone info
        utc_datetime = UTC.localize(utc_datetime)
    elif utc_datetime.tzinfo != UTC:
        # Convert to UTC first if it's in a different timezone
        utc_datetime = utc_datetime.astimezone(UTC)
    
    return utc_datetime.astimezone(IST)


def format_ist_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S IST") -> str:
    """Format datetime in IST with custom format"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = UTC.localize(dt)
    
    ist_dt = dt.astimezone(IST)
    return ist_dt.strftime(format_str)


def format_ist_time_short(dt: datetime) -> str:
    """Format datetime in IST with short format"""
    return format_ist_time(dt, "%d-%m-%Y %H:%M IST")


def format_ist_time_display(dt: datetime) -> str:
    """Format datetime for UI display"""
    return format_ist_time(dt, "%d %b %Y, %I:%M %p IST")


def parse_ist_time(time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse time string as IST"""
    dt = datetime.strptime(time_str, format_str)
    return IST.localize(dt)


def create_ist_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """Create IST datetime"""
    dt = datetime(year, month, day, hour, minute, second)
    return IST.localize(dt)


def get_ist_offset_hours() -> float:
    """Get IST offset from UTC in hours"""
    return 5.5  # IST is UTC+5:30


def get_ist_offset_seconds() -> int:
    """Get IST offset from UTC in seconds"""
    return int(5.5 * 3600)  # 5.5 hours in seconds


def seconds_until_ist_time(day_of_week: int, hour: int, minute: int) -> float:
    """Calculate seconds until next occurrence of specified IST time"""
    now = now_ist()
    today = now.weekday()
    
    # Create target time in IST
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Calculate days ahead
    days_ahead = (day_of_week - today + 7) % 7
    if days_ahead == 0 and now >= target:
        days_ahead = 7
    
    next_run = target + timedelta(days=days_ahead)
    return (next_run - now).total_seconds()


def next_monthly_run_ist(day_of_month: int, hour: int = 9, minute: int = 0) -> float:
    """Calculate next monthly run time in IST and return as timestamp"""
    now = now_ist()
    
    # Try current month first
    try:
        target = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        if now < target:
            return target.timestamp()
    except ValueError:
        # Day doesn't exist in current month (e.g., Feb 30)
        pass
    
    # Move to next month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    
    # Find the target day in next month
    try:
        target = next_month.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        return target.timestamp()
    except ValueError:
        # Day doesn't exist in next month, use last day of month
        if next_month.month == 12:
            last_day = next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1)
        
        target = last_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return target.timestamp()


def get_next_daily_run_ist(hour: int, minute: int) -> datetime:
    """Get next daily run time in IST"""
    now = now_ist()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If the target time has passed today, schedule for tomorrow
    if now >= target:
        target += timedelta(days=1)
    
    return target


def get_next_weekly_run_ist(day_of_week: int, hour: int, minute: int) -> datetime:
    """Get next weekly run time in IST"""
    now = now_ist()
    today = now.weekday()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    days_ahead = (day_of_week - today + 7) % 7
    if days_ahead == 0 and now >= target:
        days_ahead = 7
    
    next_run = target + timedelta(days=days_ahead)
    return next_run


def get_next_monthly_run_ist(day_of_month: int, hour: int, minute: int) -> datetime:
    """Get next monthly run time in IST"""
    timestamp = next_monthly_run_ist(day_of_month, hour, minute)
    return datetime.fromtimestamp(timestamp, IST)


def format_schedule_display(schedule_type: str, config: dict) -> str:
    """Format schedule configuration for UI display in IST"""
    if schedule_type == "daily":
        hour = config.get('hour', 9)
        minute = config.get('minute', 0)
        return f"Daily at {hour:02d}:{minute:02d} IST"
    
    elif schedule_type == "weekly":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_of_week = config.get('day_of_week', 0)
        hour = config.get('hour', 9)
        minute = config.get('minute', 0)
        day_name = days[day_of_week] if 0 <= day_of_week < 7 else "Monday"
        return f"Weekly on {day_name} at {hour:02d}:{minute:02d} IST"
    
    elif schedule_type == "monthly":
        day_of_month = config.get('day_of_month', 1)
        hour = config.get('hour', 9)
        minute = config.get('minute', 0)
        return f"Monthly on day {day_of_month} at {hour:02d}:{minute:02d} IST"
    
    elif schedule_type == "custom":
        cron = config.get('cron', '')
        return f"Custom: {cron} (IST)" if cron else "Custom (IST)"
    
    return f"{schedule_type.title()} (IST)"


def get_next_run_in_minutes(minutes: int) -> datetime:
    """Get a time that's X minutes from now in IST (for testing)"""
    now = now_ist()
    return now + timedelta(minutes=minutes)


def get_timezone_info() -> dict:
    """Get timezone information for display"""
    now_ist_time = now_ist()
    now_utc_time = now_utc()
    
    return {
        'timezone': 'IST',
        'full_name': 'Indian Standard Time',
        'offset': '+05:30',
        'current_ist': format_ist_time_display(now_ist_time),
        'current_utc': now_utc_time.strftime("%d %b %Y, %I:%M %p UTC"),
        'offset_hours': 5.5
    }