"""
Add a reload capability to the MCP server
This tool allows hot-reloading of specific functions
"""
import importlib
import sys

@self.mcp.tool()
async def reload_server_module() -> str:
    """Reload server modules to pick up code changes"""
    try:
        # Reload the context_server module
        if 'context_server' in sys.modules:
            importlib.reload(sys.modules['context_server'])
            return "✅ Successfully reloaded context_server module"
        else:
            return "❌ context_server module not found in sys.modules"
    except Exception as e:
        return f"❌ Error reloading module: {str(e)}"
