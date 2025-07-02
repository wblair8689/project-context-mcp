#!/usr/bin/env python3
"""
Quick test of the MCP server
"""

import sys
from pathlib import Path

# Add the project context path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from context_server import UnifiedProjectContextServer
    
    print("🧪 Testing MCP Server Components")
    print("=" * 40)
    
    # Create server instance
    project_root = "/Users/williamblair/AI-Game-Evolution-Platform"
    server = UnifiedProjectContextServer(project_root)
    
    print(f"✅ Server created successfully")
    print(f"📁 Project root: {project_root}")
    
    # Test basic attributes
    print(f"✅ Config path: {server.config_path}")
    print(f"✅ Data path: {server.data_path}")
    print(f"✅ Swift project path: {server.swift_project_path}")
    
    # Test if components are available
    if hasattr(server, '_get_git_status'):
        git_status = server._get_git_status()
        print(f"✅ Git status available: {git_status.get('available', False)}")
    
    print(f"\n🎉 MCP Server initialized successfully!")
    print(f"📡 Ready to accept MCP protocol connections")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
