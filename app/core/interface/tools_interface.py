"""Interface for managing database and system tools."""

import subprocess
import sys
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class ToolsManager:
    """Manager for database and system tools."""
    
    def __init__(self):
        self.tools_dir = Path(__file__).parent.parent.parent.parent / "tools"
        self.database_tools_dir = self.tools_dir / "database"
        self.system_tools_dir = self.tools_dir / "system"
    
    def get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get list of available tools organized by category."""
        tools = {
            "database": [],
            "system": []
        }
        
        # Database tools
        database_tools = [
            {
                "id": "sync_migrations",
                "name": "Sync Alembic Migrations",
                "description": "Comprehensive tool to sync Alembic migrations with current database state",
                "file": "sync_alembic_migrations.py",
                "category": "migration",
                "risk_level": "medium"
            },
            {
                "id": "quick_sync",
                "name": "Quick Migration Sync",
                "description": "Quick options to sync Alembic with current database state",
                "file": "quick_alembic_sync.py",
                "category": "migration",
                "risk_level": "low"
            },
            {
                "id": "run_sync_check",
                "name": "Migration Sync Check",
                "description": "Check and sync models with database after manual fixes",
                "file": "run_sync_check.py",
                "category": "migration",
                "risk_level": "low"
            }
        ]
        
        # Verify tools exist and add to list
        for tool in database_tools:
            tool_path = self.database_tools_dir / tool["file"]
            if tool_path.exists():
                tool["available"] = True
                tool["path"] = str(tool_path)
                tools["database"].append(tool)
            else:
                tool["available"] = False
                tool["path"] = str(tool_path)
                tool["error"] = "Tool file not found"
                tools["database"].append(tool)
        
        return tools
    
    def run_tool(self, tool_id: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a specific tool and return the result."""
        tools = self.get_available_tools()
        
        # Find the tool
        tool = None
        for category in tools.values():
            for t in category:
                if t["id"] == tool_id:
                    tool = t
                    break
            if tool:
                break
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_id}' not found"
            }
        
        if not tool["available"]:
            return {
                "success": False,
                "error": f"Tool '{tool_id}' is not available: {tool.get('error', 'Unknown error')}"
            }
        
        try:
            # Prepare command
            cmd = [sys.executable, tool["path"]]
            if args:
                cmd.extend(args)
            
            # Run the tool
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.tools_dir.parent)  # Run from project root
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tool execution timed out (5 minutes)",
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Error running tool {tool_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        tools = self.get_available_tools()
        
        for category in tools.values():
            for tool in category:
                if tool["id"] == tool_id:
                    return tool
        
        return None
    
    def run_alembic_command(self, command: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run an Alembic command directly."""
        try:
            cmd = [sys.executable, "-m", "alembic", command]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for alembic commands
                cwd=str(self.tools_dir.parent)  # Run from project root
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Alembic command timed out (2 minutes)",
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Error running alembic command {command}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
tools_manager = ToolsManager()