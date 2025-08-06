import re
from datetime import datetime
from app.core.interface.task_interface import (
    get_weekly_tasks, get_monthly_tasks, get_tasks_by_category, get_task_statistics)
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def load_content(timeframe, user_id: int = None):
    """Load content based on timeframe - legacy function"""
    if timeframe == "weekly":
        content = await get_weekly_tasks(user_id)
    elif timeframe == "monthly":
        content = await get_monthly_tasks(user_id)
    else:
        content = {}
    return content


async def load_dynamic_content(content_type: str = "all", user_id: int = None):
    """Load content for any template type"""
    content = {}

    try:
        if content_type in ["weekly", "all"]:
            content['weekly_tasks'] = await get_weekly_tasks(user_id)

        if content_type in ["monthly", "all"]:
            content['monthly_tasks'] = await get_monthly_tasks(user_id)

        if content_type in ["accomplishments", "all"]:
            accomplishments = await get_tasks_by_category('accomplishments', user_id)
            content['accomplishments'] = [
                task.title for task in accomplishments]

        if content_type in ["in_progress", "all"]:
            in_progress = await get_tasks_by_category('in progress', user_id)
            content['in_progress'] = [task.title for task in in_progress]

        if content_type in ["stats", "all"]:
            content['task_stats'] = await get_task_statistics(user_id)

        # Always include date/time information
        from datetime import datetime
        content['current_date'] = datetime.now().strftime('%Y-%m-%d')
        content['current_week'] = datetime.now().strftime('Week %U, %Y')
        content['current_month'] = datetime.now().strftime('%B %Y')
        content['current_year'] = datetime.now().strftime('%Y')

    except Exception as e:
        logger.error(f"Error loading content: {e}")

    return content


async def process_dynamic_content(template_content: str, user_id: int = None) -> dict:
    """Process placeholders in template content and return context data"""
    context = {}

    # Find all placeholders [placeholder_name]
    placeholders = re.findall(r'\[([^\]]+)\]', template_content)

    for placeholder in placeholders:
        if placeholder == 'weekly_tasks':
            tasks = await get_weekly_tasks(user_id)
            context['weekly_tasks'] = [{
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'category': task.category
            } for task in tasks]

        elif placeholder == 'monthly_tasks':
            tasks = await get_monthly_tasks(user_id)
            context['monthly_tasks'] = [{
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'category': task.category
            } for task in tasks]

        elif placeholder == 'accomplishments':
            tasks = await get_tasks_by_category('accomplishments', user_id)
            context['accomplishments'] = [task.title for task in tasks]

        elif placeholder == 'in_progress':
            tasks = await get_tasks_by_category('in progress', user_id)
            context['in_progress'] = [task.title for task in tasks]

        elif placeholder == 'task_stats':
            stats = await get_task_statistics(user_id)
            context['task_stats'] = stats

        elif placeholder == 'current_date':
            context['current_date'] = datetime.now().strftime('%Y-%m-%d')

        elif placeholder == 'current_week':
            context['current_week'] = datetime.now().strftime('Week %U, %Y')

        elif placeholder == 'current_month':
            context['current_month'] = datetime.now().strftime('%B %Y')

    return context
