"""
Project status related MCP tools
"""
import json
from typing import Any
from datetime import datetime
from utils.file_utils import analyze_project_structure


def register_tools(server):
    """Register project status tools with the server"""
    
    @server.mcp.tool()
    async def get_unified_project_status() -> str:
        """Get comprehensive project status including infrastructure and Swift implementation"""
        try:
            # Get infrastructure status
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            
            # Get Swift project status
            implementation = server.swift_checker.get_swift_project_status()
            
            # Get git status
            git_status = server.git_checker.get_git_status()
            
            # Calculate overall readiness
            overall_readiness = server._calculate_overall_readiness(infrastructure, implementation)
            
            # Get next steps
            next_steps = server._get_suggested_next_steps()
            
            status = {
                "project_name": server.config.get("project_name", "Unknown Project"),
                "current_phase": server.config.get("current_phase", "Unknown Phase"),
                "overall_readiness": overall_readiness,
                "last_update": datetime.now().isoformat(),
                "infrastructure": infrastructure,
                "implementation": implementation,
                "git_status": git_status,
                "next_steps": next_steps
            }
            
            return json.dumps(status, indent=2)
            
        except Exception as e:
            return f"Error getting unified project status: {str(e)}"
    
    @server.mcp.tool()
    async def get_project_status() -> str:
        """Legacy function - redirects to unified status"""
        return await get_unified_project_status()

    @server.mcp.tool()
    async def get_platform_status_summary() -> str:
        """Get quick platform status summary"""
        try:
            # Get infrastructure status
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            
            # Count ready components
            ready_count = sum(1 for status in infrastructure.values() if "✅" in status)
            total_count = len(infrastructure)
            
            # Get Swift status
            swift_status = server.swift_checker.get_swift_project_status()
            swift_files = swift_status.get("swift_files_count", 0)
            
            # Get build status
            build_status = server.swift_checker.get_build_status()
            
            # Format summary
            summary_lines = [
                f"🎮 **AI Game Evolution Platform Status**",
                f"",
                f"**Infrastructure:** {ready_count}/{total_count} components ready",
                f"**Swift Implementation:** {swift_files} files",
                f"**Build Status:** {build_status}",
                f"**Current Phase:** {server.config.get('current_phase', 'Unknown')}",
                f"",
                f"**Quick Actions:**"
            ]
            
            # Add next steps
            next_steps = server._get_suggested_next_steps()
            for i, step in enumerate(next_steps, 1):
                summary_lines.append(f"{i}. {step}")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            return f"Error getting platform status summary: {str(e)}"
    
    @server.mcp.tool()
    async def generate_platform_status_report() -> str:
        """Generate comprehensive platform status report"""
        try:
            # Get all status information
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            implementation = server.swift_checker.get_swift_project_status()
            git_status = server.git_checker.get_git_status()
            project_structure = analyze_project_structure(server.project_root)
            
            # Generate markdown report
            report = []
            report.append(f"# AI Game Evolution Platform - Status Report")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            # Project Overview
            report.append("## Project Overview")
            report.append(f"- **Name:** {server.config.get('project_name', 'Unknown')}")
            report.append(f"- **Current Phase:** {server.config.get('current_phase', 'Unknown')}")
            report.append(f"- **Total Files:** {project_structure['total_files']}")
            report.append(f"- **Total Lines:** {project_structure['total_lines']:,}")
            report.append("")
            
            # Infrastructure Status
            report.append("## Infrastructure Components")
            for component, status in infrastructure.items():
                report.append(f"- **{component.replace('_', ' ').title()}:** {status}")
            report.append("")
            
            # Implementation Status
            report.append("## iOS Implementation")
            report.append(f"- **Swift Files:** {implementation['swift_files_count']}")
            report.append(f"- **Xcode Projects:** {len(implementation['xcode_projects'])}")
            report.append(f"- **Template Status:** {implementation['ios_template_ready']}")
            report.append(f"- **Build Server:** {implementation['build_server_status']}")
            report.append("")
            
            # Git Status
            if git_status.get("available"):
                report.append("## Version Control")
                report.append(f"- **Branch:** {git_status['branch']}")
                report.append(f"- **Status:** {'Modified' if git_status['is_dirty'] else 'Clean'}")
                report.append(f"- **Untracked Files:** {git_status['untracked_files']}")
                if git_status.get('last_commit'):
                    commit = git_status['last_commit']
                    report.append(f"- **Last Commit:** {commit['hash']} - {commit['message']}")
            report.append("")
            
            # Save report
            report_path = server.data_path / "platform_status_report.md"
            with open(report_path, 'w') as f:
                f.write("\n".join(report))
            
            # Also save as JSON
            json_report = {
                "generated": datetime.now().isoformat(),
                "infrastructure": infrastructure,
                "implementation": implementation,
                "git_status": git_status,
                "project_structure": project_structure
            }
            
            json_path = server.data_path / "platform_status_report.json"
            with open(json_path, 'w') as f:
                json.dump(json_report, f, indent=2)
            
            return f"Report generated successfully!\n\nMarkdown: {report_path}\nJSON: {json_path}\n\n" + "\n".join(report)
            
        except Exception as e:
            return f"Error generating platform status report: {str(e)}"

    @server.mcp.tool()
    async def get_platform_status_summary() -> str:
        """Get quick platform status summary"""
        try:
            from ..server.base import UnifiedProjectContextServer
            server = UnifiedProjectContextServer(str(project_root))
            
            infrastructure = server._check_infrastructure_status()
            
            summary_lines = [
                f"**Platform Status Summary**",
                f"**Current Phase:** {server.config.get('current_phase', 'Unknown')}",
                f"",
                f"**Component Status:**"
            ]
            
            for component, status in infrastructure.items():
                summary_lines.append(f"- {component.replace('_', ' ').title()}: {status}")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            return f"Error getting platform status summary: {str(e)}"
    
    @server.mcp.tool()
    async def generate_platform_status_report() -> str:
        """Generate comprehensive platform status report"""
        try:
            # Get all status information
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            swift_status = server.swift_checker.get_swift_project_status()
            git_status = server.git_checker.get_git_status()
            project_structure = analyze_project_structure(server.project_root)
            
            # Generate markdown report
            report_lines = [
                f"# AI Game Evolution Platform - Status Report",
                f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                f"",
                f"## Executive Summary",
                f"- **Project**: {server.config.get('project_name', 'Unknown')}",
                f"- **Phase**: {server.config.get('current_phase', 'Unknown')}",
                f"- **Overall Readiness**: {server._calculate_overall_readiness(infrastructure, swift_status)}",
                f"",
                f"## Infrastructure Components",
                f""
            ]
            
            for component, status in infrastructure.items():
                report_lines.append(f"### {component.replace('_', ' ').title()}")
                report_lines.append(f"- Status: {status}")
                report_lines.append("")
            
            # Add more sections...
            report_lines.extend([
                f"## Implementation Status",
                f"- Swift Files: {swift_status.get('swift_files_count', 0)}",
                f"- Xcode Projects: {len(swift_status.get('xcode_projects', []))}",
                f"- Build Server: {swift_status.get('build_server_status', 'Unknown')}",
                f"",
                f"## Git Repository",
                f"- Branch: {git_status.get('branch', 'Unknown')}",
                f"- Clean: {'No' if git_status.get('is_dirty', True) else 'Yes'}",
                f"- Untracked Files: {git_status.get('untracked_files', 0)}"
            ])
            
            # Save report
            report_path = server.data_path / "platform_status_report.md"
            with open(report_path, 'w') as f:
                f.write("\n".join(report_lines))
            
            # Also save as JSON
            json_report = {
                "generated_at": datetime.now().isoformat(),
                "infrastructure": infrastructure,
                "implementation": swift_status,
                "git_status": git_status,
                "project_structure": project_structure
            }
            
            json_path = server.data_path / "platform_status_report.json"
            with open(json_path, 'w') as f:
                json.dump(json_report, f, indent=2)
            
            return f"✅ Platform status report generated successfully!\n\nMarkdown: {report_path}\nJSON: {json_path}"
            
        except Exception as e:
            return f"Error generating platform status report: {str(e)}"