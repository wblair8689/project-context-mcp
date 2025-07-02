"""
Simplified 4-command MCP tools for Xcode integration + Project Management
"""
import json
import subprocess
import time
from typing import Any, Dict, List
from datetime import datetime

# Import necessary functions from xcode monitor
try:
    from macos_automator import execute_script
except ImportError:
    execute_script = None


def register_tools(server):
    """Register the essential tools with the server"""
    
    @server.mcp.tool()
    async def list_projects() -> str:
        """List all registered projects and show current project selection"""
        try:
            if not hasattr(server, 'project_registry'):
                return json.dumps({
                    "error": "Project registry not initialized",
                    "suggestion": "Server needs to be restarted with project registry support"
                }, indent=2)
            
            projects = server.project_registry.list_projects()
            current = server.project_registry.get_current_project()
            
            if not projects:
                # Auto-discover some projects
                discovered = server.project_registry.auto_discover_projects()
                
                return json.dumps({
                    "status": "no_projects_registered",
                    "message": "No projects registered yet",
                    "current_project": None,
                    "discovered_projects": discovered[:5],  # Show first 5
                    "actions": [
                        "Use add_project() to register a project",
                        "Use select_project() to choose from discovered projects",
                        "Use auto_register_projects() to register discovered projects"
                    ]
                }, indent=2)
            
            return json.dumps({
                "status": "success",
                "current_project": current,
                "registered_projects": projects,
                "total_projects": len(projects),
                "actions": [
                    "Use select_project(name) to switch projects",
                    "Use add_project() to register new projects",
                    "Use remove_project(name) to remove projects"
                ]
            }, indent=2)
            
        except Exception as e:
            return f"Error listing projects: {str(e)}"
    
    @server.mcp.tool()
    async def select_project(project_name: str) -> str:
        """Select and switch to a specific project"""
        try:
            if not hasattr(server, 'project_registry'):
                return json.dumps({
                    "error": "Project registry not initialized"
                }, indent=2)
            
            # Check if project exists
            project = server.project_registry.get_project(project_name)
            if not project:
                available = [p["name"] for p in server.project_registry.list_projects()]
                return json.dumps({
                    "status": "error",
                    "message": f"Project '{project_name}' not found",
                    "available_projects": available,
                    "suggestion": "Use list_projects() to see available projects"
                }, indent=2)
            
            # Set as current project
            success = server.project_registry.set_current_project(project_name)
            
            if success:
                # Update server's project root
                server.project_root = project["path"]
                # Reinitialize checkers for new project
                server._reinitialize_for_project(project["path"])
                
                return json.dumps({
                    "status": "success",
                    "message": f"Switched to project: {project_name}",
                    "project_path": project["path"],
                    "xcode_enabled": project.get("xcode_enabled", True),
                    "next_action": "Use get_project_status() to check project health"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Failed to switch project"
                }, indent=2)
            
        except Exception as e:
            return f"Error selecting project: {str(e)}"
    
    @server.mcp.tool()
    async def add_project(name: str, path: str, description: str = "", 
                         project_type: str = "general", xcode_enabled: bool = True) -> str:
        """Add a new project to the registry"""
        try:
            if not hasattr(server, 'project_registry'):
                return json.dumps({
                    "error": "Project registry not initialized"
                }, indent=2)
            
            success = server.project_registry.add_project(
                name=name,
                path=path,
                description=description,
                project_type=project_type,
                xcode_enabled=xcode_enabled
            )
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Project '{name}' added successfully",
                    "project": {
                        "name": name,
                        "path": path,
                        "description": description,
                        "project_type": project_type,
                        "xcode_enabled": xcode_enabled
                    },
                    "next_action": f"Use select_project('{name}') to switch to this project"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to add project '{name}' - path may not exist"
                }, indent=2)
            
        except Exception as e:
            return f"Error adding project: {str(e)}"
    
    @server.mcp.tool()
    async def get_project_status() -> str:
        """Get unified project status: build state, errors/warnings, project health, and blockers"""
        try:
            # Check if we have project registry and current project
            if hasattr(server, 'project_registry'):
                current = server.project_registry.get_current_project()
                if not current:
                    projects = server.project_registry.list_projects()
                    if not projects:
                        return json.dumps({
                            "status": "no_project_selected",
                            "message": "No project selected and no projects registered",
                            "action_needed": "Use list_projects() to see available projects or add_project() to register one"
                        }, indent=2)
                    else:
                        return json.dumps({
                            "status": "no_project_selected", 
                            "message": "No project currently selected",
                            "available_projects": [p["name"] for p in projects[:5]],
                            "action_needed": "Use select_project(name) to choose a project"
                        }, indent=2)
            
            # Get comprehensive status from all checkers
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            implementation = server.swift_checker.get_swift_project_status() if server.swift_checker else {
                "status": "disabled", 
                "swift_files_count": 0,
                "xcode_projects": [],
                "build_server_status": "Disabled"
            }
            git_status = server.git_checker.get_git_status()
            
            # Get recent build diagnostics (only if Xcode enabled)
            if server.xcode_enabled and server.diagnostics_db:
                recent_diagnostics = server.diagnostics_db.get_recent_diagnostics(hours=1)
                errors = [d for d in recent_diagnostics if d['severity'] == 'error']
                warnings = [d for d in recent_diagnostics if d['severity'] == 'warning']
            else:
                recent_diagnostics = []
                errors = []
                warnings = []
            
            # Calculate readiness
            overall_readiness = server._calculate_overall_readiness(infrastructure, implementation)
            
            # Identify blockers
            blockers = []
            if errors:
                blockers.append(f"{len(errors)} build errors")
            if "❌" in implementation.get("build_server_status", ""):
                blockers.append("Build server not configured")
            
            # Add infrastructure blockers
            for component, status in infrastructure.items():
                if "❌" in status:
                    blockers.append(f"{component.replace('_', ' ')} not ready")
            
            # Get current project info if available
            current_project_info = {}
            if hasattr(server, 'project_registry'):
                current = server.project_registry.get_current_project()
                if current:
                    current_project_info = {
                        "selected_project": current["name"],
                        "project_path": current["path"],
                        "selected_at": current.get("set_at")
                    }
            
            status = {
                "project_name": server.config.get("project_name", "Unknown Project"),
                "current_phase": server.config.get("current_phase", "Development"),
                "overall_readiness": overall_readiness,
                **current_project_info,
                "build_health": {
                    "status": "🟢 Healthy" if len(errors) == 0 else "🔴 Issues detected",
                    "errors": len(errors),
                    "warnings": len(warnings),
                    "last_check": datetime.now().isoformat()
                },
                "blockers": blockers[:5],  # Top 5 blockers
                "swift_files": implementation.get("swift_files_count", 0),
                "xcode_projects": len(implementation.get("xcode_projects", [])),
                "git_status": {
                    "branch": git_status.get("branch", "unknown"),
                    "clean": not git_status.get("is_dirty", True),
                    "last_commit": git_status.get("last_commit", {}).get("message", "Unknown")[:50]
                },
                "next_action": "Fix build errors" if errors else "Run build to verify status"
            }
            
            return json.dumps(status, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to get project status: {str(e)}"}, indent=2)
    
    @server.mcp.tool()
    async def build() -> str:
        """Trigger Xcode build and return immediate feedback with build results"""
        try:
            # First check if Xcode is running and has a project open
            xcode_status_script = '''
            tell application "System Events"
                if not (exists process "Xcode") then
                    return "Xcode not running"
                end if
            end tell
            
            tell application "Xcode"
                if (count of windows) = 0 then
                    return "No Xcode project open"
                end if
                return "ready"
            end tell
            '''
            
            if execute_script:
                result = execute_script(script_content=xcode_status_script, language='applescript')
                if "not running" in result.get('output', '') or "No Xcode project" in result.get('output', ''):
                    return json.dumps({
                        "status": "error",
                        "message": "Xcode not running or no project open",
                        "suggestion": "Open your Xcode project first"
                    }, indent=2)
            
            # Trigger build via AppleScript
            build_script = '''
            tell application "Xcode"
                activate
                
                -- Trigger build
                tell application "System Events"
                    keystroke "b" using {command down}
                end tell
                
                return "Build triggered"
            end tell
            '''
            
            # Start the build
            build_start_time = time.time()
            if execute_script:
                result = execute_script(script_content=build_script, language='applescript')
                if result.get('exit_code', 0) != 0:
                    return json.dumps({
                        "status": "error", 
                        "message": f"Failed to trigger build: {result.get('output', 'Unknown error')}"
                    }, indent=2)
            
            # Wait a moment for build to start
            time.sleep(2)
            
            # Monitor for a few seconds to get initial feedback (only if Xcode enabled)
            if server.xcode_enabled and server.diagnostics_db:
                for i in range(10):  # Check for 10 seconds
                    time.sleep(1)
                    
                    # Get recent diagnostics
                    recent_diagnostics = server.diagnostics_db.get_recent_diagnostics(hours=0.1)  # Last 6 minutes
                    new_errors = [d for d in recent_diagnostics if d['severity'] == 'error']
                    new_warnings = [d for d in recent_diagnostics if d['severity'] == 'warning']
                    
                    # If we have new diagnostics, return them
                    if new_errors or new_warnings:
                        build_time = time.time() - build_start_time
                        return json.dumps({
                            "status": "completed" if not new_errors else "failed",
                            "build_time": f"{build_time:.1f}s",
                            "errors": len(new_errors),
                            "warnings": len(new_warnings),
                            "message": f"Build {'succeeded' if not new_errors else 'failed'} with {len(new_errors)} errors, {len(new_warnings)} warnings",
                            "top_errors": [e['message'][:100] for e in new_errors[:3]],
                            "suggestion": "Use get_diagnostics() to see detailed error information" if new_errors else "Build completed successfully"
                    }, indent=2)
            
            # If no diagnostics found, return basic status
            build_time = time.time() - build_start_time
            return json.dumps({
                "status": "triggered",
                "build_time": f"{build_time:.1f}s",
                "message": "Build triggered successfully",
                "suggestion": "Use get_diagnostics() in a few moments to check for any issues"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Build failed: {str(e)}",
                "suggestion": "Check that Xcode is running with a project open"
            }, indent=2)
    
    @server.mcp.tool()
    async def get_diagnostics() -> str:
        """Get current build errors and warnings with suggested solutions"""
        if not server.xcode_enabled:
            return json.dumps({
                "status": "disabled",
                "message": "Build diagnostics disabled - Xcode monitoring is off",
                "reason": server.config.get("xcode_monitoring", {}).get("reason", "Configuration disabled")
            }, indent=2)
        
        if not server.diagnostics_db:
            return json.dumps({
                "status": "unavailable",
                "message": "Diagnostics database not initialized",
                "suggestion": "Check Xcode monitoring configuration"
            }, indent=2)
        
        try:
            # Get recent diagnostics
            recent_diagnostics = server.diagnostics_db.get_recent_diagnostics(hours=1)
            
            if not recent_diagnostics:
                return json.dumps({
                    "status": "clean",
                    "message": "No recent build errors or warnings",
                    "suggestion": "Run build() to generate fresh diagnostics"
                }, indent=2)
            
            # Separate errors and warnings
            errors = [d for d in recent_diagnostics if d['severity'] == 'error']
            warnings = [d for d in recent_diagnostics if d['severity'] == 'warning']
            
            # Get solutions for top errors
            errors_with_solutions = []
            for error in errors[:5]:  # Top 5 errors
                solutions = server.diagnostics_db.get_solutions_for_error(error['message'])
                
                # If no specific solutions, provide general ones
                if not solutions:
                    error_lower = error['message'].lower()
                    if "cannot find" in error_lower or "unresolved" in error_lower:
                        solutions = [
                            "Check import statements are correct",
                            "Verify all required frameworks are linked",
                            "Clean build folder and rebuild"
                        ]
                    elif "syntax" in error_lower or "expected" in error_lower:
                        solutions = [
                            "Check for missing semicolons or brackets", 
                            "Verify proper Swift syntax",
                            "Check for typos in variable/function names"
                        ]
                    else:
                        solutions = ["Check error details and fix the specific issue mentioned"]
                
                errors_with_solutions.append({
                    "message": error['message'][:200],  # Truncate long messages
                    "file": error.get('file_path', 'Unknown').split('/')[-1],  # Just filename
                    "line": error.get('line_number', 'Unknown'),
                    "solutions": solutions[:3],  # Top 3 solutions
                    "timestamp": error['timestamp']
                })
            
            result = {
                "status": "issues_found" if errors else "warnings_only",
                "summary": {
                    "errors": len(errors),
                    "warnings": len(warnings),
                    "time_range": "Last hour"
                },
                "errors": errors_with_solutions,
                "top_warnings": [w['message'][:100] for w in warnings[:3]],
                "next_action": f"Fix the {len(errors)} error(s) above" if errors else "Address warnings if needed",
                "suggestion": "Use fix_error() with the error message and chosen solution"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Failed to get diagnostics: {str(e)}"
            }, indent=2)
    
    @server.mcp.tool() 
    async def fix_error(error_message: str, solution: str) -> str:
        """Apply a fix for a specific error and get immediate feedback from Xcode"""
        if not server.xcode_enabled:
            return json.dumps({
                "status": "disabled",
                "message": "Error fixing disabled - Xcode monitoring is off",
                "reason": server.config.get("xcode_monitoring", {}).get("reason", "Configuration disabled")
            }, indent=2)
        
        if not server.diagnostics_db:
            return json.dumps({
                "status": "unavailable",
                "message": "Cannot record fix - diagnostics database not available",
                "suggestion": "Apply fix manually in Xcode"
            }, indent=2)
        
        try:
            # Record that we're attempting this fix
            server.diagnostics_db.record_fix(
                error_message=error_message,
                solution=solution
            )
            
            # Provide specific guidance based on the solution
            fix_guidance = {
                "import": "Add the missing import statement to the top of your Swift file",
                "framework": "Add the framework to your project's Link Binary With Libraries build phase",
                "syntax": "Fix the syntax error in the specified file and line",
                "clean": "Use Product > Clean Build Folder in Xcode, then rebuild",
                "missing": "Check that the referenced file or symbol exists and is properly defined"
            }
            
            # Find the best guidance
            guidance = "Apply the suggested fix"
            for key, value in fix_guidance.items():
                if key.lower() in solution.lower():
                    guidance = value
                    break
            
            # Wait a moment for user to apply fix, then check build status
            result = {
                "status": "fix_recorded",
                "error": error_message[:100],
                "solution_applied": solution,
                "guidance": guidance,
                "next_steps": [
                    "Apply the fix in Xcode",
                    "Run build() to verify the fix",
                    "Check get_diagnostics() for updated status"
                ],
                "message": f"Fix recorded for error: {error_message[:50]}..."
            }
            
            # Trigger a build after a short delay to verify the fix
            time.sleep(1)
            
            # Check if we can automatically trigger verification
            verification_script = '''
            tell application "Xcode"
                if (count of windows) > 0 then
                    -- Build to verify fix
                    tell application "System Events"
                        keystroke "b" using {command down}
                    end tell
                    return "verification_build_triggered"
                else
                    return "no_project_open"
                end if
            end tell
            '''
            
            if execute_script:
                verify_result = execute_script(script_content=verification_script, language='applescript')
                if "verification_build_triggered" in verify_result.get('output', ''):
                    result["verification"] = "Build triggered to verify fix"
                    result["message"] += " Verification build started."
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to record fix: {str(e)}",
                "suggestion": "Try applying the fix manually in Xcode"
            }, indent=2)
    
    # Project Context Functions
    
    @server.mcp.tool()
    async def get_context_summary() -> str:
        """Get comprehensive project context and development status"""
        try:
            # Get all status information
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            implementation = server.swift_checker.get_swift_project_status()
            git_status = server.git_checker.get_git_status()
            
            # Calculate progress
            infra_ready = sum(1 for s in infrastructure.values() if "✅" in s)
            infra_total = len(infrastructure)
            
            context = {
                "project": {
                    "name": server.config.get("project_name", "AI Game Evolution Platform"),
                    "phase": server.config.get("current_phase", "Development"),
                    "readiness": server._calculate_overall_readiness(infrastructure, implementation)
                },
                "infrastructure": {
                    "ready": f"{infra_ready}/{infra_total} components",
                    "status": infrastructure
                },
                "implementation": {
                    "swift_files": implementation.get("swift_files_count", 0),
                    "xcode_projects": len(implementation.get("xcode_projects", [])),
                    "build_server": "Ready" if "✅" in implementation.get("build_server_status", "") else "Not configured"
                },
                "git": {
                    "branch": git_status.get("branch", "unknown"),
                    "status": "Clean" if not git_status.get("is_dirty", True) else "Has changes",
                    "last_commit": git_status.get("last_commit", {}).get("message", "Unknown")[:60]
                },
                "next_focus": server._get_suggested_next_steps()[:3]
            }
            
            return json.dumps(context, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to get context summary: {str(e)}"}, indent=2)
    
    @server.mcp.tool()
    async def update_project_phase(new_phase: str) -> str:
        """Update the current development phase and store context"""
        try:
            old_phase = server.config.get("current_phase", "Unknown")
            
            # Update config
            server.config["current_phase"] = new_phase
            
            # Save config
            config_file = server.config_path / "project_config.json"
            with open(config_file, 'w') as f:
                json.dump(server.config, f, indent=2)
            
            # Store context about the phase change
            context_change = f"Phase updated from '{old_phase}' to '{new_phase}' on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Store in session contexts
            contexts_file = server.data_path / "session_contexts.json"
            if contexts_file.exists():
                with open(contexts_file, 'r') as f:
                    contexts = json.load(f)
            else:
                contexts = []
            
            contexts.append({
                "timestamp": datetime.now().isoformat(),
                "context": context_change,
                "type": "phase_change"
            })
            
            # Keep only last 10 contexts
            contexts = contexts[-10:]
            
            with open(contexts_file, 'w') as f:
                json.dump(contexts, f, indent=2)
            
            return json.dumps({
                "status": "success",
                "old_phase": old_phase,
                "new_phase": new_phase,
                "message": f"✅ Project phase updated to: {new_phase}"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to update project phase: {str(e)}"
            }, indent=2)
    
    @server.mcp.tool()
    async def store_context(context_note: str) -> str:
        """Store important context or notes from the current development session"""
        try:
            # Load existing contexts
            contexts_file = server.data_path / "session_contexts.json"
            if contexts_file.exists():
                with open(contexts_file, 'r') as f:
                    contexts = json.load(f)
            else:
                contexts = []
            
            # Add new context with timestamp
            new_context = {
                "timestamp": datetime.now().isoformat(),
                "context": context_note,
                "type": "development_note",
                "phase": server.config.get("current_phase", "Unknown")
            }
            
            contexts.append(new_context)
            
            # Keep only last 20 contexts
            contexts = contexts[-20:]
            
            # Save
            with open(contexts_file, 'w') as f:
                json.dump(contexts, f, indent=2)
            
            return json.dumps({
                "status": "success",
                "message": "✅ Context stored successfully",
                "stored_note": context_note[:100] + "..." if len(context_note) > 100 else context_note,
                "total_contexts": len(contexts)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error", 
                "message": f"Failed to store context: {str(e)}"
            }, indent=2)
    
    @server.mcp.tool()
    async def get_recent_context() -> str:
        """Get recent development context and session history"""
        try:
            contexts_file = server.data_path / "session_contexts.json"
            if not contexts_file.exists():
                return json.dumps({
                    "status": "empty",
                    "message": "No development context history found",
                    "suggestion": "Use store_context() to start tracking development notes"
                }, indent=2)
            
            with open(contexts_file, 'r') as f:
                contexts = json.load(f)
            
            if not contexts:
                return json.dumps({
                    "status": "empty",
                    "message": "No development context found"
                }, indent=2)
            
            # Get recent contexts by type
            recent_contexts = contexts[-10:]  # Last 10
            phase_changes = [c for c in recent_contexts if c.get("type") == "phase_change"]
            dev_notes = [c for c in recent_contexts if c.get("type") == "development_note"]
            
            result = {
                "status": "found",
                "current_phase": server.config.get("current_phase", "Unknown"),
                "total_contexts": len(contexts),
                "recent_phase_changes": [
                    {
                        "timestamp": pc["timestamp"],
                        "change": pc["context"]
                    }
                    for pc in phase_changes[-3:]  # Last 3 phase changes
                ],
                "recent_notes": [
                    {
                        "timestamp": note["timestamp"],
                        "note": note["context"],
                        "phase": note.get("phase", "Unknown")
                    }
                    for note in dev_notes[-5:]  # Last 5 development notes
                ],
                "suggestion": "Use store_context() to add new development notes"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get recent context: {str(e)}"
            }, indent=2)
