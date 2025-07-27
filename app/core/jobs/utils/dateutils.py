from datetime import datetime, timedelta, timezone


def next_monthly_run(hour=16, minute=20) -> float:
    now = datetime.now(timezone.utc)
    # Get first day of next month
    year, month = now.year, now.month
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    # Last day of this month
    last_day = next_month - timedelta(days=1)
    # Move back to last weekday if needed
    while last_day.weekday() >= 5:
        last_day -= timedelta(days=1)
    run_time = last_day.replace(
        hour=hour, minute=minute, second=0, microsecond=0)
    if now >= run_time:
        # Recurse for next month
        return next_monthly_run(hour, minute)
    return run_time.timestamp()
