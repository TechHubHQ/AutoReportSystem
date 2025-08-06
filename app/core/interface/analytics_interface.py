from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, func
from app.database.db_connector import get_db
from app.database.models import Task, User
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def get_dashboard_summary(user_id: Optional[int] = None) -> Dict:
    """Get comprehensive dashboard summary data"""
    try:
        db = await get_db()

        # Base query for tasks
        base_query = select(Task)
        if user_id:
            base_query = base_query.where(Task.created_by == user_id)

        result = await db.execute(base_query)
        tasks = result.scalars().all()

        # Calculate summary statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        in_progress_tasks = len([t for t in tasks if t.status == 'inprogress'])
        pending_tasks = len([t for t in tasks if t.status == 'pending'])
        todo_tasks = len([t for t in tasks if t.status == 'todo'])

        # Priority breakdown
        high_priority = len(
            [t for t in tasks if t.priority in ['high', 'urgent']])
        overdue_tasks = len([
            t for t in tasks
            if t.due_date and t.due_date < datetime.now() and t.status != 'completed'
        ])

        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_tasks = len([t for t in tasks if t.created_at >= week_ago])
        recent_completions = len([
            t for t in tasks
            if t.status == 'completed' and t.updated_at >= week_ago
        ])

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'pending_tasks': pending_tasks,
            'todo_tasks': todo_tasks,
            'high_priority_tasks': high_priority,
            'overdue_tasks': overdue_tasks,
            'recent_tasks': recent_tasks,
            'recent_completions': recent_completions,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise e
    finally:
        await db.close()


async def get_task_completion_trends(user_id: Optional[int] = None, days: int = 30) -> Dict:
    """Get task completion trends over specified days"""
    try:
        db = await get_db()

        # Get tasks for the specified period
        start_date = datetime.now() - timedelta(days=days)
        base_query = select(Task).where(Task.created_at >= start_date)
        if user_id:
            base_query = base_query.where(Task.created_by == user_id)

        result = await db.execute(base_query)
        tasks = result.scalars().all()

        # Generate daily completion data
        daily_data = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date()
            daily_data[date.isoformat()] = {
                'created': 0,
                'completed': 0,
                'date': date.isoformat()
            }

        # Count tasks by day
        for task in tasks:
            created_date = task.created_at.date().isoformat()
            if created_date in daily_data:
                daily_data[created_date]['created'] += 1

            if task.status == 'completed' and task.updated_at:
                completed_date = task.updated_at.date().isoformat()
                if completed_date in daily_data:
                    daily_data[completed_date]['completed'] += 1

        return {
            'daily_trends': list(daily_data.values()),
            'total_period_tasks': len(tasks),
            'period_completions': len([t for t in tasks if t.status == 'completed'])
        }

    except Exception as e:
        logger.error(f"Error getting task completion trends: {e}")
        raise e
    finally:
        await db.close()


async def get_productivity_insights(user_id: Optional[int] = None) -> Dict:
    """Get productivity insights and recommendations"""
    try:
        db = await get_db()

        base_query = select(Task)
        if user_id:
            base_query = base_query.where(Task.created_by == user_id)

        result = await db.execute(base_query)
        tasks = result.scalars().all()

        if not tasks:
            return {
                'insights': [],
                'recommendations': ['Create your first task to start tracking productivity!']
            }

        insights = []
        recommendations = []

        # Analyze completion patterns
        completed_tasks = [t for t in tasks if t.status == 'completed']
        completion_rate = len(completed_tasks) / len(tasks) * 100

        if completion_rate > 80:
            insights.append(
                f"Excellent completion rate: {completion_rate:.1f}%")
        elif completion_rate > 60:
            insights.append(f"Good completion rate: {completion_rate:.1f}%")
            recommendations.append(
                "Consider breaking down larger tasks for better completion rates")
        else:
            insights.append(
                f"Completion rate needs improvement: {completion_rate:.1f}%")
            recommendations.append(
                "Focus on completing existing tasks before creating new ones")

        # Analyze overdue tasks
        overdue_tasks = [
            t for t in tasks
            if t.due_date and t.due_date < datetime.now() and t.status != 'completed'
        ]

        if overdue_tasks:
            insights.append(f"{len(overdue_tasks)} tasks are overdue")
            recommendations.append(
                "Prioritize overdue tasks to improve time management")

        # Analyze priority distribution
        high_priority = len(
            [t for t in tasks if t.priority in ['high', 'urgent']])
        if high_priority > len(tasks) * 0.5:
            insights.append("Many tasks marked as high priority")
            recommendations.append(
                "Review task priorities - not everything can be urgent")

        return {
            'insights': insights,
            'recommendations': recommendations,
            'completion_rate': completion_rate,
            'total_tasks': len(tasks),
            'overdue_count': len(overdue_tasks)
        }

    except Exception as e:
        logger.error(f"Error getting productivity insights: {e}")
        raise e
    finally:
        await db.close()
