"""Database health monitoring interface."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database.db_connector import get_db
from app.database.models import Base
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def check_database_connection() -> Dict[str, Any]:
    """Check basic database connectivity."""
    start_time = time.time()
    db = None
    
    try:
        db = await get_db()
        
        # Simple connectivity test
        await db.execute(text("SELECT 1"))
        
        connection_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "status": "healthy",
            "connection_time_ms": round(connection_time, 2),
            "timestamp": datetime.now(),
            "message": "Database connection successful"
        }
        
    except Exception as e:
        connection_time = (time.time() - start_time) * 1000
        logger.error(f"Database connection failed: {e}")
        
        return {
            "status": "unhealthy",
            "connection_time_ms": round(connection_time, 2),
            "timestamp": datetime.now(),
            "message": f"Database connection failed: {str(e)}",
            "error": str(e)
        }
    finally:
        if db:
            await db.close()


async def check_database_tables() -> Dict[str, Any]:
    """Check if all required tables exist and are accessible."""
    db = None
    
    try:
        db = await get_db()
        
        # Get expected tables from models
        expected_tables = set(Base.metadata.tables.keys())
        
        # Get actual tables from database
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """))
        actual_tables = set(row[0] for row in result.fetchall())
        
        missing_tables = expected_tables - actual_tables
        extra_tables = actual_tables - expected_tables - {'alembic_version'}
        
        # Test basic operations on key tables
        table_tests = {}
        key_tables = ['users', 'tasks', 'jobs', 'job_executions']
        
        for table in key_tables:
            if table in actual_tables:
                try:
                    start_time = time.time()
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    query_time = (time.time() - start_time) * 1000
                    
                    table_tests[table] = {
                        "status": "healthy",
                        "record_count": count,
                        "query_time_ms": round(query_time, 2)
                    }
                except Exception as e:
                    table_tests[table] = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                table_tests[table] = {
                    "status": "missing",
                    "error": "Table does not exist"
                }
        
        overall_status = "healthy"
        if missing_tables or any(test["status"] == "error" for test in table_tests.values()):
            overall_status = "unhealthy"
        elif any(test["status"] == "missing" for test in table_tests.values()):
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(),
            "expected_tables": len(expected_tables),
            "actual_tables": len(actual_tables),
            "missing_tables": list(missing_tables),
            "extra_tables": list(extra_tables),
            "table_tests": table_tests
        }
        
    except Exception as e:
        logger.error(f"Database table check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now(),
            "error": str(e)
        }
    finally:
        if db:
            await db.close()


async def check_alembic_migration_status() -> Dict[str, Any]:
    """Check Alembic migration status."""
    db = None
    
    try:
        db = await get_db()
        
        # Check if alembic_version table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            )
        """))
        alembic_table_exists = result.scalar()
        
        if not alembic_table_exists:
            return {
                "status": "not_initialized",
                "timestamp": datetime.now(),
                "message": "Alembic not initialized - no version table found"
            }
        
        # Get current migration version
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        
        # Check if there are any pending migrations by comparing with models
        expected_tables = set(Base.metadata.tables.keys())
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """))
        actual_tables = set(row[0] for row in result.fetchall()) - {'alembic_version'}
        
        missing_tables = expected_tables - actual_tables
        
        if missing_tables:
            migration_status = "pending"
            message = f"Missing tables: {', '.join(missing_tables)}"
        else:
            migration_status = "up_to_date"
            message = "All tables present"
        
        return {
            "status": migration_status,
            "timestamp": datetime.now(),
            "current_version": current_version,
            "message": message,
            "missing_tables": list(missing_tables)
        }
        
    except Exception as e:
        logger.error(f"Alembic status check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now(),
            "error": str(e)
        }
    finally:
        if db:
            await db.close()


async def get_comprehensive_database_health() -> Dict[str, Any]:
    """Get comprehensive database health report."""
    try:
        # Run all health checks concurrently
        connection_check, tables_check, migration_check = await asyncio.gather(
            check_database_connection(),
            check_database_tables(),
            check_alembic_migration_status(),
            return_exceptions=True
        )
        
        # Determine overall health status
        checks = [connection_check, tables_check, migration_check]
        
        if any(isinstance(check, Exception) for check in checks):
            overall_status = "error"
        elif any(check.get("status") in ["unhealthy", "error"] for check in checks if isinstance(check, dict)):
            overall_status = "unhealthy"
        elif any(check.get("status") in ["warning", "pending"] for check in checks if isinstance(check, dict)):
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now(),
            "connection": connection_check if not isinstance(connection_check, Exception) else {"status": "error", "error": str(connection_check)},
            "tables": tables_check if not isinstance(tables_check, Exception) else {"status": "error", "error": str(tables_check)},
            "migrations": migration_check if not isinstance(migration_check, Exception) else {"status": "error", "error": str(migration_check)}
        }
        
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return {
            "overall_status": "error",
            "timestamp": datetime.now(),
            "error": str(e)
        }