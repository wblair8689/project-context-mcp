#!/usr/bin/env python3
"""
Test MCP Server Startup
"""

import sys
import subprocess
import time

def test_mcp_server():
    """Test if MCP server starts without errors"""
    
    print("🧪 Testing MCP Server Startup...")
    
    try:
        # Test import
        print("  ✅ Testing import...")
        result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.insert(0, '.'); import context_server; print('Import successful')"
        ], capture_output=True, text=True, timeout=10, cwd="/Users/williamblair/AI-Game-Evolution-Platform/project_context_mcp")
        
        if result.returncode != 0:
            print(f"  ❌ Import failed: {result.stderr}")
            return False
        
        print(f"  ✅ Import test passed: {result.stdout.strip()}")
        
        # Test server startup (briefly)
        print("  ✅ Testing server startup...")
        proc = subprocess.Popen([
            sys.executable, "context_server.py", "--debug"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd="/Users/williamblair/AI-Game-Evolution-Platform/project_context_mcp")
        
        # Give it 3 seconds to start and check for errors
        time.sleep(3)
        
        if proc.poll() is not None:
            # Process exited
            stdout, stderr = proc.communicate()
            print(f"  ❌ Server exited early:")
            print(f"     stdout: {stdout[:200]}...")
            print(f"     stderr: {stderr[:200]}...")
            return False
        
        # Server is still running, kill it
        proc.terminate()
        proc.wait(timeout=5)
        
        print("  ✅ Server startup test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    if success:
        print("\n🎉 MCP Server is ready!")
        print("✅ No startup errors detected")
        print("✅ Ready for Claude Desktop connection")
    else:
        print("\n❌ MCP Server has issues")
        print("🔧 Check the error messages above")
