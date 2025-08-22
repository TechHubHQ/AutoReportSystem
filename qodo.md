# Repository Tour

## 🎯 What This Repository Does

AutoReportSystem is a comprehensive task management and automated reporting platform built with modern Python technologies. It streamlines reporting workflows with intelligent automation, providing a complete solution for task tracking, analytics, and automated report generation.

**Key responsibilities:**
- Task management with interactive Kanban board and analytics
- Automated report generation with customizable templates and scheduling
- Email integration with SMTP configuration and template-based delivery

---

## 🏗️ Architecture Overview

### System Context
```
[Users] → [Streamlit UI] → [AutoReportSystem] → [PostgreSQL Database]
                                    ↓
                            [Email/SMTP Services]
                                    ↓
                            [Background Job Scheduler]
```

### Key Components
- **Streamlit UI Layer** - Interactive web interface with modern components and real-time updates
- **Core Business Logic** - Services, interfaces, and utilities for task management and automation
- **Security Layer** - Authentication, authorization, and session management with backend storage
- **Job Scheduler** - APScheduler-based background task processing with monitoring
- **Database Layer** - PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Integration Layer** - Email services, Git integration, and external API connections

### Data Flow
1. User interacts with Streamlit UI for task management and configuration
2. Business logic processes requests through service interfaces
3. Data is persisted to PostgreSQL database with audit trails
4. Background scheduler executes automated jobs (reports, lifecycle management)
5. Email service delivers reports using customizable templates
6. System metrics and job execution data provide monitoring insights

---

## 📁 Project Structure [Partial Directory Tree]

```
AutoReportSystem/
├── app/                          # Main application package
│   ├── config/                   # Configuration management
│   │   ├── config.py            # Application settings
│   │   └── logging_config.py    # Logging configuration
│   ├── core/                     # Core business logic
│   │   ├── interface/           # Service interfaces (12 modules)
│   │   ├── jobs/                # Background job system & scheduler
│   │   ├── services/            # Business services (encryption, etc.)
│   │   └── utils/               # Utility functions & helpers
│   ├── database/                # Database models, connections & migrations
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── db_connector.py      # Database connection management
│   │   └── migrations.py        # Migration utilities
│   ├── integrations/            # External service integrations
│   │   ├── email/               # Email templates & SMTP integration
│   │   └── git/                 # Git integration services
│   ├── security/                # Authentication & authorization
│   │   ├── auth/                # Authentication modules
│   │   ├── backend_session_manager.py  # Session management
│   │   ├── middleware.py        # Security middleware
│   │   └── route_protection.py  # Route access control
│   └── ui/                      # User interface components
│       ├── components/          # Reusable UI components (5 modules)
│       ├── dashboard.py         # Main dashboard
│       ├── jobs_dashboard.py    # Job management interface
│       └── template_designer.py # Template creation interface
├── alembic/                     # Database migrations
│   ├── versions/               # Migration scripts
│   └── env.py                  # Alembic configuration
├── docs/                        # Documentation
├── infra/                       # Infrastructure & deployment
│   ├── Dockerfile              # Development Docker image
│   ├── Dockerfile.prod         # Production Docker image
│   └── nginx.conf              # Nginx configuration
├── logs/                        # Application logs
├── tests/                       # Test suite
├── main.py                      # Application entry point
├── pyproject.toml              # Project configuration with uv
└── uv.lock                     # Dependency lock file
```

### Key Files to Know

| File | Purpose | When You'd Touch It |
|------|---------|---------------------|
| `main.py` | Streamlit application entry point | Adding new pages/routes |
| `app/database/models.py` | SQLAlchemy database models | Adding new data structures |
| `app/core/jobs/scheduler.py` | Background job scheduler | Modifying job execution logic |
| `pyproject.toml` | Project dependencies and configuration | Adding new libraries |
| `app/config/config.py` | Application settings | Changing configuration |
| `alembic.ini` | Database migration configuration | Database schema changes |
| `app/security/route_protection.py` | Authentication and route access | Adding security features |
| `app/ui/dashboard.py` | Main dashboard interface | Modifying UI components |
| `infra/Dockerfile.prod` | Production deployment | Deployment configuration |

---

## 🔧 Technology Stack

### Core Technologies
- **Language:** Python 3.12+ - Modern Python with latest features and performance improvements
- **Framework:** Streamlit 1.47+ - Rapid web app development with enhanced UI components
- **Database:** PostgreSQL 13+ - Advanced relational database with JSON support
- **ORM:** SQLAlchemy 2.0+ - Modern Python SQL toolkit with async support

### Key Libraries
- **APScheduler 3.11+** - Advanced Python Scheduler for background job processing
- **AsyncPG 0.30+** - High-performance async PostgreSQL driver
- **Plotly 5.0+** - Interactive data visualization for analytics dashboards
- **bcrypt 3.2** - Secure password hashing for authentication
- **Alembic** - Database migration tool for schema management
- **Cryptography 45.0+** - Encryption services for sensitive data

### Development Tools
- **uv** - Fast Python package manager for dependency management
- **pytest 8.4+** - Testing framework with async support
- **python-dotenv** - Environment variable management
- **psutil** - System monitoring and resource tracking

---

## 🌐 External Dependencies

### Required Services
- **PostgreSQL Database** - Primary data storage with full ACID compliance
- **SMTP Server** - Email delivery service (Gmail, Outlook, or custom SMTP)

### Optional Integrations
- **Git Repository** - Auto-commit functionality for template changes
- **System Monitoring** - Built-in CPU, memory, and disk usage tracking

### Environment Variables

```bash
# Required
DB_URL=                    # PostgreSQL connection string
ALEMBIC_URL=              # Database URL for migrations
SMTP_ENV_KEY=             # Encryption key for SMTP credentials

# Optional
DEBUG=                    # Enable debug mode (default: False)
LOG_LEVEL=               # Logging verbosity (default: INFO)
SECRET_KEY=              # Application secret key
SESSION_TIMEOUT=         # Session timeout in seconds (default: 3600)
```

---

## 🔄 Common Workflows

### Task Management Workflow
1. User creates tasks with priorities, due dates, and categories
2. Tasks are displayed on interactive Kanban board with color coding
3. Status changes are tracked with audit history
4. Progress notes and issue documentation are added
5. Analytics provide insights on productivity and completion trends

**Code path:** `ui/dashboard.py` → `core/interface/task_interface.py` → `database/models.py`

### Automated Report Generation
1. User configures email templates with dynamic content
2. Jobs are scheduled using cron expressions or intervals
3. Background scheduler executes report generation
4. Data is collected from database and processed
5. Email is sent using configured SMTP settings

**Code path:** `core/jobs/scheduler.py` → `core/jobs/tasks/weekly_reporter.py` → `integrations/email/email_client.py`

### User Authentication & Session Management
1. User credentials are validated against database
2. Secure session token is generated and stored
3. Session data is maintained in backend database
4. Route access is controlled based on authentication status
5. Sessions automatically expire and cleanup occurs

**Code path:** `ui/login.py` → `security/route_protection.py` → `security/backend_session_manager.py`

---

## 📈 Performance & Scale

### Performance Considerations
- **Async Database Operations** - AsyncPG for high-performance database access
- **Connection Pooling** - NullPool configuration prevents connection sharing issues
- **Background Processing** - APScheduler handles long-running tasks without blocking UI
- **Session Management** - Backend database storage for scalable session handling

### Monitoring
- **System Metrics** - Real-time CPU, memory, and disk usage tracking
- **Job Execution** - Comprehensive tracking of scheduled job performance
- **Application Logs** - Structured logging with rotation and Unicode handling
- **Health Checks** - Built-in health monitoring for scheduler and system components

---

## 🚨 Things to Be Careful About

### 🔒 Security Considerations
- **Password Security** - bcrypt hashing with secure salt generation
- **Session Management** - Backend database storage with automatic cleanup
- **Route Protection** - Comprehensive access control for all authenticated routes
- **Data Encryption** - Sensitive SMTP credentials encrypted at rest

### Database Operations
- **Async Context** - Always use async database operations in proper context
- **Migration Safety** - Test migrations in development before production deployment
- **Connection Management** - NullPool prevents async connection sharing issues

### Background Jobs
- **Scheduler Thread Safety** - Thread-safe scheduler instance management
- **Job Monitoring** - Comprehensive execution tracking and error handling
- **Resource Management** - System resource monitoring during job execution

*Updated at: 2025-01-27 UTC*