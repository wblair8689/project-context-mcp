"""
Enhanced Documentation Manager - Auto-update README files and generate status reports
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess


class EnhancedDocumentationManager:
    """Manages automatic documentation updates and status report generation"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.project_context_path = self.project_root / "project_context_mcp"
        self.data_path = self.project_context_path / "data"
        
        # Ensure data directory exists
        self.data_path.mkdir(parents=True, exist_ok=True)
    
    def generate_platform_status_report(self, project_tracker) -> Dict[str, Any]:
        """Generate comprehensive platform status report"""
        
        # Get project data
        project_status = project_tracker.get_project_status()
        
        # Analyze feature groups
        feature_analysis = self._analyze_feature_groups()
        
        # Get implementation status
        implementation_status = self._assess_implementation_status()
        
        # Get git status
        git_info = project_status.get('git_status', {})
        
        # Calculate overall progress
        overall_progress = self._calculate_overall_progress(feature_analysis)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "project_overview": {
                "name": "AI Game Evolution Platform AI Game Evolution Platform",
                "description": "Autonomous game evolution using genetic algorithms and multi-agent AI",
                "total_files": project_status['file_counts']['total'],
                "python_files": project_status['file_counts']['python'],
                "swift_files": project_status['file_counts']['swift'],
                "overall_progress": overall_progress
            },
            "feature_groups": feature_analysis,
            "implementation_status": implementation_status,
            "git_status": git_info,
            "next_priorities": self._get_next_priorities(feature_analysis),
            "system_capabilities": self._assess_system_capabilities(),
            "architecture_summary": self._get_architecture_summary()
        }
        
        return report
    
    def _analyze_feature_groups(self) -> List[Dict[str, Any]]:
        """Analyze status of each feature group with CURRENT reality check"""
        
        feature_groups = [
            {
                "name": "project_context_mcp",
                "description": "Project management and context preservation",
                "priority": 1,
                "expected_files": ["context_server.py", "project_tracker.py", "documentation_manager.py"]
            },
            {
                "name": "genetic_evolution", 
                "description": "17-parameter chromosome system and genetic algorithms",
                "priority": 2,
                "expected_files": ["game_chromosome.py", "evolution_engine.py", "fitness_evaluator.py"]
            },
            {
                "name": "ai_agents",
                "description": "LangGraph multi-agent orchestration", 
                "priority": 3,
                "expected_files": ["conceiver.py", "judge.py", "visual_artist.py", "visual_artist_sd.py"]
            },
            {
                "name": "image_generation",
                "description": "DALL-E 3 + Stable Diffusion dual API pipeline",
                "priority": 4,
                "expected_files": ["dalle_integration.py", "stable_diffusion_integration.py"]
            },
            {
                "name": "ios_game_engine",
                "description": "SpriteKit game template with ECS architecture",
                "priority": 5,
                "expected_files": ["GameScene.swift", "AppDelegate.swift", "GameViewController.swift"]
            },
            {
                "name": "xcode_automation",
                "description": "Real-time Xcode monitoring and build automation",
                "priority": 6,
                "expected_files": ["swift_mcp_monitor.py", "xcode_build_triggers.py"]
            }
        ]
        
        analyzed_groups = []
        
        for group in feature_groups:
            group_path = self.project_root / group["name"]
            
            analysis = {
                "name": group["name"],
                "description": group["description"],
                "priority": group["priority"],
                "exists": group_path.exists(),
                "status": "not_started"
            }
            
            if group_path.exists():
                # Count files
                python_files = list(group_path.glob("**/*.py"))
                swift_files = list(group_path.glob("**/*.swift"))
                total_files = list(group_path.glob("**/*"))
                total_files = [f for f in total_files if f.is_file()]
                
                analysis.update({
                    "python_files": len(python_files),
                    "swift_files": len(swift_files), 
                    "total_files": len(total_files),
                    "has_readme": (group_path / "README.md").exists(),
                    "has_tests": (group_path / "tests").exists()
                })
                
                # Check for expected files
                found_files = []
                missing_files = []
                
                for expected_file in group["expected_files"]:
                    found = False
                    for existing_file in total_files:
                        if expected_file in existing_file.name:
                            found_files.append(expected_file)
                            found = True
                            break
                    if not found:
                        missing_files.append(expected_file)
                
                analysis["found_files"] = found_files
                analysis["missing_files"] = missing_files
                
                # ENHANCED STATUS DETECTION - Check what's ACTUALLY implemented
                if group["name"] == "genetic_evolution":
                    # Check if genetic implementation exists elsewhere (LangGraph, main files)
                    chromosome_files = list(self.project_root.glob("**/chromosome*.py"))
                    evolution_files = list(self.project_root.glob("**/evolution*.py"))
                    if chromosome_files or evolution_files:
                        analysis["status"] = "complete"
                        analysis["implementation_location"] = "integrated_elsewhere"
                    elif len(found_files) == 0:
                        analysis["status"] = "structure_only"
                    else:
                        analysis["status"] = "in_progress"
                        
                elif group["name"] == "image_generation":
                    # Check if AI generation exists in ai_agents
                    visual_artist_files = list(self.project_root.glob("**/visual_artist*.py"))
                    if visual_artist_files:
                        analysis["status"] = "complete"
                        analysis["implementation_location"] = "ai_agents"
                    elif len(found_files) == 0:
                        analysis["status"] = "structure_only"
                    else:
                        analysis["status"] = "in_progress"
                        
                elif group["name"] == "ios_game_engine":
                    # Check if iOS game exists in main iOS directory
                    ios_main = self.project_root / "iOS"
                    if ios_main.exists() and len(list(ios_main.glob("**/*.swift"))) >= 10:
                        analysis["status"] = "complete"
                        analysis["implementation_location"] = "iOS_directory"
                    elif len(found_files) == 0:
                        analysis["status"] = "structure_only"
                    else:
                        analysis["status"] = "in_progress"
                        
                else:
                    # Original logic for other groups
                    if len(found_files) == 0:
                        analysis["status"] = "structure_only"
                    elif len(missing_files) == 0:
                        analysis["status"] = "complete"
                    else:
                        analysis["status"] = "in_progress"
            
            analyzed_groups.append(analysis)
        
        return analyzed_groups
    
    def _assess_implementation_status(self) -> Dict[str, Any]:
        """Assess ACTUAL implementation status with reality checks"""
        
        working_systems = []
        missing_systems = []
        
        # Project Context MCP
        context_server = self.project_root / "project_context_mcp" / "context_server.py"
        if context_server.exists():
            working_systems.append("Project Context MCP Server")
        else:
            missing_systems.append("Project Context MCP Server")
        
        # AI Agents - Check multiple locations
        ai_agents_langgraph = self.project_root / "LangGraph" / "agents"
        ai_agents_feature = self.project_root / "ai_agents"
        
        if (ai_agents_langgraph.exists() and len(list(ai_agents_langgraph.glob("*.py"))) >= 3) or \
           (ai_agents_feature.exists() and len(list(ai_agents_feature.glob("**/*.py"))) >= 3):
            working_systems.append("AI Agent Coordination")
        else:
            missing_systems.append("AI Agent Coordination")
        
        # Xcode Automation - Check XcodeMonitorMCP  
        xcode_mcp = self.project_root / "XcodeMonitorMCP"
        xcode_automation = self.project_root / "xcode_automation"
        
        if (xcode_mcp.exists() and len(list(xcode_mcp.glob("**/*.py"))) >= 5) or \
           (xcode_automation.exists() and len(list(xcode_automation.glob("**/*.py"))) >= 3):
            working_systems.append("Xcode Automation")
        else:
            missing_systems.append("Xcode Automation")
        
        # iOS Game Engine - Check main iOS directory
        ios_main = self.project_root / "iOS"
        ios_feature = self.project_root / "ios_game_engine"
        
        if (ios_main.exists() and len(list(ios_main.glob("**/*.swift"))) >= 10) or \
           (ios_feature.exists() and len(list(ios_feature.glob("**/*.swift"))) >= 3):
            working_systems.append("iOS Game Foundation")
        else:
            missing_systems.append("iOS Game Foundation")
        
        # Genetic Evolution - Check for implementation anywhere
        genetic_files = list(self.project_root.glob("**/chromosome*.py"))
        evolution_files = list(self.project_root.glob("**/evolution*.py"))
        
        if genetic_files or evolution_files:
            working_systems.append("Genetic Evolution Engine")
        else:
            missing_systems.append("Genetic Evolution Engine")
        
        # Image Generation - Check for AI integration
        visual_artist_files = list(self.project_root.glob("**/visual_artist*.py"))
        if visual_artist_files and any("openai" in str(f) or "stability" in str(f) for f in self.project_root.glob("**/*.py")):
            working_systems.append("AI Image Generation")
        else:
            missing_systems.append("AI Image Generation")
        
        return {
            "working_systems": working_systems,
            "missing_systems": missing_systems,
            "completion_percentage": len(working_systems) / (len(working_systems) + len(missing_systems)) * 100
        }
    
    def _calculate_overall_progress(self, feature_analysis: List[Dict]) -> Dict[str, Any]:
        """Calculate overall project progress"""
        
        total_groups = len(feature_analysis)
        complete_groups = len([g for g in feature_analysis if g["status"] == "complete"])
        in_progress_groups = len([g for g in feature_analysis if g["status"] == "in_progress"])
        structure_only_groups = len([g for g in feature_analysis if g["status"] == "structure_only"])
        
        progress_percentage = (complete_groups * 100 + in_progress_groups * 50 + structure_only_groups * 25) / (total_groups * 100) * 100
        
        return {
            "total_feature_groups": total_groups,
            "complete": complete_groups,
            "in_progress": in_progress_groups,
            "structure_only": structure_only_groups,
            "not_started": total_groups - complete_groups - in_progress_groups - structure_only_groups,
            "percentage": round(progress_percentage, 1)
        }
    
    def _get_next_priorities(self, feature_analysis: List[Dict]) -> List[str]:
        """Determine next development priorities based on ACTUAL status"""
        
        priorities = []
        
        # Check what's actually missing vs implemented elsewhere
        all_complete = all(g["status"] == "complete" for g in feature_analysis)
        
        if all_complete:
            priorities.extend([
                "Begin end-to-end integration testing",
                "Deploy LangGraph agents to Google Cloud",
                "Set up real Xcode MCP automation"
            ])
        else:
            # Find highest priority incomplete group
            incomplete_groups = [g for g in feature_analysis if g["status"] != "complete"]
            if incomplete_groups:
                next_group = min(incomplete_groups, key=lambda x: x["priority"])
                if next_group["status"] == "structure_only":
                    priorities.append(f"Implement {next_group['name']} core functionality")
                else:
                    priorities.append(f"Complete {next_group['name']} implementation")
        
        return priorities[:3]  # Return top 3 priorities
    
    def _assess_system_capabilities(self) -> Dict[str, str]:
        """Assess CURRENT system capabilities with reality checks"""
        
        capabilities = {}
        
        # Check MCP server
        if (self.project_root / "project_context_mcp" / "context_server.py").exists():
            capabilities["Project Context"] = "✅ Working MCP server with context preservation"
        else:
            capabilities["Project Context"] = "❌ MCP server not implemented"
        
        # Check AI agents - Check actual locations
        ai_agents_langgraph = self.project_root / "LangGraph" / "agents"
        ai_agents_feature = self.project_root / "ai_agents"
        
        agent_count = 0
        if ai_agents_langgraph.exists():
            agent_count += len(list(ai_agents_langgraph.glob("*.py")))
        if ai_agents_feature.exists():
            agent_count += len(list(ai_agents_feature.glob("**/*.py")))
            
        if agent_count >= 4:
            capabilities["AI Coordination"] = "✅ 4+ agent LangGraph system ready"
        elif agent_count >= 2:
            capabilities["AI Coordination"] = "🔄 Partial AI agent implementation"
        else:
            capabilities["AI Coordination"] = "❌ AI agents not fully implemented"
        
        # Check Xcode automation - Check actual locations
        xcode_mcp = self.project_root / "XcodeMonitorMCP"
        if xcode_mcp.exists() and len(list(xcode_mcp.glob("**/*.py"))) >= 5:
            capabilities["Xcode Automation"] = "✅ MCP server with build automation"
        else:
            capabilities["Xcode Automation"] = "❌ Xcode integration incomplete"
        
        # Check iOS game - Check main iOS directory
        ios_main = self.project_root / "iOS"
        if ios_main.exists() and len(list(ios_main.glob("**/*.swift"))) >= 10:
            capabilities["iOS Game Engine"] = "✅ SpriteKit template ready"
        else:
            capabilities["iOS Game Engine"] = "❌ iOS game template missing"
        
        # Check genetic evolution - Look for actual implementation
        genetic_files = list(self.project_root.glob("**/chromosome*.py"))
        evolution_files = list(self.project_root.glob("**/evolution*.py"))
        
        if genetic_files and evolution_files:
            capabilities["Genetic Evolution"] = "✅ Evolution engine implemented"
        elif genetic_files or evolution_files:
            capabilities["Genetic Evolution"] = "🔄 Partial genetic implementation"
        else:
            capabilities["Genetic Evolution"] = "❌ Core evolution engine missing"
        
        # Check image generation - Look for actual API integration
        visual_artist_files = list(self.project_root.glob("**/visual_artist*.py"))
        api_key_file = self.project_root / ".env"
        
        if visual_artist_files and api_key_file.exists():
            capabilities["Image Generation"] = "✅ DALL-E 3 + Stable Diffusion ready"
        else:
            capabilities["Image Generation"] = "❌ AI image generation not integrated"
        
        return capabilities
    
    def _get_architecture_summary(self) -> Dict[str, Any]:
        """Get high-level architecture summary"""
        
        return {
            "concept": "Autonomous game evolution using genetic algorithms and multi-agent AI",
            "core_components": [
                "17-parameter genetic chromosome system",
                "Multi-agent LangGraph coordination (Conceiver, Judge, Developer, Artist)",
                "Dual AI asset generation (DALL-E 3 + Stable Diffusion)", 
                "Automated iOS building via Xcode MCP",
                "Real-time analytics and fitness evaluation"
            ],
            "expected_scale": {
                "parameter_combinations": "131,072 (2^17)",
                "visual_combinations": "1M+ unique assets",
                "evolution_speed": "100+ variants per hour (target)",
                "autonomous_operation": "Minimal human intervention required"
            },
            "innovation": [
                "Games that evolve themselves to maximize player engagement",
                "Multi-modal evolution (gameplay + visuals simultaneously)",
                "Cost-optimized dual AI provider pipeline",
                "Real-time fitness evaluation without human testing"
            ]
        }
    
    def save_status_report(self, report: Dict[str, Any]) -> str:
        """Save status report to file"""
        
        # Save JSON version
        json_path = self.data_path / "platform_status_report.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown version
        markdown_content = self._generate_markdown_report(report)
        markdown_path = self.data_path / "platform_status_report.md"
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
        
        return str(markdown_path)
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown version of status report"""
        
        md = f"""# 🎮 AI Game Evolution Platform - ENHANCED Status Report

**Generated**: {report['generated_at'][:19]}

## 📊 Project Overview

**{report['project_overview']['name']}**  
{report['project_overview']['description']}

- **Total Files**: {report['project_overview']['total_files']}
- **Python Files**: {report['project_overview']['python_files']}  
- **Swift Files**: {report['project_overview']['swift_files']}
- **Overall Progress**: {report['project_overview']['overall_progress']['percentage']}%

## 🗂️ Feature Groups Status (Enhanced Analysis)

"""
        
        for group in report['feature_groups']:
            status_emoji = {
                "complete": "✅",
                "in_progress": "🔄", 
                "structure_only": "🏗️",
                "not_started": "❌"
            }.get(group['status'], "❓")
            
            md += f"### {status_emoji} **{group['name']}**\n"
            md += f"{group['description']}\n\n"
            
            if group['exists']:
                md += f"- **Files**: {group['total_files']} total ({group['python_files']} Python, {group['swift_files']} Swift)\n"
                md += f"- **README**: {'✅' if group['has_readme'] else '❌'}\n"
                md += f"- **Tests**: {'✅' if group['has_tests'] else '❌'}\n"
                
                if group.get('implementation_location'):
                    md += f"- **Implementation**: Found in {group['implementation_location']}\n"
                    
                if group.get('found_files'):
                    md += f"- **Found**: {', '.join(group['found_files'])}\n"
                if group.get('missing_files'):
                    md += f"- **Missing**: {', '.join(group['missing_files'])}\n"
            else:
                md += "- **Status**: Directory not found\n"
            
            md += "\n"
        
        md += f"""## 🚀 Implementation Status (Reality Check)

**Working Systems** ({len(report['implementation_status']['working_systems'])}):
"""
        for system in report['implementation_status']['working_systems']:
            md += f"- ✅ {system}\n"
        
        md += f"\n**Missing Systems** ({len(report['implementation_status']['missing_systems'])}):\n"
        for system in report['implementation_status']['missing_systems']:
            md += f"- ❌ {system}\n"
        
        md += f"\n**Completion**: {report['implementation_status']['completion_percentage']:.1f}%\n"
        
        md += f"""
## 🎯 Next Priorities (Updated)

"""
        for i, priority in enumerate(report['next_priorities'], 1):
            md += f"{i}. {priority}\n"
        
        md += f"""
## 🔧 System Capabilities (Enhanced)

"""
        for capability, status in report['system_capabilities'].items():
            md += f"**{capability}**: {status}\n"
        
        if report.get('git_status', {}).get('available'):
            git = report['git_status']
            md += f"""
## 📝 Git Status

- **Branch**: {git.get('branch', 'unknown')}
- **Clean**: {'Yes' if not git.get('is_dirty', True) else 'No'}
- **Last Commit**: {git.get('last_commit', {}).get('message', 'Unknown')[:100]}...
"""
        
        md += f"""
## 🏗️ Architecture Summary

**Vision**: {report['architecture_summary']['concept']}

**Core Components**:
"""
        for component in report['architecture_summary']['core_components']:
            md += f"- {component}\n"
        
        md += f"""
**Expected Scale**:
- Parameter combinations: {report['architecture_summary']['expected_scale']['parameter_combinations']}
- Visual combinations: {report['architecture_summary']['expected_scale']['visual_combinations']}
- Evolution speed: {report['architecture_summary']['expected_scale']['evolution_speed']}

**Innovation**:
"""
        for innovation in report['architecture_summary']['innovation']:
            md += f"- {innovation}\n"
        
        md += f"""
---

*Report auto-generated by Enhanced Project Context MCP Server*  
*Enhanced analysis checks multiple implementation locations*  
*Next update: When project changes are detected*
"""
        
        return md
