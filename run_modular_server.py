#!/usr/bin/env python3
"""
Main entry point for Project Context MCP Server
This file should be run directly, not as a module
"""
import sys
import os

# Add the parent directory to the Python path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can import from the server package
from server.main import main

if __name__ == "__main__":
    main()
