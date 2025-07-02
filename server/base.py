"""
Base server class for Project Context MCP Server
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from conversation_initializer import ConversationInitializer
from build_diagnostics import BuildDiagnosticsDB
from build_awareness import BuildAwarenessManager
from diagnostics_seeder import seed_known_solutions
from xcode_runtime_monitor import XcodeRuntimeMonitor
from project_registry import ProjectRegistry

from utils.config_utils import load_config
from utils.file_utils import should_ignore_file, get_all_project_files, analyze_project_structure
from checkers.infrastructure import InfrastructureChecker
from checkers.swift_project import SwiftProjectChecker
from checkers.git_status import GitStatusChecker

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

        # Initialize project registry
        self.project_registry = ProjectRegistry(self.data_path)
        
        # Check if we have a current project or should use the provided root
        current_project = self.project_registry.get_current_project()
        if current_project and Path(current_project["path"]).exists():
            self.project_root = Path(current_project["path"])
            logging.info(f"Using current project: {current_project['name']} at {self.project_root}")
        else:
            # Add current project to registry if not present
            project_name = Path(project_root).name
            self.project_registry.add_project(
                name=project_name,
                path=project_root,
                description=f"Auto-registered project: {project_name}",
                project_type="auto-detected"
            )
            self.project_registry.set_current_project(project_name)
            logging.info(f"Auto-registered and selected project: {project_name}")

        # Load configuration
        self.config = load_config(self.config_path)
        
        # Check if Xcode monitoring is enabled
        self.xcode_enabled = self.config.get("xcode_monitoring", {}).get("enabled", True)
        
        # Initialize for current project
        self._reinitialize_for_project(str(self.project_root))
            logging.info("Xcode monitoring disabled by configuration")
    
    def _reinitialize_for_project(self, project_path: str):
        """Reinitialize checkers and components for a new project"""
        self.project_root = Path(project_path)
        
        # Initialize checkers
        self.infrastructure_checker = InfrastructureChecker(self.project_root)
        self.git_checker = GitStatusChecker(self.project_root)
        
        # Swift monitoring attributes (only if Xcode enabled)
        if self.xcode_enabled:
            self.swift_project_path = project_path
            self.swift_checker = SwiftProjectChecker(self.project_root)
            
            # Initialize build diagnostics database
            self.diagnostics_db = BuildDiagnosticsDB(self.data_path / "build_diagnostics.db")
            
            # Initialize runtime monitor
            self.runtime_monitor = None  # Will be initialized when monitoring starts
            
            # Seed database with known solutions
            seed_known_solutions(self.diagnostics_db)
        else:
            # Initialize placeholder values when Xcode is disabled
            self.swift_project_path = None
            self.swift_checker = None
            self.diagnostics_db = None
            self.runtime_monitor = None
            logging.info("Xcode monitoring disabled by configuration")
        
        # Initialize build awareness manager (replaces individual components)
        self.build_awareness = BuildAwarenessManager(project_root, self.data_path)
        
        # For backward compatibility, expose the components
        self.diagnostics_db = self.build_awareness.diagnostics_db
        self.build_monitor = self.build_awareness.build_monitor
        
        # Initialize MCP server
        self.mcp = FastMCP("unified-project-context")
        
        # Initialize conversation handler
        self.conversation_initializer = ConversationInitializer(self.data_path)
        
        # Start build monitoring
        self.build_awareness.start_monitoring()
    
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
        """Get general solutions for a category of errors"""
        solutions = {
            "module": [
                "Check if all required packages are installed",
                "Verify import statements are correct",
                "Ensure virtual environment is activated",
                "Run: pip install -r requirements.txt"
            ],
            "syntax": [
                "Check for missing colons, parentheses, or quotes",
                "Verify indentation is consistent",
                "Look for typos in variable/function names"
            ],
            "type": [
                "Ensure variables have correct types",
                "Check function return types match expectations",
                "Verify type hints are accurate"
            ]
        }
        return solutions.get(category, ["Check error message for specific details"])

    def _get_suggested_next_steps(self) -> List[str]:
        """Get suggested next steps based on current state"""
        steps = []
        
        # Check infrastructure status
        infra_status = self.infrastructure_checker.get_infrastructure_status()
        
        # Add steps based on what's incomplete
        for component, status in infra_status.items():
            if "❌" in status:
                steps.append(f"Set up {component.replace('_', ' ')} infrastructure")
            elif "🟨" in status:
                steps.append(f"Complete {component.replace('_', ' ')} implementation")
        
        # Check Swift project status  
        swift_status = self.swift_checker.get_swift_project_status() if self.swift_checker else {"build_server_status": "Disabled"}
        if "❌" in swift_status.get("build_server_status", ""):
            steps.append("Configure Xcode build server")
            
        # Always include some general steps
        if not steps:
            steps = [
                "Run end-to-end integration tests",
                "Deploy agents to Google Cloud", 
                "Begin automated evolution testing"
            ]
            
        return steps[:3]  # Return top 3 steps
    
    def _calculate_overall_readiness(self, infrastructure: Dict, implementation: Dict) -> str:
        """Calculate overall project readiness percentage"""
        # Infrastructure components (60% weight)
        infra_ready = sum(1 for status in infrastructure.values() if "✅" in status)
        infra_total = len(infrastructure)
        infra_score = (infra_ready / infra_total) * 60 if infra_total > 0 else 0
        
        # Implementation components (40% weight)
        impl_ready = 0
        impl_total = 3  # xcode projects, template, build server
        
        if implementation.get("xcode_projects"):
            impl_ready += 1
        if "✅" in implementation.get("ios_template_ready", ""):
            impl_ready += 1
        if "✅" in implementation.get("build_server_status", ""):
            impl_ready += 1
            
        impl_score = (impl_ready / impl_total) * 40 if impl_total > 0 else 0
        
        total_score = int(infra_score + impl_score)
        infra_percent = int((infra_ready / infra_total) * 100) if infra_total > 0 else 0
        impl_percent = int((impl_ready / impl_total) * 100) if impl_total > 0 else 0
        
        return f"{total_score}% (Infrastructure: {infra_percent}%, Implementation: {impl_percent}%)"
    
    def run_server(self, transport: str = "stdio"):
        """Run the MCP server"""
        # Import simplified tools to register them
        from tools import simple_tools
        
        # Register the 4 essential tools with the server
        simple_tools.register_tools(self)
        
        # Run the server
        import asyncio
        asyncio.run(self.mcp.run(transport=transport))
