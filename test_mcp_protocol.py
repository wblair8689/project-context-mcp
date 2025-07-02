#!/usr/bin/env python3
"""
Simple test to verify MCP server responds to protocol calls
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_protocol():
    """Test MCP server via protocol calls"""
    
    print("🧪 Testing MCP Server via Protocol")
    print("=" * 50)
    
    # Start the MCP server in stdio mode
    print("🚀 Starting MCP server in stdio mode...")
    
    server_path = Path(__file__).parent / "context_server.py"
    project_root = "/Users/williamblair/AI-Game-Evolution-Platform"
    
    # Start server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, str(server_path),
        "--project-root", project_root,
        "--transport", "stdio",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Send a simple ping to test if server is responding
        print("📡 Testing server communication...")
        
        # MCP initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send request
        request_str = json.dumps(init_request) + "\n"
        process.stdin.write(request_str.encode())
        await process.stdin.drain()
        
        # Read response with timeout
        try:
            response = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
            response_data = json.loads(response.decode())
            
            if "result" in response_data:
                print("✅ MCP server responded successfully!")
                print(f"✅ Server capabilities: {response_data['result'].get('capabilities', {})}")
            else:
                print(f"⚠️ Unexpected response: {response_data}")
                
        except asyncio.TimeoutError:
            print("⚠️ Server didn't respond within timeout")
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON response from server")
        
        # Test listing tools
        print("\n📋 Testing tool listing...")
        tools_request = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list"
        }
        
        request_str = json.dumps(tools_request) + "\n"
        process.stdin.write(request_str.encode())
        await process.stdin.drain()
        
        try:
            response = await asyncio.wait_for(process.stdout.readline(), timeout=3.0)
            response_data = json.loads(response.decode())
            
            if "result" in response_data and "tools" in response_data["result"]:
                tools = response_data["result"]["tools"]
                print(f"✅ Found {len(tools)} MCP tools:")
                for tool in tools[:5]:  # Show first 5 tools
                    print(f"  📋 {tool['name']}: {tool.get('description', 'No description')}")
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more tools")
            else:
                print(f"⚠️ No tools found in response: {response_data}")
                
        except asyncio.TimeoutError:
            print("⚠️ Tools list request timed out")
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON response for tools list")
        
    finally:
        # Clean shutdown
        print("\n🛑 Shutting down server...")
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3.0)
            print("✅ Server shut down cleanly")
        except asyncio.TimeoutError:
            print("⚠️ Server shutdown timeout, killing process")
            process.kill()
    
    print("\n🎉 MCP Protocol Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_mcp_protocol())
