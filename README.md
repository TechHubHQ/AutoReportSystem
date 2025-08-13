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
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 Task Management

- **Interactive Kanban Board** with drag-and-drop functionality
- **Smart Color Coding** for status, priority, and due date urgency
- **Task Analytics** with productivity insights and trends
- **Archive System** for historical task management
- **Real-time Updates** with live dashboard metrics

### 📊 Dashboard & Analytics

- **Comprehensive Metrics** - Task completion rates, productivity stats
- **Interactive Visualizations** - Plotly charts and graphs
- **System Monitoring** - CPU, memory, disk usage tracking
- **Trend Analysis** - 30-day completion and creation patterns
- **Productivity Insights** - AI-powered recommendations

### ⚙️ Job Automation

- **Flexible Scheduling** - Weekly, monthly, daily, custom schedules
- **Automated Reporting** - Generate and deliver reports automatically
- **Email Integration** - SMTP-based delivery system
- **Job Monitoring** - Real-time status and execution tracking
- **Custom Job Creation** - Build your own automation workflows

### 📝 Template Management

- **Rich HTML Editor** - Design beautiful email templates
- **Dynamic Variables** - Personalized content generation
- **Template Library** - Organized categories and reusable templates
- **Live Preview** - Real-time template rendering
- **Version Control** - Track template changes and history

### 🔐 Security & Authentication

- **Secure Authentication** - bcrypt password hashing
- **Session Management** - Persistent and secure user sessions
- **Role-based Access** - Granular permission control
- **Data Encryption** - Protect sensitive information
- **Audit Logging** - Track all system activities

## 🏗️ Architecture

AutoReportSystem follows a modern layered architecture with clear separation of concerns:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Presentation Layer                              │
│                       Streamlit UI + Custom Components                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Application Layer                               │
│                    Interfaces • Services • Business Logic                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                Security Layer                                │
│                 Authentication • Authorization • Encryption                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Integration Layer                               │
│                      Email • Git • External APIs • SMTP                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                  Data Layer                                  │
│                 PostgreSQL • SQLAlchemy • Alembic Migrations                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

📖 **[View Detailed Architecture Documentation](docs/architecture.md)**

## 🛠️ Technology Stack

### Backend

- **[Python 3.12+](https://python.org)** - Modern Python with latest features
- **[FastAPI](https://fastapi.tiangolo.com)** - High-performance async web framework
- **[SQLAlchemy](https://sqlalchemy.org)** - Modern Python SQL toolkit and ORM
- **[Alembic](https://alembic.sqlalchemy.org)** - Database migration tool
- **[APScheduler](https://apscheduler.readthedocs.io)** - Advanced Python Scheduler

### Frontend

- **[Streamlit](https://streamlit.io)** - Rapid web app development
- **[Plotly](https://plotly.com/python/)** - Interactive data visualization
- **Custom CSS** - Enhanced modern UI/UX

### Database

- **[PostgreSQL](https://postgresql.org)** - Advanced relational database
- **[AsyncPG](https://magicstack.github.io/asyncpg/)** - High-performance async driver

### Security

- **[bcrypt](https://pypi.org/project/bcrypt/)** - Password hashing
- **Custom Session Management** - Secure user sessions
- **Route Protection** - Access control system

### Infrastructure

- **[Docker](https://docker.com)** - Containerization
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment management
- **Comprehensive Logging** - Application monitoring

## 🚀 Installation

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 13 or higher
- Git

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/AutoReportSystem.git
   cd AutoReportSystem
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   # OR using uv (recommended)
   uv sync
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**

   ```bash
   alembic upgrade head
   ```

6. **Run the application**

   ```bash
   streamlit run main.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

### Docker Installation

1. **Build and run with Docker**

   ```bash
   docker build -t autoreportsystem .
   docker run -p 8501:8501 autoreportsystem
   ```

2. **Using Docker Compose** (recommended)
   ```bash
   docker-compose up -d
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_URL=postgresql+asyncpg://username:password@localhost:5432/autoreportsystem

# SMTP Configuration
SMTP_ENV_KEY=your_smtp_encryption_key

# Application Settings
DEBUG=True
LOG_LEVEL=INFO

# Security Settings
SECRET_KEY=your_secret_key_here
SESSION_TIMEOUT=3600
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

Configure email settings in the application:

1. Navigate to Settings → SMTP Configuration
2. Enter your SMTP server details
3. Test the connection
4. Save configuration

## 📖 Usage

### Getting Started

1. **Create an Account**

   - Navigate to the signup page
   - Fill in your details
   - Verify your email (if configured)

2. **Dashboard Overview**

   - View task statistics and metrics
   - Monitor system performance
   - Access productivity insights

3. **Task Management**

   - Create tasks with priorities and due dates
   - Use the Kanban board for visual management
   - Track progress with analytics

4. **Job Automation**

   - Set up scheduled reports
   - Configure email delivery
   - Monitor job execution

5. **Template Design**
   - Create custom email templates
   - Use dynamic variables
   - Preview before saving

### Key Workflows

#### Creating a Task

```python
# Via UI: Dashboard → New Task
# Or programmatically:
task = {
    "title": "Complete project documentation",
    "description": "Write comprehensive docs",
    "priority": "high",
    "due_date": "2024-02-15",
    "category": "in progress"
}
```

#### Setting up Automated Reports

1. Go to Jobs Dashboard
2. Create new job
3. Configure schedule (weekly/monthly)
4. Select email template
5. Set recipients
6. Activate job

#### Designing Email Templates

1. Navigate to Template Designer
2. Choose template category
3. Design with HTML editor
4. Add dynamic variables
5. Preview and save

## 🔧 Development

### Project Structure

```
AutoReportSystem/
├── app/                          # Main application package
│   ├── config/                   # Configuration management
│   ├── core/                     # Core business logic
│   │   ├── interface/           # Service interfaces
│   │   ├── jobs/                # Background job system
│   │   ├── services/            # Business services
│   │   └── utils/               # Utility functions
│   ├── database/                # Database models and connections
│   ├── integrations/            # External service integrations
│   ├── security/                # Authentication and authorization
│   └── ui/                      # User interface components
├── docs/                        # Documentation
├── infra/                       # Infrastructure and deployment
├── tests/                       # Test suite
├── alembic/                     # Database migrations
├── main.py                      # Application entry point
└── pyproject.toml              # Project configuration
```

### Development Setup

1. **Install development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

2. **Set up pre-commit hooks**

   ```bash
   pre-commit install
   ```

3. **Run in development mode**
   ```bash
   streamlit run main.py --server.runOnSave true
   ```

### Code Style

- **Formatting**: Black
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

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_models.py

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows

### Writing Tests

```python
# Example unit test
import pytest
from app.core.services.report_generator import ReportGenerator

def test_report_generation():
    generator = ReportGenerator()
    report = generator.generate_weekly_report(user_id=1)
    assert report is not None
    assert "tasks_completed" in report
```

## 🚢 Deployment

### Production Deployment

#### Using Docker

1. **Build production image**

   ```bash
   docker build -f infra/Dockerfile -t autoreportsystem:prod .
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

#### Using Docker Compose

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DB_URL=postgresql://user:pass@db:5432/autoreportsystem
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=autoreportsystem
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Cloud Deployment

**AWS ECS/Fargate**

- Use the provided Dockerfile
- Configure RDS for PostgreSQL
- Set up Application Load Balancer
- Configure environment variables in ECS

**Heroku**

```bash
# Install Heroku CLI and login
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

#### Staging

```env
DEBUG=False
LOG_LEVEL=INFO
DB_URL=postgresql://staging-db:5432/autoreportsystem_staging
```

#### Production

```env
DEBUG=False
LOG_LEVEL=WARNING
DB_URL=postgresql://prod-db:5432/autoreportsystem
SENTRY_DSN=https://your-sentry-dsn
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

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

- Verify SMTP server settings
- Check firewall and network connectivity
- Ensure authentication credentials are correct

**Performance Issues**

- Monitor system resources
- Check database query performance
- Review application logs

#### Debug Mode

Enable debug mode for detailed logging:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 🔮 Roadmap

### Version 2.0 (Q2 2024)

- [ ] RESTful API with FastAPI
- [ ] Mobile-responsive design
- [ ] Advanced analytics with ML insights
- [ ] Team collaboration features
- [ ] Real-time notifications

### Version 3.0 (Q4 2024)

- [ ] Microservices architecture
- [ ] Multi-tenant support
- [ ] Advanced workflow automation
- [ ] Integration marketplace
- [ ] Mobile applications

---

<div align="center">

**Built with ❤️ by the AutoReportSystem Team**

[⭐ Star us on GitHub](https://github.com/yourusername/AutoReportSystem) • [🐛 Report Bug](https://github.com/yourusername/AutoReportSystem/issues) • [💡 Request Feature](https://github.com/yourusername/AutoReportSystem/issues)

</div>
