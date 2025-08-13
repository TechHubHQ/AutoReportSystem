# Installation Guide

## Prerequisites

Before installing AutoReportSystem, ensure you have the following prerequisites:

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.12 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free disk space
- **Network**: Internet connection for package installation

### Required Software
- **Python 3.12+**: [Download from python.org](https://python.org/downloads/)
- **PostgreSQL 13+**: [Download from postgresql.org](https://postgresql.org/download/)
- **Git**: [Download from git-scm.com](https://git-scm.com/downloads)

### Optional Tools
- **Docker**: For containerized deployment
- **uv**: Fast Python package manager (recommended)

## Installation Methods

### Method 1: Standard Installation

#### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/AutoReportSystem.git
cd AutoReportSystem
```

#### Step 2: Create Virtual Environment
```bash
# Using venv
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
# Using pip
pip install -r requirements.txt

# OR using uv (recommended for faster installation)
pip install uv
uv sync
```

#### Step 4: Database Setup
```bash
# Create PostgreSQL database
createdb autoreportsystem

# Run database migrations
alembic upgrade head
```

#### Step 5: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

#### Step 6: Run Application
```bash
streamlit run main.py
```

### Method 2: Docker Installation

#### Prerequisites
- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

#### Quick Start with Docker
```bash
# Clone repository
git clone https://github.com/yourusername/AutoReportSystem.git
cd AutoReportSystem

# Build and run with Docker Compose
docker-compose up -d

# Access application at http://localhost:8501
```

#### Manual Docker Build
```bash
# Build Docker image
docker build -t autoreportsystem .

# Run container
docker run -d \
  --name autoreportsystem \
  -p 8501:8501 \
  -e DB_URL=postgresql://user:pass@host:5432/db \
  autoreportsystem
```

### Method 3: Development Installation

For contributors and developers:

#### Step 1: Fork and Clone
```bash
# Fork the repository on GitHub first
git clone https://github.com/yourusername/AutoReportSystem.git
cd AutoReportSystem

# Add upstream remote
git remote add upstream https://github.com/originalowner/AutoReportSystem.git
```

#### Step 2: Development Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

#### Step 3: Development Database
```bash
# Create development database
createdb autoreportsystem_dev

# Set development environment
export DB_URL=postgresql://localhost:5432/autoreportsystem_dev

# Run migrations
alembic upgrade head
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_URL=postgresql+asyncpg://username:password@localhost:5432/autoreportsystem

# SMTP Configuration (for email features)
SMTP_ENV_KEY=your_encryption_key_here

# Application Settings
DEBUG=False
LOG_LEVEL=INFO

# Security Settings
SECRET_KEY=your_secret_key_here
SESSION_TIMEOUT=3600

# Optional: External Service Keys
SENTRY_DSN=https://your-sentry-dsn-here
```

### Database Configuration

#### PostgreSQL Setup
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database and user
CREATE DATABASE autoreportsystem;
CREATE USER ars_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE autoreportsystem TO ars_user;

-- Exit PostgreSQL
\q
```

#### Connection String Format
```
postgresql+asyncpg://username:password@host:port/database_name
```

Examples:
- Local: `postgresql+asyncpg://ars_user:password@localhost:5432/autoreportsystem`
- Remote: `postgresql+asyncpg://user:pass@db.example.com:5432/autoreportsystem`

### SMTP Configuration

For email functionality, configure SMTP settings:

1. **Gmail Example**:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

2. **Outlook Example**:
   ```env
   SMTP_HOST=smtp-mail.outlook.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@outlook.com
   SMTP_PASSWORD=your-password
   ```

3. **Custom SMTP**:
   ```env
   SMTP_HOST=mail.yourcompany.com
   SMTP_PORT=587
   SMTP_USERNAME=your-username
   SMTP_PASSWORD=your-password
   ```

## Verification

### Test Installation
```bash
# Check Python version
python --version

# Check if all packages are installed
pip list

# Test database connection
python -c "from app.database.db_connector import test_connection; test_connection()"

# Run application
streamlit run main.py
```

### Access Application
1. Open your web browser
2. Navigate to `http://localhost:8501`
3. You should see the AutoReportSystem home page
4. Create an account or sign in

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

## Troubleshooting

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If using multiple Python versions
python3.12 -m venv .venv
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
pg_isready -h localhost -p 5432

# Check if database exists
psql -U postgres -l | grep autoreportsystem

# Test connection string
python -c "import asyncpg; print('Connection test passed')"
```

#### Package Installation Issues
```bash
# Clear pip cache
pip cache purge

# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v -r requirements.txt
```

#### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501  # On macOS/Linux
netstat -ano | findstr :8501  # On Windows

# Kill process if needed
kill -9 <PID>  # On macOS/Linux
taskkill /PID <PID> /F  # On Windows

# Run on different port
streamlit run main.py --server.port 8502
```

#### Permission Issues
```bash
# On macOS/Linux, ensure proper permissions
chmod +x scripts/*.sh

# On Windows, run as administrator if needed
```

### Getting Help

If you encounter issues:

1. **Check the logs**: Look in the `logs/` directory for error messages
2. **Enable debug mode**: Set `DEBUG=True` in your `.env` file
3. **Check dependencies**: Ensure all required packages are installed
4. **Database connectivity**: Verify PostgreSQL is running and accessible
5. **Environment variables**: Double-check your `.env` configuration

### Support Channels

- **GitHub Issues**: [Report bugs and issues](https://github.com/yourusername/AutoReportSystem/issues)
- **Documentation**: Check the `docs/` directory for detailed guides
- **Community**: Join our discussions for help and tips

## Next Steps

After successful installation:

1. **Create your first user account**
2. **Configure SMTP settings** for email functionality
3. **Explore the dashboard** and create your first task
4. **Set up your first automated job**
5. **Design custom email templates**

Congratulations! You've successfully installed AutoReportSystem. 🎉