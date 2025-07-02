#!/usr/bin/env python3
"""
Comprehensive MCP Server Diagnostic
"""

import sys
import traceback

def test_all_imports():
    """Test all module imports"""
    
    print("🔍 Testing all module imports...")
    
    try:
        # Test main server
        import context_server
        print("  ✅ context_server")
        
        # Test tools
        from tools import build_tools
        print("  ✅ tools.build_tools")
        
        from tools import project_status
        print("  ✅ tools.project_status")
        
        from tools import context_tools
        print("  ✅ tools.context_tools")
        
        from tools import swift_tools
        print("  ✅ tools.swift_tools")
        
        # Test other components
        import conversation_initializer
        print("  ✅ conversation_initializer")
        
        import build_diagnostics
        print("  ✅ build_diagnostics")
        
        import diagnostics_seeder
        print("  ✅ diagnostics_seeder")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_server_creation():
    """Test server creation"""
    
    print("\n🏗️ Testing server creation...")
    
    try:
        from context_server import UnifiedProjectContextServer
        server = UnifiedProjectContextServer("/Users/williamblair/AI-Game-Evolution-Platform")
        print("  ✅ Server instance created")
        return True
        
    except Exception as e:
        print(f"  ❌ Server creation failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Comprehensive MCP Server Diagnostic")
    print("=" * 50)
    
    imports_ok = test_all_imports()
    server_ok = test_server_creation()
    
    if imports_ok and server_ok:
        print("\n🎉 All tests passed!")
        print("✅ MCP Server should work with Claude Desktop")
    else:
        print("\n❌ Issues detected!")
        print("🔧 Check error messages above")
