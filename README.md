# 🚀 AutoReportSystem

A comprehensive task management and automated reporting platform built with modern Python technologies.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.47+-red.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 Task Management

- **Interactive Kanban Board** with drag-and-drop functionality and smart color coding
- **Enhanced Task Cards** with gradient color schemes based on status, priority, and due date urgency
- **Task Notes System** with progress tracking, issue documentation, and resolution notes
- **Task Analytics** with comprehensive analysis and productivity insights
- **Archive System** for historical task management with revive functionality
- **Real-time Updates** with live dashboard metrics and notifications

### 📊 Dashboard & Analytics

- **Multi-Tab Dashboard** with Kanban Board, Analytics, System Monitor, Task Analysis, and Archive views
- **Comprehensive Task Analysis** with detailed tabular reports and CSV export functionality
- **Interactive Visualizations** using Plotly for charts and graphs
- **System Monitoring** with CPU, memory, disk usage tracking and health scores
- **Productivity Insights** with AI-powered recommendations and trend analysis
- **Task Completion Trends** with 30-day analysis and creation vs completion patterns

### ⚙️ Job Automation & Scheduling

- **Advanced Job Scheduler** using APScheduler with flexible scheduling options
- **Automated Report Generation** with customizable templates and delivery
- **Email Integration** with SMTP configuration and template-based delivery
- **Job Monitoring Dashboard** with real-time status and execution tracking
- **Background Task Processing** with persistent job management

### 📝 Template Management & Design

- **Rich Template Designer** with HTML editor and live preview
- **Dynamic Variable System** for personalized content generation
- **Template Categories** with organized library and reusable components
- **Email Template Integration** with SMTP delivery system
- **Template Versioning** and management capabilities

### 🔐 Security & Authentication

- **Secure Authentication System** with bcrypt password hashing
- **Session Management** with persistent and secure user sessions
- **Route Protection** with granular access control
- **Backend Session Manager** with automatic cleanup and restoration
- **Security Middleware** with comprehensive protection layers

### 🎨 Modern UI/UX

- **Enhanced Color System** with soft teal gradients and status-based styling
- **Responsive Design** with modern CSS and smooth animations
- **Interactive Components** with modals, loaders, and notifications
- **Custom Styling** with enhanced visual hierarchy and accessibility
- **Mobile-Friendly** interface with adaptive layouts

## 🏗️ Architecture

AutoReportSystem follows a modern layered architecture with clear separation of concerns:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Presentation Layer                              │
│                    Streamlit UI + Custom Components + Modals                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Application Layer                               │
│                 Interfaces • Services • Business Logic • Jobs                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                Security Layer                                │
│            Authentication • Authorization • Session Management               │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Integration Layer                               │
│                      Email • Git • SMTP • External APIs                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                  Data Layer                                  │
│                 PostgreSQL • SQLAlchemy • Alembic Migrations                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
AutoReportSystem/
├── app/                          # Main application package
│   ├── config/                   # Configuration management
│   ├── core/                     # Core business logic
│   │   ├── interface/           # Service interfaces (12 modules)
│   │   ├── jobs/                # Background job system & scheduler
│   │   ├── services/            # Business services
│   │   └── utils/               # Utility functions & helpers
│   ├── database/                # Database models, connections & migrations
│   ├── integrations/            # External service integrations
│   │   ├── email/               # Email templates & SMTP integration
│   │   └── git/                 # Git integration services
│   ├── security/                # Authentication & authorization
│   │   └── auth/                # Authentication modules
│   └── ui/                      # User interface components
│       └── components/          # Reusable UI components (5 modules)
├── alembic/                     # Database migrations
├── docs/                        # Documentation
├── infra/                       # Infrastructure & deployment
│   ├── Dockerfile              # Production Docker image
│   ├── Dockerfile.prod         # Optimized production build
│   └── nginx.conf              # Nginx configuration
├── logs/                        # Application logs
├── tests/                       # Test suite
├── main.py                      # Application entry point
└── pyproject.toml              # Project configuration with uv
```

## 🛠️ Technology Stack

### Backend & Core

- **[Python 3.12+](https://python.org)** - Modern Python with latest features
- **[Streamlit 1.47+](https://streamlit.io)** - Rapid web app development with enhanced UI
- **[FastAPI 0.116+](https://fastapi.tiangolo.com)** - High-performance async web framework
- **[SQLAlchemy 2.0+](https://sqlalchemy.org)** - Modern Python SQL toolkit and ORM
- **[Alembic](https://alembic.sqlalchemy.org)** - Database migration tool
- **[APScheduler 3.11+](https://apscheduler.readthedocs.io)** - Advanced Python Scheduler

### Database & Storage

- **[PostgreSQL 13+](https://postgresql.org)** - Advanced relational database
- **[AsyncPG 0.30+](https://magicstack.github.io/asyncpg/)** - High-performance async driver

### Frontend & Visualization

- **[Plotly 5.0+](https://plotly.com/python/)** - Interactive data visualization
- **Custom CSS** - Enhanced modern UI/UX with gradients and animations
- **Responsive Design** - Mobile-friendly adaptive layouts

### Security & Authentication

- **[bcrypt 3.2](https://pypi.org/project/bcrypt/)** - Password hashing
- **[Cryptography 45.0+](https://cryptography.io/)** - Encryption and security
- **Custom Session Management** - Secure user sessions with backend storage
- **Route Protection** - Comprehensive access control system

### Development & Tools

- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
- **[pytest 8.4+](https://pytest.org)** - Testing framework with async support
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment management
- **Comprehensive Logging** - Application monitoring and debugging

### Infrastructure

- **[Docker](https://docker.com)** - Containerization with multi-stage builds
- **[Nginx](https://nginx.org)** - Reverse proxy and load balancing
- **Production-ready** - Optimized Docker images and configurations

## 🚀 Installation

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 13 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/AutoReportSystem.git
   cd AutoReportSystem
   ```
2. **Create virtual environment and install dependencies**

   ```bash
   # Using uv (recommended)
   uv sync

   # OR using pip
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```
3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
4. **Initialize database**

   ```bash
   # Run migrations
   alembic upgrade head
   ```
5. **Run the application**

   ```bash
   streamlit run main.py
   ```
6. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

### Docker Installation

1. **Build and run with Docker**

   ```bash
   # Development
   docker build -f infra/Dockerfile -t autoreportsystem:dev .
   docker run -p 8501:8501 autoreportsystem:dev

   # Production
   docker build -f infra/Dockerfile.prod -t autoreportsystem:prod .
   docker run -p 8501:8501 autoreportsystem:prod
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_URL=postgresql+asyncpg://username:password@localhost:5432/autoreportsystem
ALEMBIC_URL=postgresql://username:password@localhost:5432/autoreportsystem

# SMTP Configuration (encrypted)
SMTP_ENV_KEY=your_smtp_encryption_key

# Application Settings
DEBUG=True
LOG_LEVEL=INFO

# Security Settings
SECRET_KEY=your_secret_key_here
SESSION_TIMEOUT=3600

# System Monitoring
ENABLE_METRICS=True
METRICS_RETENTION_HOURS=168
```

### Database Setup

1. **Create PostgreSQL database**

   ```sql
   CREATE DATABASE autoreportsystem;
   CREATE USER ars_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE autoreportsystem TO ars_user;
   ```
2. **Run migrations**

   ```bash
   alembic upgrade head
   ```

### SMTP Configuration

Configure email settings through the application:

1. Navigate to Settings → SMTP Configuration
2. Enter your SMTP server details (encrypted storage)
3. Test the connection
4. Save configuration

## 📖 Usage

### Getting Started

1. **Create an Account**

   - Navigate to the signup page
   - Fill in your details and create account
   - Login with your credentials
2. **Dashboard Overview**

   - **Kanban Board**: Visual task management with color-coded cards
   - **Productivity Analytics**: Charts, metrics, and insights
   - **System Monitor**: Real-time system health and performance
   - **Task Analysis**: Comprehensive task analysis with export
   - **Archive**: Manage archived tasks and historical data
3. **Task Management**

   - Create tasks with priorities, due dates, and categories
   - Use the enhanced Kanban board for visual management
   - Add progress notes, issue documentation, and resolutions
   - Track analytics and productivity insights
4. **Job Automation**

   - Set up scheduled reports and automation
   - Configure email delivery with custom templates
   - Monitor job execution and status
5. **Template Design**

   - Create custom email templates with HTML editor
   - Use dynamic variables for personalization
   - Preview templates before saving

### Key Workflows

#### Creating and Managing Tasks

```python
# Tasks support multiple statuses and categories
task_statuses = ["todo", "inprogress", "pending", "completed"]
task_priorities = ["low", "medium", "high", "urgent"]
task_categories = ["in progress", "accomplishments"]

# Enhanced color coding based on:
# - Status (todo=blue, inprogress=purple, pending=orange, completed=green)
# - Due date urgency (overdue=red, urgent=orange, safe=green, none=teal)
# - Priority levels with visual indicators
```

#### Setting up Automated Reports

1. Go to Jobs Dashboard
2. Create new scheduled job
3. Configure schedule (cron expressions supported)
4. Select email template and recipients
5. Activate job for automatic execution

#### Using Task Analytics

1. Navigate to Task Analysis tab
2. Filter by scope (All Tasks, Current Month, Archived)
3. Filter by status and priority
4. Export detailed analysis to CSV
5. View comprehensive metrics and insights

## 🔧 Development

### Development Setup

1. **Install development dependencies**

   ```bash
   uv sync --dev
   ```
2. **Run in development mode**

   ```bash
   streamlit run main.py --server.runOnSave true
   ```

### Code Quality

- **Formatting**: Black (configured in pyproject.toml)
- **Linting**: Flake8, pylint
- **Type Checking**: mypy
- **Import Sorting**: isort

```bash
# Format code
black .

# Lint code
flake8 app/

# Type check
mypy app/

# Sort imports
isort .
```

### Key Development Features

- **Hot Reload**: Automatic reloading during development
- **Comprehensive Logging**: Detailed application logs in `logs/` directory
- **Session Management**: Persistent sessions with automatic cleanup
- **Error Handling**: Graceful error handling with user feedback
- **Performance Monitoring**: Built-in system metrics and monitoring

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run async tests
pytest -v tests/ --asyncio-mode=auto
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and database operations
- **End-to-End Tests**: Test complete user workflows
- **Async Tests**: Test asynchronous operations and database interactions

## 🚢 Deployment

### Production Deployment

#### Using Docker

1. **Build production image**

   ```bash
   docker build -f infra/Dockerfile.prod -t autoreportsystem:prod .
   ```
2. **Run with environment variables**

   ```bash
   docker run -d \
     --name autoreportsystem \
     -p 8501:8501 \
     -e DB_URL=postgresql://... \
     -e SMTP_ENV_KEY=... \
     autoreportsystem:prod
   ```

#### Cloud Deployment Options

**AWS ECS/Fargate**

- Use the provided Dockerfile.prod
- Configure RDS for PostgreSQL
- Set up Application Load Balancer
- Configure environment variables in ECS

**Heroku**

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SMTP_ENV_KEY=your_key
git push heroku main
```

**Azure Container Instances**

- Build and push to Azure Container Registry
- Deploy using Azure Container Instances
- Configure Azure Database for PostgreSQL

### Environment-Specific Configuration

#### Development

```env
DEBUG=True
LOG_LEVEL=DEBUG
DB_URL=postgresql://localhost:5432/autoreportsystem_dev
```

#### Production

```env
DEBUG=False
LOG_LEVEL=WARNING
DB_URL=postgresql://prod-db:5432/autoreportsystem
ENABLE_METRICS=True
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Ensure all tests pass**
   ```bash
   pytest
   ```
6. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Create a Pull Request**

### Code Review Process

- All changes require review from maintainers
- Automated tests must pass
- Code coverage should not decrease
- Documentation must be updated for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/AutoReportSystem/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/yourusername/AutoReportSystem/discussions)

### Troubleshooting

#### Common Issues

**Database Connection Error**

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify connection string
echo $DB_URL
```

**SMTP Configuration Issues**

- Verify SMTP server settings in the application
- Check firewall and network connectivity
- Ensure authentication credentials are correct
- Test connection through the SMTP Configuration page

**Performance Issues**

- Monitor system resources through the System Monitor tab
- Check database query performance
- Review application logs in the `logs/` directory

#### Debug Mode

Enable debug mode for detailed logging:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 🔮 Roadmap

### Current Version (v0.1.0)

- ✅ Complete task management system with Kanban board
- ✅ Advanced analytics and reporting
- ✅ Job scheduling and automation
- ✅ Template designer with email integration
- ✅ System monitoring and metrics
- ✅ Secure authentication and session management

### Upcoming Features

- [ ] RESTful API endpoints
- [ ] Mobile-responsive enhancements
- [ ] Advanced workflow automation
- [ ] Team collaboration features
- [ ] Real-time notifications
- [ ] Integration marketplace
- [ ] Advanced reporting capabilities

---

<div align="center">

**Built with ❤️ using modern Python technologies**

[⭐ Star us on GitHub](https://github.com/yourusername/AutoReportSystem) • [🐛 Report Bug](https://github.com/yourusername/AutoReportSystem/issues) • [💡 Request Feature](https://github.com/yourusername/AutoReportSystem/issues)

</div>
