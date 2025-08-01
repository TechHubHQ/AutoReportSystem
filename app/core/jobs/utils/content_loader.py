import re
from datetime import datetime
from app.core.interface.task_interface import get_weekly_tasks, get_monthly_tasks, get_tasks_by_category, get_task_statistics


async def load_content(timeframe):
    if timeframe == "weekly":
        content = await get_weekly_tasks()
    elif timeframe == "monthly":
        content = await get_monthly_tasks()
    return content


async def process_dynamic_content(template_content: str, user_id: int = None) -> dict:
    """Process dynamic placeholders in template content and return context data"""
    context = {}
    
    # Find all dynamic placeholders [placeholder_name]
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
