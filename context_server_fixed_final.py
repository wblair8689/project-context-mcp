#!/usr/bin/env python3
"""
Fixed MCP Server - No Print to Stdout
This version ensures no print statements or debug output goes to stdout during MCP operation
"""

import os
import json
import asyncio
import subprocess
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging to go to stderr, not stdout
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Explicitly use stderr to avoid corrupting stdout JSON-RPC
)

# Import all other modules after logging is configured
from conversation_initializer import ConversationInitializer
from build_diagnostics import BuildDiagnosticsDB
from build_monitor import XcodeBuildMonitor
from build_awareness import BuildAwarenessManager
from diagnostics_seeder import seed_known_solutions
from xcode_runtime_monitor import XcodeRuntimeMonitor

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool, TextContent
except ImportError:
    import sys
    sys.stderr.write("MCP not available - install with: pip install mcp\n")
    # Mock for development
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
        def tool(self, **kwargs):
            def decorator(func):
                return func
            return decorator

class UnifiedProjectContextServer:
    """Unified project context and Swift monitoring server"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "project_context_mcp" / "config"
        self.data_path = self.project_root / "project_context_mcp" / "data"
