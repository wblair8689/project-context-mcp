"""
Build diagnostics and monitoring MCP tools
"""
import json
from typing import Any
from datetime import datetime, timedelta


def register_tools(server):
    """Register build-related tools with the server"""
    
    @server.mcp.tool()
    async def get_build_diagnostics() -> str:
        """Get recent build diagnostics including errors, warnings, and solutions"""
        try:
            # Get recent diagnostics from the database
            recent_diagnostics = server.diagnostics_db.get_recent_diagnostics(hours=24)
            
            if not recent_diagnostics:
                return json.dumps({
                    "status": "No recent build diagnostics",
                    "suggestion": "Run a build to generate diagnostics"
                }, indent=2)
            
            # Group diagnostics by type
            errors = [d for d in recent_diagnostics if d['severity'] == 'error']
            warnings = [d for d in recent_diagnostics if d['severity'] == 'warning']
            
            # Get solutions for errors
            errors_with_solutions = []
            for error in errors[:5]:  # Limit to 5 most recent
                solutions = server.diagnostics_db.get_solutions_for_error(error['message'])
                errors_with_solutions.append({
                    "message": error['message'],
                    "file": error.get('file_path', 'Unknown'),
                    "line": error.get('line_number', 'Unknown'),
                    "timestamp": error['timestamp'],
                    "solutions": solutions
                })
            
            result = {
                "summary": {
                    "total_errors": len(errors),
                    "total_warnings": len(warnings),
                    "time_range": "Last 24 hours"
                },
                "recent_errors": errors_with_solutions,
                "top_warnings": warnings[:3]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error getting build diagnostics: {str(e)}"
    @server.mcp.tool()
    async def get_error_solution(error_message: str) -> str:
        """Get solution for a specific build error message"""
        try:
            # Get solutions from database
            solutions = server.diagnostics_db.get_solutions_for_error(error_message)
            
            if not solutions:
                # Try to categorize the error and provide general solutions
                error_lower = error_message.lower()
                if "module" in error_lower or "import" in error_lower:
                    category_solutions = server._get_general_solutions("module")
                elif "syntax" in error_lower:
                    category_solutions = server._get_general_solutions("syntax")
                elif "type" in error_lower:
                    category_solutions = server._get_general_solutions("type")
                else:
                    category_solutions = ["No specific solution found. Check error details."]
                
                return json.dumps({
                    "error": error_message,
                    "solutions": category_solutions,
                    "type": "general"
                }, indent=2)
            
            return json.dumps({
                "error": error_message,
                "solutions": solutions,
                "type": "specific"
            }, indent=2)
            
        except Exception as e:
            return f"Error getting error solution: {str(e)}"
    
    @server.mcp.tool()
    async def record_successful_fix(error_message: str, solution_description: str, fix_pattern: str = None) -> str:
        """Record that an error was successfully fixed with a specific solution"""
        try:
            # Record the fix in the database
            server.diagnostics_db.record_fix(
                error_message=error_message,
                solution=solution_description,
                fix_pattern=fix_pattern
            )
            
            return f"✅ Successfully recorded fix for error: {error_message[:50]}..."
            
        except Exception as e:
            return f"Error recording fix: {str(e)}"
    
    @server.mcp.tool()
    async def get_build_health_summary() -> str:
        """Get a quick summary of build health and recent activity"""
        try:
            # Get recent diagnostics
            recent = server.diagnostics_db.get_recent_diagnostics(hours=1)
            last_24h = server.diagnostics_db.get_recent_diagnostics(hours=24)
            
            # Calculate trends
            errors_1h = len([d for d in recent if d['severity'] == 'error'])
            errors_24h = len([d for d in last_24h if d['severity'] == 'error'])
            
            health_status = "🟢 Healthy" if errors_1h == 0 else "🔴 Issues detected"
            
            summary = {
                "status": health_status,
                "last_hour": {
                    "errors": errors_1h,
                    "warnings": len([d for d in recent if d['severity'] == 'warning'])
                },
                "last_24_hours": {
                    "errors": errors_24h,
                    "warnings": len([d for d in last_24h if d['severity'] == 'warning'])
                },
                "trend": "Improving" if errors_1h < errors_24h / 24 else "Stable"
            }
            
            return json.dumps(summary, indent=2)
            
        except Exception as e:
            return f"Error getting build health summary: {str(e)}"

    @server.mcp.tool()
    async def get_enhanced_build_status() -> str:
        """Get enhanced build status with diagnostics insights and solution suggestions"""
        try:
            status = server.build_awareness.get_enhanced_status()
            return json.dumps(status, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get enhanced build status: {str(e)}"}, indent=2)
    
    @server.mcp.tool()
    async def record_build_fix(error_message: str, solution_applied: str) -> str:
        """Record that a build error was successfully fixed with a specific solution"""
        try:
            success = server.build_awareness.record_successful_fix(error_message, solution_applied)
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Recorded successful fix for: {error_message[:50]}..."
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Failed to record fix"
                }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to record build fix: {str(e)}"}, indent=2)
    
    @server.mcp.tool()
    async def get_build_error_solution(error_message: str) -> str:
        """Get solution suggestions for a specific build error message"""
        try:
            solutions = server.build_awareness.get_solution_for_error(error_message)
            return json.dumps({
                "error": error_message,
                "solutions": solutions if solutions else ["No specific solutions found"],
                "suggestion": "Try the solutions in order, starting with the most commonly successful ones"
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get error solutions: {str(e)}"}, indent=2)