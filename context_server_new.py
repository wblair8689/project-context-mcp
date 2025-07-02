"""
Backwards compatibility wrapper for the refactored Project Context MCP Server

This file maintains the original interface while using the new modular structure.
"""
from server.main import main

# For direct imports
from server.base import UnifiedProjectContextServer

if __name__ == "__main__":
    main()
