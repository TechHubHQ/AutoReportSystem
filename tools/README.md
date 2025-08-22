# AutoReportSystem Tools

This directory contains various tools for managing and maintaining the AutoReportSystem.

## Directory Structure

```
tools/
├── database/           # Database management tools
│   ├── sync_alembic_migrations.py    # Comprehensive migration sync
│   ├── quick_alembic_sync.py         # Quick migration operations
│   └── run_sync_check.py             # Migration status checker
├── system/             # System management tools (future)
└── README.md           # This file
```

## Database Tools

### sync_alembic_migrations.py
**Purpose**: Comprehensive tool to sync Alembic migrations with current database state.

**Features**:
- Checks current database state
- Compares with model definitions
- Verifies specific schema elements
- Provides interactive sync options

**Usage**:
```bash
python tools/database/sync_alembic_migrations.py
```

### quick_alembic_sync.py
**Purpose**: Quick options to sync Alembic with current database state.

**Features**:
- Check current migration status
- Generate migration from current state
- Stamp database as current head
- Show migration history
- Upgrade to head

**Usage**:
```bash
python tools/database/quick_alembic_sync.py
```

### run_sync_check.py
**Purpose**: Check and sync models with database after manual fixes.

**Features**:
- Checks if models match database state
- Generates migration if needed
- Stamps database if everything is in sync

**Usage**:
```bash
python tools/database/run_sync_check.py
```

## UI Integration

All tools are integrated into the System Monitor page in the web interface:

1. Navigate to **System Monitor** in the sidebar
2. Go to the **Database Health** tab
3. Use the **Database Management Tools** section
4. Or use the **Tools Management** tab for detailed tool information

## Safety Notes

- **Always backup your database** before running migration tools
- **Test in development** before running in production
- **Review generated migrations** before applying them
- Tools have different risk levels:
  - 🟢 **Low Risk**: Status checks, read-only operations
  - 🟠 **Medium Risk**: Migration generation, schema changes
  - 🔴 **High Risk**: Data modification, destructive operations

## Adding New Tools

To add a new tool:

1. Create the tool script in the appropriate directory
2. Update `app/core/interface/tools_interface.py` to include the new tool
3. Add appropriate risk level and category
4. Test thoroughly before deployment

## Command Line Usage

All tools can be run directly from the command line:

```bash
# From project root
python tools/database/tool_name.py

# Or with specific Python interpreter
python3 tools/database/tool_name.py
```

## Environment Requirements

Tools require the same environment as the main application:
- Python 3.12+
- All project dependencies installed
- Proper database configuration
- Access to alembic configuration files