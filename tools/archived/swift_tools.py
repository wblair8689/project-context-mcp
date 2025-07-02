"""
Swift-specific MCP tools
"""
import json
from typing import Any


def register_tools(server):
    """Register Swift-related tools with the server"""
    
    @server.mcp.tool()
    async def get_swift_project_details() -> str:
        """Get detailed Swift project information"""
        try:
            # Get Swift project status
            swift_status = server.swift_checker.get_swift_project_status()
            
            # Get additional details
            details = {
                "xcode_projects": swift_status.get("xcode_projects", []),
                "swift_files": {
                    "count": swift_status.get("swift_files_count", 0),
                    "locations": []
                },
                "build_configuration": {
                    "server_status": swift_status.get("build_server_status", "Unknown"),
                    "last_build": swift_status.get("last_build", "Unknown")
                },
                "ios_template": swift_status.get("ios_template_ready", "Unknown"),
                "automation": {
                    "xcode_monitor": "✅ Active" if server.runtime_monitor else "❌ Not running",
                    "build_monitor": "✅ Active" if hasattr(server, 'build_monitor') else "❌ Not configured"
                }
            }
            
            # Add file location breakdown if we have files
            if swift_status.get("swift_files_count", 0) > 0:
                swift_files = server.swift_checker.find_swift_files()
                # Group by directory
                file_groups = {}
                for file_path in swift_files[:20]:  # Limit to first 20 for brevity
                    dir_name = file_path.split('/')[-2] if '/' in file_path else "root"
                    if dir_name not in file_groups:
                        file_groups[dir_name] = 0
                    file_groups[dir_name] += 1
                
                details["swift_files"]["locations"] = [
                    f"{dir_name}: {count} files" 
                    for dir_name, count in sorted(file_groups.items(), key=lambda x: x[1], reverse=True)
                ]
            
            return json.dumps(details, indent=2)
            
        except Exception as e:
            return f"Error getting Swift project details: {str(e)}"