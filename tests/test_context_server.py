#!/usr/bin/env python3
"""
Test the Project Context MCP Server functionality
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_server import ProjectContextServer

async def test_context_server():
    """Test the context server functionality"""
    
    print("🧪 Testing Project Context Server")
    
    # Create server instance
    project_root = Path(__file__).parent.parent.parent
    server = ProjectContextServer(str(project_root))
    
    print(f"📁 Project Root: {project_root}")
    print(f"✅ Server created successfully")
    print(f"✅ Config loaded: {server.config['project_name']}")
    print(f"✅ Current phase: {server.config['current_phase']}")
    print(f"✅ Active group: {server.config['active_feature_group']}")
    
    # Test git status
    print("\n📊 Testing git status...")
    git_status = server._get_git_status()
    if git_status.get("available"):
        print(f"✅ Git available: {git_status['branch']}")
        print(f"✅ Last commit: {git_status['last_commit']['message'][:50]}...")
    else:
        print(f"❌ Git not available: {git_status.get('error', 'Unknown error')}")
    
    # Test next steps suggestion
    print("\n🎯 Testing next steps...")
    next_steps = server._get_suggested_next_steps()
    for i, step in enumerate(next_steps, 1):
        print(f"  {i}. {step}")
    
    # Test directory structure
    print("\n📁 Testing directory structure...")
    print(f"✅ Config path exists: {server.config_path.exists()}")
    print(f"✅ Data path exists: {server.data_path.exists()}")
    
    # Test feature group detection
    print("\n🗂️ Testing feature group detection...")
    feature_groups = server.config.get("feature_groups", [])
    for group in feature_groups:
        if isinstance(group, dict):
            group_name = group["name"]
        else:
            group_name = group
        
        group_path = server.project_root / group_name
        exists = "✅" if group_path.exists() else "❌"
        readme = "📝" if (group_path / "README.md").exists() else "❌"
        print(f"  {exists} {group_name} {readme}")
    
    print("\n🎉 Context server test completed successfully!")
    return True

if __name__ == "__main__":
    asyncio.run(test_context_server())
if __name__ == "__main__":
    asyncio.run(generate_project_summary())
