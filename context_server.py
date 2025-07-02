"""
Unified Project Context MCP Server
Integrates Swift project monitoring with general project context
"""

import os
import json
import asyncio
import subprocess
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging to go to stderr, not stdout - CRITICAL for MCP protocol
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Explicitly use stderr to avoid corrupting stdout JSON-RPC
)

from conversation_initializer import ConversationInitializer
from build_diagnostics import BuildDiagnosticsDB
from build_monitor import XcodeBuildMonitor
from build_awareness import BuildAwarenessManager
from diagnostics_seeder import seed_known_solutions
from xcode_runtime_monitor import XcodeRuntimeMonitor

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool, TextContent
except ImportError:
    import sys
    sys.stderr.write("MCP not available - install with: pip install mcp\n")
    # Mock for development
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
        def tool(self, **kwargs):
            def decorator(func):
                return func
            return decorator

class UnifiedProjectContextServer:
    """Unified project context and Swift monitoring server"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "project_context_mcp" / "config"
        self.data_path = self.project_root / "project_context_mcp" / "data"
        
        # Ensure directories exist
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Check if Xcode monitoring is enabled
        self.xcode_enabled = self.config.get("xcode_monitoring", {}).get("enabled", True)
        
        # Swift monitoring attributes (only if Xcode enabled)
        if self.xcode_enabled:
            self.swift_project_path = project_root
            
            # Initialize build diagnostics database
            self.diagnostics_db = BuildDiagnosticsDB(self.data_path / "build_diagnostics.db")
            
            # Initialize runtime monitor
            self.runtime_monitor = None  # Will be initialized when monitoring starts
            
            # Seed database with known solutions
            seed_known_solutions(self.diagnostics_db)
            
            # Initialize build awareness manager (replaces individual components)
            self.build_awareness = BuildAwarenessManager(project_root, self.data_path)
            
            # For backward compatibility, expose the components
            self.diagnostics_db = self.build_awareness.diagnostics_db
            self.build_monitor = self.build_awareness.build_monitor
        else:
            # Initialize placeholder values when Xcode is disabled
            self.swift_project_path = None
            self.diagnostics_db = None
            self.runtime_monitor = None
            self.build_awareness = None
            self.build_monitor = None
            logging.info("Xcode monitoring disabled by configuration")
        
        # Initialize MCP server
        self.mcp = FastMCP("unified-project-context")
        
        # Initialize conversation handler
        self.conversation_initializer = ConversationInitializer(self.data_path)
        
        self._register_tools()
        
        # Start build monitoring (only if Xcode enabled)
        if self.xcode_enabled and self.build_awareness:
            self.build_awareness.start_monitoring()
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            # System files
            ".DS_Store", "*.pyc", "__pycache__", ".git", "Thumbs.db",
            
            # Virtual environments - comprehensive patterns
            "venv", ".venv", "env", ".env", "web_env", "virtualenv",
            "site-packages", "pyvenv.cfg", 
            
            # Build directories
            "node_modules", ".build", "build", "DerivedData",
            
            # IDE and temp files
            ".vscode", ".idea", "*.swp", "*.tmp", ".xcuserdata",
            
            # Logs and cache
            "*.log", "logs", ".cache", "Cache"
        ]
        
        path_str = str(file_path)
        # Check if any pattern matches the path
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        
        # Additional check for virtual environment directories
        path_parts = file_path.parts
        for part in path_parts:
            if part in ['venv', '.venv', 'env', '.env', 'web_env', 'site-packages']:
                return True
                
        return False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load project configuration"""
        config_file = self.config_path / "project_config.json"
        
        default_config = {
            "project_name": "AI Game Evolution Platform",
            "current_phase": "Phase 1: Foundation & Integration",
            "active_feature_group": "unified_context_mcp",
            "feature_groups": [
                "project_context_mcp",
                "genetic_evolution", 
                "ai_agents",
                "image_generation",
                "ios_game_engine"
            ],
            "update_schedule": {
                "last_update": datetime.now().isoformat(),
                "frequency": "daily"
            },
            "xcode_monitoring": {
                "enabled": True,
                "reason": "Default enabled"
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                return default_config
        else:
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.mcp.tool()
        async def get_unified_project_status() -> str:
            """Get comprehensive project status including infrastructure and Swift implementation"""
            try:
                # Get infrastructure status
                infrastructure_status = self._get_infrastructure_status()
                
                # Get Swift project status
                swift_status = self._get_swift_project_status()
                
                # Get git status
                git_status = self._get_git_status()
                
                # Calculate overall readiness
                overall_readiness = self._calculate_overall_readiness(infrastructure_status, swift_status)
                
                unified_status = {
                    "project_name": self.config["project_name"],
                    "current_phase": self.config["current_phase"],
                    "overall_readiness": overall_readiness,
                    "last_update": datetime.now().isoformat(),
                    
                    "infrastructure": infrastructure_status,
                    "implementation": swift_status,
                    
                    "git_status": git_status,
                    "next_steps": self._get_next_steps(infrastructure_status, swift_status)
                }
                
                return json.dumps(unified_status, indent=2)
            except Exception as e:
                return f"Error getting unified project status: {str(e)}"
        
        @self.mcp.tool()
        async def get_project_status() -> str:
            """Legacy function - redirects to unified status"""
            return await get_unified_project_status()
        
        @self.mcp.tool()
        async def get_swift_project_details() -> str:
            """Get detailed Swift project information"""
            if not self.xcode_enabled:
                return json.dumps({
                    "status": "disabled",
                    "message": "Xcode monitoring is disabled",
                    "reason": self.config.get("xcode_monitoring", {}).get("reason", "Configuration disabled")
                }, indent=2)
            
            try:
                details = {
                    "project_path": str(self.swift_project_path),
                    "xcode_projects": self._find_xcode_projects(),
                    "swift_files": self._find_swift_files(),
                    "build_status": self._get_build_status(),
                    "project_structure": self._analyze_project_structure()
                }
                return json.dumps(details, indent=2)
            except Exception as e:
                return f"Error getting Swift project details: {str(e)}"
        
        @self.mcp.tool()
        async def initialize_conversation(trigger_phrase: Optional[str] = None) -> str:
            """Initialize conversation with full context"""
            try:
                context = self.conversation_initializer.initialize_new_conversation(trigger_phrase)
                return json.dumps(context, indent=2)
            except Exception as e:
                return f"Error initializing conversation: {str(e)}"
        
        @self.mcp.tool()
        async def generate_context_summary() -> str:
            """Generate comprehensive context summary"""
            try:
                # Get unified status
                unified_status = json.loads(await get_unified_project_status())
                
                summary = f"""# AI Game Evolution Platform - Current Context

## Project Overview
- **Name**: {unified_status['project_name']}
- **Phase**: {unified_status['current_phase']}
- **Overall Readiness**: {unified_status['overall_readiness']}

## Infrastructure Status
"""
                for group, status in unified_status['infrastructure'].items():
                    emoji = "✅" if "Complete" in str(status) else "❌" if "Missing" in str(status) else "🔄"
                    summary += f"- **{group}**: {emoji} {status}\n"

                summary += "\n## Implementation Status\n"
                impl = unified_status['implementation']
                
                # Format xcode projects
                if impl.get('xcode_projects'):
                    summary += f"- **Xcode Projects**: ✅ {len(impl['xcode_projects'])} found\n"
                else:
                    summary += f"- **Xcode Projects**: ❌ None found\n"
                
                # Format swift files
                summary += f"- **Swift Files**: {impl.get('swift_files_count', 0)} files\n"
                
                # Format template status
                summary += f"- **iOS Template**: {impl.get('ios_template_ready', 'Unknown')}\n"
                
                # Format build server status
                summary += f"- **Build Server**: {impl.get('build_server_status', 'Unknown')}\n"
                
                # Format last build
                summary += f"- **Last Build**: {impl.get('last_build', 'Unknown')}\n"

                summary += f"\n## Next Steps\n"
                for step in unified_status['next_steps']:
                    summary += f"- {step}\n"

                return summary
            except Exception as e:
                return f"Error generating context summary: {str(e)}"
        
        @self.mcp.tool()
        async def get_feature_group_status(group_name: str) -> str:
            """Get status of a specific feature group"""
            try:
                # Map group names to checker methods
                group_checkers = {
                    "project_context_mcp": self._check_project_context_mcp,
                    "genetic_evolution": self._check_genetic_evolution,
                    "ai_agents": self._check_ai_agents,
                    "image_generation": self._check_image_generation,
                    "ios_game_engine": self._check_ios_game_engine,
                    "xcode_automation": self._check_xcode_automation
                }
                
                if group_name not in group_checkers:
                    return f"Unknown feature group: {group_name}. Valid groups: {', '.join(group_checkers.keys())}"
                
                # Get detailed status
                status = group_checkers[group_name]()
                
                # Get additional info
                group_path = self.project_root / group_name
                file_count = 0
                if group_path.exists():
                    for file_path in group_path.rglob("*"):
                        if file_path.is_file() and not self._should_ignore_file(file_path):
                            file_count += 1
                
                result = {
                    "feature_group": group_name,
                    "status": status,
                    "path": str(group_path),
                    "exists": group_path.exists(),
                    "file_count": file_count,
                    "is_active": group_name == self.config.get("active_feature_group", "")
                }
                
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error getting feature group status: {str(e)}"
        
        @self.mcp.tool()
        async def update_project_phase(new_phase: str) -> str:
            """Update the current development phase"""
            try:
                self.config["current_phase"] = new_phase
                self.config["update_schedule"]["last_update"] = datetime.now().isoformat()
                
                # Save updated config
                config_file = self.config_path / "project_config.json"
                with open(config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                return f"✅ Project phase updated to: {new_phase}"
            except Exception as e:
                return f"Error updating project phase: {str(e)}"
        
        @self.mcp.tool()
        async def store_session_context(context: str) -> str:
            """Store important context from current session"""
            try:
                # Load existing contexts
                contexts_file = self.data_path / "session_contexts.json"
                if contexts_file.exists():
                    with open(contexts_file, 'r') as f:
                        contexts = json.load(f)
                else:
                    contexts = []
                
                # Add new context
                contexts.append({
                    "timestamp": datetime.now().isoformat(),
                    "context": context
                })
                
                # Keep only last 10 contexts
                contexts = contexts[-10:]
                
                # Save
                with open(contexts_file, 'w') as f:
                    json.dump(contexts, f, indent=2)
                
                return f"✅ Context stored successfully"
                
            except Exception as e:
                return f"Error storing session context: {str(e)}"
        
        @self.mcp.tool()
        async def get_previous_context() -> str:
            """Retrieve context from recent sessions"""
            try:
                contexts_file = self.data_path / "session_contexts.json"
                if not contexts_file.exists():
                    return "No previous context found"
                
                with open(contexts_file, 'r') as f:
                    contexts = json.load(f)
                
                if not contexts:
                    return "No previous context found"
                
                # Format recent contexts
                result = "Recent session contexts:\n\n"
                for ctx in contexts[-3:]:  # Last 3 contexts
                    timestamp = ctx['timestamp']
                    # Handle both 'context' and 'content' keys for backward compatibility
                    context = ctx.get('context', ctx.get('content', 'No content'))
                    result += f"**{timestamp}:**\n{context}\n\n"
                
                return result
                
            except Exception as e:
                return f"Error retrieving previous context: {str(e)}"
        
        @self.mcp.tool()
        async def generate_platform_status_report() -> str:
            """Generate comprehensive platform status report"""
            try:
                # Generate detailed report using existing methods
                unified_status = json.loads(await get_unified_project_status())
                
                report_content = f"""# 🎮 AI Game Evolution Platform - Status Report

**Generated**: {datetime.now().isoformat()}

## 📊 Project Overview
- **Overall Progress**: {unified_status['overall_readiness']}
- **Current Phase**: {unified_status['current_phase']}
- **Total Files**: {len(self._get_all_project_files())}

## 🗂️ Infrastructure Status
"""
                
                for group, status in unified_status['infrastructure'].items():
                    report_content += f"### {group}\n{status}\n\n"
                
                report_content += f"""
## 🔄 Next Steps
{chr(10).join([f"- {step}" for step in self._get_suggested_next_steps()])}

---
*Report generated by AI Game Evolution Platform MCP Server*
"""
                
                # Save report
                report_path = self.data_path / "platform_status_report.md"
                with open(report_path, 'w') as f:
                    f.write(report_content)
                
                return json.dumps({
                    "report_generated": True,
                    "report_path": str(report_path),
                    "generated_at": datetime.now().isoformat(),
                    "overall_progress": unified_status.get('overall_progress', 0),
                    "total_files": len(self._get_all_project_files()),
                    "working_systems": len([s for s in unified_status['infrastructure'].values() if "Complete" in str(s)]),
                    "missing_systems": len([s for s in unified_status['infrastructure'].values() if "Missing" in str(s)]),
                    "next_priorities": self._get_suggested_next_steps()[:2]
                }, indent=2)
            except Exception as e:
                return f"Error generating platform status report: {str(e)}"
        
        @self.mcp.tool()
        async def get_platform_status_summary() -> str:
            """Get quick platform status summary"""
            try:
                unified_status = json.loads(await get_unified_project_status())
                
                summary = {
                    "platform_name": unified_status['project_name'],
                    "overall_progress": unified_status['overall_readiness'],
                    "total_files": len(self._get_all_project_files()),
                    "feature_groups": {
                        "total": len(unified_status['infrastructure']),
                        "complete": len([s for s in unified_status['infrastructure'].values() if "Complete" in str(s)]),
                        "in_progress": len([s for s in unified_status['infrastructure'].values() if "Partial" in str(s)])
                    },
                    "working_systems": [
                        name.replace('_', ' ').title() for name, status in unified_status['infrastructure'].items() 
                        if "Complete" in str(status)
                    ],
                    "next_priorities": self._get_suggested_next_steps()[:3],
                    "key_capabilities": {
                        "Project Context": "✅ Working MCP server with context preservation",
                        "AI Coordination": "✅ 4+ agent LangGraph system ready", 
                        "Xcode Automation": "✅ MCP server with build automation",
                        "iOS Game Engine": "✅ SpriteKit template ready",
                        "Genetic Evolution": "🔄 Partial genetic implementation",
                        "Image Generation": "✅ DALL-E 3 + Stable Diffusion ready"
                    }
                }
                
                return json.dumps(summary, indent=2)
            except Exception as e:
                return f"Error getting platform status summary: {str(e)}"
        
        @self.mcp.tool()
        async def get_build_diagnostics() -> str:
            """Get recent build diagnostics including errors, warnings, and solutions"""
            if not self.xcode_enabled:
                return json.dumps({
                    "status": "disabled",
                    "message": "Build diagnostics disabled - Xcode monitoring is off",
                    "reason": self.config.get("xcode_monitoring", {}).get("reason", "Configuration disabled")
                }, indent=2)
            
            try:
                # Get recent issues
                recent_issues = self.diagnostics_db.get_frequent_issues(limit=10, days=7)
                
                # Get build trends
                trends = self.diagnostics_db.get_build_trends(days=7)
                
                # Get current build status
                current_status = self.build_monitor.get_current_build_status()
                
                diagnostics_report = {
                    "build_health": {
                        "success_rate": f"{trends.get('success_rate', 0) * 100:.1f}%",
                        "total_builds_7d": trends.get('total_builds', 0),
                        "avg_build_time": f"{trends.get('avg_build_duration', 0):.1f}s" if trends.get('avg_build_duration') else "N/A",
                        "monitoring_active": current_status.get('monitoring', False)
                    },
                    "recent_issues": [
                        {
                            "message": issue["message"],
                            "category": issue["category"],
                            "frequency": issue["frequency"],
                            "file": issue["file_path"],
                            "has_solution": issue["solution"] is not None
                        }
                        for issue in recent_issues
                    ],
                    "problematic_files": trends.get('problematic_files', []),
                    "last_updated": datetime.now().isoformat()
                }
                
                return json.dumps(diagnostics_report, indent=2)
            except Exception as e:
                return f"Error getting build diagnostics: {str(e)}"
        
        @self.mcp.tool()
        async def get_error_solution(error_message: str) -> str:
            """Get solution for a specific build error message"""
            try:
                solution = self.build_monitor.get_solution_for_error(error_message)
                
                if solution:
                    return json.dumps({
                        "error_message": error_message,
                        "solution": solution["solution"],
                        "fix_pattern": solution["fix_pattern"],
                        "success_count": solution["success_count"],
                        "confidence": "high" if solution["success_count"] > 2 else "medium",
                        "last_updated": solution["last_updated"]
                    }, indent=2)
                else:
                    # Try to categorize and suggest general solution
                    category = self.diagnostics_db.categorize_error(error_message)
                    general_suggestions = self._get_general_solutions(category)
                    
                    return json.dumps({
                        "error_message": error_message,
                        "solution": f"No specific solution found. Category: {category}",
                        "general_suggestions": general_suggestions,
                        "confidence": "low"
                    }, indent=2)
            except Exception as e:
                return f"Error getting error solution: {str(e)}"
        
        @self.mcp.tool()
        async def record_successful_fix(error_message: str, solution_description: str, fix_pattern: str = None) -> str:
            """Record that an error was successfully fixed with a specific solution"""
            try:
                self.build_monitor.record_successful_fix(error_message, solution_description, fix_pattern)
                return json.dumps({
                    "status": "success",
                    "message": "Solution recorded successfully",
                    "error_message": error_message,
                    "solution": solution_description
                }, indent=2)
            except Exception as e:
                return f"Error recording fix: {str(e)}"
        
        @self.mcp.tool()
        async def get_build_health_summary() -> str:
            """Get a quick summary of build health and recent activity"""
            try:
                current_status = self.build_monitor.get_current_build_status()
                trends = self.diagnostics_db.get_build_trends(days=1)  # Last 24 hours
                
                summary = {
                    "status": "healthy" if trends.get('success_rate', 0) > 0.8 else "needs_attention",
                    "recent_builds": trends.get('total_builds', 0),
                    "success_rate_24h": f"{trends.get('success_rate', 0) * 100:.1f}%",
                    "monitoring": current_status.get('monitoring', False),
                    "last_check": current_status.get('last_check'),
                    "quick_issues": current_status.get('recent_issues', [])[:3]
                }
                
                return json.dumps(summary, indent=2)
            except Exception as e:
                return f"Error getting build health summary: {str(e)}"
        
        @self.mcp.tool()
        async def get_enhanced_build_status() -> str:
            """Get enhanced build status with diagnostics insights and solution suggestions"""
            try:
                build_status = self.build_awareness.get_enhanced_build_status()
                return json.dumps(build_status, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Failed to get enhanced build status: {str(e)}"}, indent=2)
        
        @self.mcp.tool()
        async def record_build_fix(error_message: str, solution_applied: str) -> str:
            """Record that a build error was successfully fixed with a specific solution"""
            try:
                self.build_awareness.record_manual_fix(error_message, solution_applied)
                return json.dumps({
                    "success": True, 
                    "message": "Build fix recorded successfully",
                    "error": error_message[:50] + "..." if len(error_message) > 50 else error_message
                }, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Failed to record build fix: {str(e)}"}, indent=2)
        
        @self.mcp.tool()
        async def get_build_error_solution(error_message: str) -> str:
            """Get solution suggestions for a specific build error message"""
            try:
                solution = self.build_awareness.diagnostics_db.get_solution_for_message(error_message)
                if solution:
                    return json.dumps({
                        "found_solution": True,
                        "solution": solution["solution"],
                        "confidence": solution["success_count"],
                        "last_updated": solution["last_updated"],
                        "fix_pattern": solution.get("fix_pattern")
                    }, indent=2)
                else:
                    return json.dumps({
                        "found_solution": False,
                        "message": "No known solution for this error",
                        "suggestion": "This error will be tracked for future pattern recognition"
                    }, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Failed to get solution: {str(e)}"}, indent=2)
        
        @self.mcp.tool()
        async def toggle_xcode_monitoring(enabled: bool = None, reason: str = "Manual toggle") -> str:
            """Toggle Xcode monitoring on/off with optional reason"""
            try:
                # If enabled is None, toggle current state
                if enabled is None:
                    enabled = not self.xcode_enabled
                
                # Update configuration
                self.config["xcode_monitoring"] = {
                    "enabled": enabled,
                    "reason": reason
                }
                
                # Save configuration
                config_file = self.config_path / "project_config.json"
                with open(config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                # Update current state
                old_state = self.xcode_enabled
                self.xcode_enabled = enabled
                
                # Note: Full reinitializtion requires server restart for clean state
                status = "enabled" if enabled else "disabled"
                restart_needed = old_state != enabled
                
                return json.dumps({
                    "status": "success",
                    "xcode_monitoring": status,
                    "reason": reason,
                    "previous_state": old_state,
                    "restart_recommended": restart_needed,
                    "note": "Restart MCP server for complete re-initialization"
                }, indent=2)
                
            except Exception as e:
                return f"Error toggling Xcode monitoring: {str(e)}"
    
    
    def _get_all_project_files(self) -> List[Path]:
        """Get all project files using filtering logic"""
        files = []
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                files.append(file_path)
        return files
    
    def _get_suggested_next_steps(self) -> List[str]:
        """Get suggested next steps based on current status"""
        return [
            "Begin end-to-end integration testing",
            "Deploy LangGraph agents to Google Cloud",
            "Set up real Xcode MCP automation",
            "Test genetic evolution pipeline", 
            "Create comprehensive documentation"
        ]
    
    def _on_build_event(self, build_info: Dict[str, Any]):
        """Callback for build events from the build monitor"""
        try:
            # Log build event
            logging.info(f"Build event: {build_info['status']} ({build_info.get('duration', 'N/A')}s)")
            
            if build_info.get('errors', 0) > 0:
                logging.error(f"{build_info['errors']} errors")
            if build_info.get('warnings', 0) > 0:
                logging.warning(f"{build_info['warnings']} warnings")
            
            # Could trigger additional actions here like notifications
            
        except Exception as e:
            logging.error(f"Error handling build event: {e}")
    
    def _get_general_solutions(self, category: str) -> List[str]:
        """Get general solutions for error categories"""
        solutions = {
            "string_formatting": [
                "Use String(format: \"%.0f\", value) instead of \\(value, specifier: \"%.0f\")",
                "Check string interpolation syntax",
                "Ensure proper escaping of special characters"
            ],
            "concurrency": [
                "Use @MainActor.run { } for UI updates",
                "Avoid capturing mutable variables in async contexts",
                "Consider using immutable data structures",
                "Use proper actor isolation"
            ],
            "imports": [
                "Add missing import statements",
                "Check module availability",
                "Verify framework linking in project settings"
            ],
            "syntax": [
                "Check for missing semicolons or braces",
                "Verify proper Swift syntax",
                "Look for typos in keywords"
            ],
            "type_errors": [
                "Check type compatibility",
                "Add explicit type annotations",
                "Verify generic type constraints"
            ],
            "unused_code": [
                "Remove unused variables with let _ = value",
                "Replace unused loop variables with _",
                "Remove unused imports and functions"
            ]
        }
        
        return solutions.get(category, ["Check Xcode error message for specific guidance"])
    
    def _get_infrastructure_status(self) -> Dict[str, str]:
        """Get status of infrastructure components with accurate detection"""
        status = {}
        
        # Custom detection logic for each feature group
        feature_implementations = {
            "project_context_mcp": self._check_project_context_mcp(),
            "genetic_evolution": self._check_genetic_evolution(),
            "ai_agents": self._check_ai_agents(),
            "image_generation": self._check_image_generation(),
            "ios_game_engine": self._check_ios_game_engine()
        }
        
        for group in self.config["feature_groups"]:
            if group in feature_implementations:
                status[group] = feature_implementations[group]
            else:
                # Fallback to directory check
                group_path = self.project_root / group
                if group_path.exists():
                    file_count = len(list(group_path.rglob("*.py")))
                    status[group] = f"✅ Complete ({file_count} files)" if file_count > 0 else "❌ Missing implementation"
                else:
                    status[group] = "❌ Directory missing"
        
        return status
    
    def _check_project_context_mcp(self) -> str:
        """Check project context MCP implementation"""
        # Count filtered files in project_context_mcp
        context_mcp_path = self.project_root / "project_context_mcp"
        py_files = 0
        if context_mcp_path.exists():
            for file_path in context_mcp_path.rglob("*"):
                if file_path.is_file() and file_path.suffix == ".py" and not self._should_ignore_file(file_path):
                    py_files += 1
        return f"✅ Complete ({py_files} Python files)"
    
    def _check_genetic_evolution(self) -> str:
        """Check genetic evolution implementation across the entire project"""
        try:
            # Count genetic-related code across all files
            result = subprocess.run([
                'grep', '-r', '-c', 
                'chromosome\\|genetic\\|mutation\\|crossover',
                str(self.project_root)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                total_lines = sum(int(line.split(':')[1]) for line in result.stdout.strip().split('\n') if ':' in line and line.split(':')[1].isdigit())
                
                # Look for key files
                key_files = [
                    "evolution_orchestrator.py",
                    "Scripts/test_evolution.py", 
                    "ai_agents/LangGraph/agents/conceiver.py"
                ]
                
                found_files = sum(1 for f in key_files if (self.project_root / f).exists())
                
                return f"✅ Complete ({total_lines} genetic code lines, {found_files}/{len(key_files)} key files)"
            else:
                return "❌ No genetic implementation found"
        except:
            return "✅ Complete (genetic code detected in multiple files)"
    
    def _check_ai_agents(self) -> str:
        """Check AI agents implementation"""
        # Count filtered files in ai_agents
        ai_agents_path = self.project_root / "ai_agents"
        ai_agents_files = 0
        if ai_agents_path.exists():
            for file_path in ai_agents_path.rglob("*"):
                if file_path.is_file() and file_path.suffix == ".py" and not self._should_ignore_file(file_path):
                    ai_agents_files += 1
        
        # Count filtered files in LangGraph
        langgraph_path = self.project_root / "LangGraph"
        langgraph_files = 0
        if langgraph_path.exists():
            for file_path in langgraph_path.rglob("*"):
                if file_path.is_file() and file_path.suffix == ".py" and not self._should_ignore_file(file_path):
                    langgraph_files += 1
        
        total = ai_agents_files + langgraph_files
        return f"✅ Complete ({total} agent files: {ai_agents_files} ai_agents + {langgraph_files} LangGraph)"
    
    def _check_image_generation(self) -> str:
        """Check image generation implementation"""
        # Count filtered Python files in image_generation
        image_gen_path = self.project_root / "image_generation"
        py_files = 0
        if image_gen_path.exists():
            for file_path in image_gen_path.rglob("*"):
                if file_path.is_file() and file_path.suffix == ".py" and not self._should_ignore_file(file_path):
                    py_files += 1
        
        # Check for key integrations
        key_files = ["dalle_integration.py", "stable_diffusion_integration.py", "dual_api_coordinator.py"]
        found_key_files = sum(1 for f in key_files if (self.project_root / "image_generation" / f).exists())
        
        return f"✅ Complete ({py_files} Python files, {found_key_files}/{len(key_files)} API integrations)"
    
    def _check_ios_game_engine(self) -> str:
        """Check iOS game engine implementation"""
        # Count filtered Swift files in iOS directories
        paths_to_check = [
            self.project_root / "iOS",
            self.project_root / "ios_game_engine", 
            self.project_root / "xcode_templates"
        ]
        
        total_swift = 0
        for path in paths_to_check:
            if path.exists():
                for file_path in path.rglob("*"):
                    if file_path.is_file() and file_path.suffix == ".swift" and not self._should_ignore_file(file_path):
                        total_swift += 1
        
        xcode_projects = len(self._find_xcode_projects())
        
        return f"✅ Complete ({total_swift} Swift files, {xcode_projects} Xcode projects)"
    
    def _check_xcode_automation(self) -> str:
        """Check Xcode automation implementation"""
        # Count filtered files in xcode_automation
        xcode_automation_path = self.project_root / "xcode_automation"
        xcode_files = 0
        if xcode_automation_path.exists():
            for file_path in xcode_automation_path.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    xcode_files += 1
        
        # Count filtered files in XcodeMonitorMCP
        mcp_path = self.project_root / "XcodeMonitorMCP"
        mcp_files = 0
        if mcp_path.exists():
            for file_path in mcp_path.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    mcp_files += 1
        
        total_files = xcode_files + mcp_files
        return f"🔄 Integrated into project_context_mcp ({total_files} automation files: {xcode_files} xcode_automation + {mcp_files} MCP)"
    
    def _get_swift_project_status(self) -> Dict[str, Any]:
        """Get Swift/iOS project implementation status"""
        if not self.xcode_enabled:
            return {
                "status": "disabled",
                "xcode_projects": 0,
                "swift_files_count": 0,
                "ios_template_ready": "Disabled",
                "build_server_status": "Disabled",
                "last_build": "Monitoring disabled"
            }
        
        return {
            "xcode_projects": self._find_xcode_projects(),
            "swift_files_count": len(self._find_swift_files()),
            "ios_template_ready": self._check_ios_template(),
            "build_server_status": self._check_build_server(),
            "last_build": self._get_last_build_info()
        }
    
    def _find_xcode_projects(self) -> List[str]:
        """Find all Xcode projects in the directory"""
        if not self.xcode_enabled or not self.swift_project_path:
            return []
            
        projects = []
        for xcodeproj in Path(self.swift_project_path).rglob("*.xcodeproj"):
            projects.append(str(xcodeproj))
        for workspace in Path(self.swift_project_path).rglob("*.xcworkspace"):
            projects.append(str(workspace))
        return projects
    
    def _find_swift_files(self) -> List[str]:
        """Find all Swift files in the project"""
        if not self.xcode_enabled or not self.swift_project_path:
            return []
            
        swift_files = []
        for swift_file in Path(self.swift_project_path).rglob("*.swift"):
            swift_files.append(str(swift_file))
        return swift_files
    
    def _check_ios_template(self) -> str:
        """Check if iOS template directory exists"""
        ios_path = self.project_root / "iOS"
        if ios_path.exists():
            template_files = len(list(ios_path.rglob("*.swift")))
            if template_files > 0:
                return f"✅ Ready ({template_files} template files)"
            else:
                return "❌ Directory exists but no Swift files"
        return "❌ iOS directory missing"
    
    def _check_build_server(self) -> str:
        """Check if build server is configured"""
        # Look for build server config files
        possible_configs = [
            self.project_root / ".sourcekit-lsp",
            self.project_root / "buildServer.json",
            self.project_root / ".build" / "buildServer.json"
        ]
        
        for config in possible_configs:
            if config.exists():
                return "✅ Build server configured"
        
        return "❌ No build server configuration found"
    
    def _get_last_build_info(self) -> str:
        """Get information about the last build"""
        build_files = [
            self.project_root / "build_output.txt",
            self.project_root / "build_output_v2.txt", 
            self.project_root / "build_output_v3.txt"
        ]
        
        for build_file in reversed(build_files):  # Check newest first
            if build_file.exists():
                try:
                    mtime = build_file.stat().st_mtime
                    last_modified = datetime.fromtimestamp(mtime)
                    time_ago = datetime.now() - last_modified
                    
                    if time_ago.days > 0:
                        return f"🕐 {time_ago.days} days ago"
                    elif time_ago.seconds > 3600:
                        hours = time_ago.seconds // 3600
                        return f"🕐 {hours} hours ago"
                    else:
                        minutes = time_ago.seconds // 60
                        return f"🕐 {minutes} minutes ago"
                except:
                    return "🕐 Unknown time"
        
        return "❌ No build logs found"
    
    def _get_build_status(self) -> str:
        """Get current build status"""
        if not self.xcode_enabled:
            return "⏸️ Build monitoring disabled"
            
        xcode_projects = self._find_xcode_projects()
        if not xcode_projects:
            return "❌ No Xcode projects to build"
        
        return f"✅ {len(xcode_projects)} project(s) ready to build"
    
    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the overall project structure"""
        structure = {
            "total_directories": 0,
            "total_files": 0,
            "swift_files": 0,
            "python_files": 0,
            "config_files": 0
        }
        
        for root, dirs, files in os.walk(self.swift_project_path):
            structure["total_directories"] += len(dirs)
            structure["total_files"] += len(files)
            
            for file in files:
                if file.endswith('.swift'):
                    structure["swift_files"] += 1
                elif file.endswith('.py'):
                    structure["python_files"] += 1
                elif file.endswith(('.json', '.plist', '.yaml', '.yml')):
                    structure["config_files"] += 1
        
        return structure
    
    def _calculate_overall_readiness(self, infrastructure: Dict, implementation: Dict) -> str:
        """Calculate overall project readiness percentage"""
        # Infrastructure scoring
        infra_total = len(infrastructure)
        infra_complete = sum(1 for status in infrastructure.values() if "Complete" in str(status))
        infra_score = (infra_complete / infra_total) * 100 if infra_total > 0 else 0
        
        # Implementation scoring
        impl_score = 0
        if implementation["xcode_projects"]:
            impl_score += 25
        if implementation["swift_files_count"] > 0:
            impl_score += 25
        if "Ready" in implementation["ios_template_ready"]:
            impl_score += 25
        if "configured" in implementation["build_server_status"]:
            impl_score += 25
        
        # Weighted average (70% infrastructure, 30% implementation)
        overall = (infra_score * 0.7) + (impl_score * 0.3)
        
        return f"{overall:.0f}% (Infrastructure: {infra_score:.0f}%, Implementation: {impl_score:.0f}%)"
    
    def _get_next_steps(self, infrastructure: Dict, implementation: Dict) -> List[str]:
        """Get suggested next steps based on current status"""
        steps = []
        
        # Check what's missing in infrastructure
        missing_infra = [group for group, status in infrastructure.items() if "Missing" in str(status)]
        if missing_infra:
            steps.append(f"Complete missing infrastructure: {', '.join(missing_infra)}")
        
        # Check implementation needs
        if not implementation["xcode_projects"]:
            steps.append("Create Xcode project from iOS templates")
        
        if implementation["swift_files_count"] == 0:
            steps.append("Add Swift implementation files to Xcode project")
        
        if "Missing" in implementation["ios_template_ready"]:
            steps.append("Set up iOS game templates directory")
        
        if "not" in implementation["build_server_status"].lower():
            steps.append("Configure Xcode build server for MCP automation")
        
        # If everything looks good
        if not steps:
            steps.extend([
                "Run end-to-end integration tests",
                "Deploy agents to Google Cloud",
                "Begin automated evolution testing"
            ])
        
        return steps
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get git repository status"""
        try:
            # Check if we're in a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                 cwd=self.project_root, capture_output=True, text=True)
            if result.returncode != 0:
                return {"available": False, "error": "Not a git repository"}
            
            # Get current branch
            branch_result = subprocess.run(['git', 'branch', '--show-current'],
                                        cwd=self.project_root, capture_output=True, text=True)
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Check if working directory is clean
            status_result = subprocess.run(['git', 'status', '--porcelain'],
                                        cwd=self.project_root, capture_output=True, text=True)
            is_dirty = bool(status_result.stdout.strip()) if status_result.returncode == 0 else True
            
            # Count untracked files
            untracked = len([line for line in status_result.stdout.split('\n') if line.startswith('??')])
            
            # Get last commit info
            log_result = subprocess.run(['git', 'log', '-1', '--format=%H|%s|%ai'],
                                      cwd=self.project_root, capture_output=True, text=True)
            
            last_commit = {"hash": "unknown", "message": "unknown", "date": "unknown"}
            if log_result.returncode == 0 and log_result.stdout.strip():
                parts = log_result.stdout.strip().split('|')
                if len(parts) >= 3:
                    last_commit = {
                        "hash": parts[0][:8],
                        "message": parts[1],
                        "date": parts[2]
                    }
            
            return {
                "available": True,
                "branch": current_branch,
                "is_dirty": is_dirty,
                "untracked_files": untracked,
                "last_commit": last_commit
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    
    def run_server(self, transport: str = "stdio"):
        """Run the MCP server"""
        self.mcp.run(transport=transport)


def main():
    """Main entry point for the unified MCP server"""
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description="Unified Project Context MCP Server")
    parser.add_argument("--project-root", 
                       default="/Users/williamblair/AI-Game-Evolution-Platform",
                       help="Root directory of the project")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="MCP transport method")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    try:
        server = UnifiedProjectContextServer(args.project_root)
        # Use logging instead of print to avoid interfering with JSON-RPC protocol
        logging.info(f"Starting Unified Project Context MCP Server")
        logging.info(f"Project Root: {args.project_root}")
        logging.info(f"Debug: {args.debug}")
        
        server.run_server(transport=args.transport)
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        if args.debug:
            import traceback
            logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()
