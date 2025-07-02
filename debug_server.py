#!/usr/bin/env python3
"""
Debug MCP Server - outputs diagnostics to stderr for troubleshooting
"""

import sys
import os
import logging
import traceback

# Configure verbose logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=== MCP SERVER DEBUG START ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    try:
        logger.info("Testing imports...")
        
        # Test FastMCP import
        try:
            from mcp.server.fastmcp import FastMCP
            logger.info("✅ FastMCP imported successfully")
        except Exception as e:
            logger.error(f"❌ FastMCP import failed: {e}")
            
        # Test main server import
        try:
            from context_server import UnifiedProjectContextServer
            logger.info("✅ UnifiedProjectContextServer imported successfully")
        except Exception as e:
            logger.error(f"❌ UnifiedProjectContextServer import failed: {e}")
            traceback.print_exc()
            return
        
        # Test server creation
        try:
            project_root = "/Users/williamblair/AI-Game-Evolution-Platform"
            server = UnifiedProjectContextServer(project_root)
            logger.info("✅ Server instance created successfully")
        except Exception as e:
            logger.error(f"❌ Server creation failed: {e}")
            traceback.print_exc()
            return
            
        # Test MCP server creation
        try:
            from context_server import create_mcp_server
            mcp = create_mcp_server(project_root)
            logger.info("✅ MCP server created successfully")
        except Exception as e:
            logger.error(f"❌ MCP server creation failed: {e}")
            traceback.print_exc()
            return
        
        logger.info("=== ALL TESTS PASSED ===")
        logger.info("Starting actual MCP server...")
        
        # Run the server
        mcp.run()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
