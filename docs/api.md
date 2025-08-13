# API Documentation

## Overview

AutoReportSystem provides a comprehensive set of internal APIs for managing tasks, jobs, users, and system operations. While the primary interface is the Streamlit web application, the underlying API structure is designed for extensibility and potential future REST API exposure.

## Core Interfaces

### Task Interface

The Task Interface provides comprehensive task management functionality.

#### Methods

##### `get_tasks(user_id: int = None, status: str = None, limit: int = 100)`
Retrieve tasks with optional filtering.

**Parameters:**
- `user_id` (int, optional): Filter tasks by user ID
- `status` (str, optional): Filter by task status (todo, inprogress, pending, completed)
- `limit` (int): Maximum number of tasks to return (default: 100)

**Returns:**
- `List[Task]`: List of task objects

**Example:**
```python
from app.core.interface.task_interface import get_tasks

# Get all tasks for user
tasks = await get_tasks(user_id=1)

# Get only completed tasks
completed_tasks = await get_tasks(user_id=1, status="completed")
```

##### `create_task(title: str, description: str = None, **kwargs)`
Create a new task.

**Parameters:**
- `title` (str): Task title (required)
- `description` (str, optional): Task description
- `status` (str): Task status (default: "todo")
- `priority` (str): Task priority (default: "medium")
- `category` (str): Task category (default: "in progress")
- `due_date` (datetime, optional): Due date
- `created_by` (int): User ID of creator

**Returns:**
- `Task`: Created task object

**Example:**
```python
from app.core.interface.task_interface import create_task
from datetime import datetime

task = await create_task(
    title="Complete project documentation",
    description="Write comprehensive API docs",
    priority="high",
    due_date=datetime(2024, 2, 15),
    created_by=1
)
```

##### `update_task(task_id: int, **kwargs)`
Update an existing task.

**Parameters:**
- `task_id` (int): Task ID to update
- `**kwargs`: Fields to update (title, description, status, priority, etc.)

**Returns:**
- `Task`: Updated task object

**Example:**
```python
from app.core.interface.task_interface import update_task

updated_task = await update_task(
    task_id=1,
    status="completed",
    updated_by=1
)
```

##### `delete_task(task_id: int)`
Delete a task.

**Parameters:**
- `task_id` (int): Task ID to delete

**Returns:**
- `bool`: True if successful

##### `get_task_statistics(user_id: int = None)`
Get task statistics and metrics.

**Parameters:**
- `user_id` (int, optional): Filter statistics by user

**Returns:**
- `dict`: Statistics including total, completed, in progress, pending counts

**Example:**
```python
from app.core.interface.task_interface import get_task_statistics

stats = await get_task_statistics(user_id=1)
# Returns: {"total": 25, "completed": 15, "inprogress": 5, "pending": 3, "todo": 2}
```

### User Interface

Manages user accounts, authentication, and user-related operations.

#### Methods

##### `create_user(username: str, email: str, password: str, userrole: str = "Software Engineer")`
Create a new user account.

**Parameters:**
- `username` (str): Unique username
- `email` (str): User email address
- `password` (str): Plain text password (will be hashed)
- `userrole` (str): User role (default: "Software Engineer")

**Returns:**
- `User`: Created user object

##### `authenticate_user(username: str, password: str)`
Authenticate user credentials.

**Parameters:**
- `username` (str): Username or email
- `password` (str): Plain text password

**Returns:**
- `User | None`: User object if authentication successful, None otherwise

##### `get_user_by_id(user_id: int)`
Retrieve user by ID.

**Parameters:**
- `user_id` (int): User ID

**Returns:**
- `User | None`: User object if found

##### `update_user(user_id: int, **kwargs)`
Update user information.

**Parameters:**
- `user_id` (int): User ID to update
- `**kwargs`: Fields to update (username, email, userrole)

**Returns:**
- `User`: Updated user object

### Job Interface

Manages scheduled jobs and automation tasks.

#### Methods

##### `get_jobs(is_active: bool = None, is_custom: bool = None)`
Retrieve jobs with optional filtering.

**Parameters:**
- `is_active` (bool, optional): Filter by active status
- `is_custom` (bool, optional): Filter by custom vs auto-discovered jobs

**Returns:**
- `List[Job]`: List of job objects

##### `create_job(name: str, function_name: str, module_path: str, schedule_type: str, **kwargs)`
Create a new scheduled job.

**Parameters:**
- `name` (str): Unique job name
- `function_name` (str): Function to execute
- `module_path` (str): Python module path
- `schedule_type` (str): Schedule type (weekly, monthly, daily, custom)
- `description` (str, optional): Job description
- `schedule_config` (str, optional): JSON schedule configuration
- `is_active` (bool): Whether job is active (default: True)

**Returns:**
- `Job`: Created job object

##### `update_job(job_id: int, **kwargs)`
Update job configuration.

**Parameters:**
- `job_id` (int): Job ID to update
- `**kwargs`: Fields to update

**Returns:**
- `Job`: Updated job object

##### `execute_job(job_id: int)`
Manually execute a job.

**Parameters:**
- `job_id` (int): Job ID to execute

**Returns:**
- `dict`: Execution result with status and output

### Template Interface

Manages email templates for automated reporting.

#### Methods

##### `get_templates(user_id: int = None, category: str = None, is_active: bool = True)`
Retrieve email templates.

**Parameters:**
- `user_id` (int, optional): Filter by creator
- `category` (str, optional): Filter by category
- `is_active` (bool): Filter by active status

**Returns:**
- `List[EmailTemplate]`: List of template objects

##### `create_template(name: str, subject: str, html_content: str, created_by: int, **kwargs)`
Create a new email template.

**Parameters:**
- `name` (str): Template name
- `subject` (str): Email subject
- `html_content` (str): HTML template content
- `created_by` (int): Creator user ID
- `description` (str, optional): Template description
- `category` (str): Template category (default: "General")

**Returns:**
- `EmailTemplate`: Created template object

##### `update_template(template_id: int, **kwargs)`
Update template content or metadata.

**Parameters:**
- `template_id` (int): Template ID to update
- `**kwargs`: Fields to update

**Returns:**
- `EmailTemplate`: Updated template object

##### `render_template(template_id: int, variables: dict = None)`
Render template with variables.

**Parameters:**
- `template_id` (int): Template ID to render
- `variables` (dict, optional): Variables for template substitution

**Returns:**
- `str`: Rendered HTML content

### SMTP Interface

Manages SMTP configurations for email delivery.

#### Methods

##### `get_smtp_configs(user_email: str = None, is_active: bool = True)`
Retrieve SMTP configurations.

**Parameters:**
- `user_email` (str, optional): Filter by user email
- `is_active` (bool): Filter by active status

**Returns:**
- `List[SMTPConf]`: List of SMTP configuration objects

##### `create_smtp_config(smtp_host: str, smtp_port: int, smtp_username: str, smtp_password: str, sender_email: str)`
Create SMTP configuration.

**Parameters:**
- `smtp_host` (str): SMTP server hostname
- `smtp_port` (int): SMTP server port
- `smtp_username` (str): SMTP username
- `smtp_password` (str): SMTP password (will be encrypted)
- `sender_email` (str): Sender email address

**Returns:**
- `SMTPConf`: Created SMTP configuration

##### `test_smtp_connection(config_id: int)`
Test SMTP connection.

**Parameters:**
- `config_id` (int): SMTP configuration ID

**Returns:**
- `dict`: Test result with success status and message

### Analytics Interface

Provides analytics and insights for tasks and productivity.

#### Methods

##### `get_task_completion_trends(user_id: int = None, days: int = 30)`
Get task completion trends over time.

**Parameters:**
- `user_id` (int, optional): Filter by user
- `days` (int): Number of days to analyze (default: 30)

**Returns:**
- `dict`: Trend data with daily completion and creation counts

##### `get_productivity_insights(user_id: int = None)`
Get AI-powered productivity insights.

**Parameters:**
- `user_id` (int, optional): Filter by user

**Returns:**
- `dict`: Insights and recommendations

### Metrics Interface

System monitoring and performance metrics.

#### Methods

##### `get_current_system_status()`
Get current system performance metrics.

**Returns:**
- `dict`: Current CPU, memory, disk usage and health score

##### `get_historical_metrics(hours: int = 24)`
Get historical system metrics.

**Parameters:**
- `hours` (int): Number of hours of historical data

**Returns:**
- `dict`: Historical metrics data

##### `get_system_info()`
Get system information.

**Returns:**
- `dict`: System details including CPU, memory, platform info

## Data Models

### Task Model
```python
class Task:
    id: int
    title: str
    description: str | None
    status: str  # todo, inprogress, pending, completed
    priority: str  # low, medium, high, urgent
    category: str  # accomplishments, in progress
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: int
```

### User Model
```python
class User:
    id: int
    username: str
    email: str
    password: str  # hashed
    userrole: str
```

### Job Model
```python
class Job:
    id: int
    name: str
    description: str | None
    function_name: str
    module_path: str
    schedule_type: str  # weekly, monthly, daily, custom
    code: str | None
    schedule_config: str | None  # JSON
    is_active: bool
    is_custom: bool
    last_run: datetime | None
    next_run: datetime | None
    created_at: datetime
    updated_at: datetime
```

### EmailTemplate Model
```python
class EmailTemplate:
    id: int
    name: str
    subject: str
    description: str | None
    category: str
    html_content: str
    file_path: str | None
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
```

### SMTPConf Model
```python
class SMTPConf:
    id: int
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str  # encrypted
    sender_email: str
    is_active: str
```

## Error Handling

All interface methods use consistent error handling:

### Common Exceptions
- `ValueError`: Invalid input parameters
- `NotFoundError`: Resource not found
- `AuthenticationError`: Authentication failed
- `PermissionError`: Insufficient permissions
- `DatabaseError`: Database operation failed

### Error Response Format
```python
{
    "error": True,
    "message": "Error description",
    "code": "ERROR_CODE",
    "details": {...}  # Additional error details
}
```

## Usage Examples

### Complete Task Workflow
```python
from app.core.interface.task_interface import create_task, update_task, get_tasks
from app.core.interface.user_interface import authenticate_user
from datetime import datetime

# Authenticate user
user = await authenticate_user("john_doe", "password123")

# Create task
task = await create_task(
    title="Implement new feature",
    description="Add user authentication system",
    priority="high",
    due_date=datetime(2024, 2, 20),
    created_by=user.id
)

# Update task status
await update_task(task.id, status="inprogress", updated_by=user.id)

# Get user's tasks
user_tasks = await get_tasks(user_id=user.id)
```

### Job Automation Setup
```python
from app.core.interface.job_interface import create_job
from app.core.interface.template_interface import create_template

# Create email template
template = await create_template(
    name="Weekly Report",
    subject="Weekly Task Summary",
    html_content="<h1>Tasks Completed: {{tasks_completed}}</h1>",
    created_by=user.id,
    category="Reports"
)

# Create scheduled job
job = await create_job(
    name="weekly_task_report",
    function_name="send_weekly_report",
    module_path="app.core.jobs.tasks.report_sender",
    schedule_type="weekly",
    description="Send weekly task completion report",
    schedule_config='{"day_of_week": "monday", "hour": 9}'
)
```

### Analytics and Insights
```python
from app.core.interface.analytics_interface import get_task_completion_trends, get_productivity_insights

# Get completion trends
trends = await get_task_completion_trends(user_id=user.id, days=30)

# Get productivity insights
insights = await get_productivity_insights(user_id=user.id)

print(f"Tasks completed in last 30 days: {sum(trends['daily_trends'])}")
print(f"Productivity insights: {insights['insights']}")
```

## Future API Enhancements

### Planned REST API
A REST API is planned for future releases with the following endpoints:

```
GET    /api/v1/tasks              # List tasks
POST   /api/v1/tasks              # Create task
GET    /api/v1/tasks/{id}         # Get task
PUT    /api/v1/tasks/{id}         # Update task
DELETE /api/v1/tasks/{id}         # Delete task

GET    /api/v1/jobs               # List jobs
POST   /api/v1/jobs               # Create job
GET    /api/v1/jobs/{id}          # Get job
PUT    /api/v1/jobs/{id}          # Update job
POST   /api/v1/jobs/{id}/execute  # Execute job

GET    /api/v1/templates          # List templates
POST   /api/v1/templates          # Create template
GET    /api/v1/templates/{id}     # Get template
PUT    /api/v1/templates/{id}     # Update template

GET    /api/v1/analytics/trends   # Get trends
GET    /api/v1/analytics/insights # Get insights
GET    /api/v1/metrics/system     # System metrics
```

### Authentication
Future REST API will support:
- JWT token authentication
- API key authentication
- OAuth 2.0 integration
- Rate limiting and throttling

This API documentation provides a comprehensive guide to the internal interfaces available in AutoReportSystem. For the most up-to-date information, refer to the source code and inline documentation.