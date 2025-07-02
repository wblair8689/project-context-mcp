"""
Infrastructure checking functions
"""
import os
from pathlib import Path
from typing import Dict, List, Any
from utils.file_utils import count_lines_recursive


class InfrastructureChecker:
    """Checks various infrastructure components of the project"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def check_project_context_mcp(self) -> str:
        """Check project_context_mcp infrastructure"""
        mcp_path = self.project_root / "project_context_mcp"
        if not mcp_path.exists():
            return "❌ Not found"
        
        # Count Python files
        py_files = list(mcp_path.glob("**/*.py"))
        py_files = [f for f in py_files if "venv" not in str(f) and "web_env" not in str(f)]
        
        if len(py_files) >= 10:
            return f"✅ Complete ({len(py_files)} Python files)"
        else:
            return f"🟨 In progress ({len(py_files)} Python files)"
    
    def check_genetic_evolution(self) -> str:
        """Check genetic evolution system"""
        genetics_path = self.project_root / "genetic_evolution"
        if not genetics_path.exists():
            return "❌ Not found"
        
        # Check for key files
        key_files = ["gene_pool.py", "evolution_engine.py", "mutation_strategies.py"]
        found_files = sum(1 for f in key_files if (genetics_path / f).exists())
        
        # Count lines of genetic code
        genetic_lines = count_lines_recursive(genetics_path, ['py'])
        
        if found_files == len(key_files) and genetic_lines > 500:
            return f"✅ Complete ({genetic_lines} genetic code lines, {found_files}/{len(key_files)} key files)"
        else:
            return f"🟨 In progress ({genetic_lines} lines, {found_files}/{len(key_files)} key files)"
    
    def check_ai_agents(self) -> str:
        """Check AI agents infrastructure"""
        agents_path = self.project_root / "ai_agents"
        langgraph_path = self.project_root / "LangGraph"
        
        agent_files = 0
        if agents_path.exists():
            agent_files += len(list(agents_path.glob("**/*.py")))
        if langgraph_path.exists():
            agent_files += len(list(langgraph_path.glob("**/*.py")))
        
        if agent_files >= 10:
            # Count files from each directory
            ai_count = len(list(agents_path.glob("**/*.py"))) if agents_path.exists() else 0
            lg_count = len(list(langgraph_path.glob("**/*.py"))) if langgraph_path.exists() else 0
            return f"✅ Complete ({agent_files} agent files: {ai_count} ai_agents + {lg_count} LangGraph)"
        elif agent_files > 0:
            return f"🟨 In progress ({agent_files} agent files)"
        else:
            return "❌ Not found"

    def check_image_generation(self) -> str:
        """Check image generation infrastructure"""
        img_gen_path = self.project_root / "image_generation"
        if not img_gen_path.exists():
            return "❌ Not found"
        
        # Check for API integrations
        py_files = list(img_gen_path.glob("**/*.py"))
        api_keywords = ["openai", "dall", "stable", "midjourney", "api"]
        api_integrations = sum(1 for f in py_files 
                             for keyword in api_keywords 
                             if keyword in f.read_text().lower())
        
        if len(py_files) >= 3 and api_integrations >= 2:
            return f"✅ Complete ({len(py_files)} Python files, {min(3, api_integrations)}/3 API integrations)"
        else:
            return f"🟨 In progress ({len(py_files)} files, {api_integrations} API integrations)"
    
    def check_ios_game_engine(self) -> str:
        """Check iOS game engine infrastructure"""
        ios_path = self.project_root / "iOS"
        if not ios_path.exists():
            return "❌ Not found"
        
        # Count Swift files
        swift_files = list(ios_path.glob("**/*.swift"))
        
        # Check for Xcode projects
        xcode_projects = list(ios_path.glob("**/*.xcodeproj"))
        
        if len(swift_files) >= 50 and len(xcode_projects) >= 1:
            return f"✅ Complete ({len(swift_files)} Swift files, {len(xcode_projects)} Xcode projects)"
        else:
            return f"🟨 In progress ({len(swift_files)} Swift files, {len(xcode_projects)} Xcode projects)"
    
    def check_xcode_automation(self) -> str:
        """Check Xcode automation setup"""
        xcode_monitor = self.project_root / "xcode_build_server" / "xcode_monitor.py"
        
        if xcode_monitor.exists():
            return "✅ Complete (xcode_monitor.py present)"
        else:
            return "❌ Not configured"
    
    def get_infrastructure_status(self) -> Dict[str, str]:
        """Get status of all infrastructure components"""
        return {
            "project_context_mcp": self.check_project_context_mcp(),
            "genetic_evolution": self.check_genetic_evolution(),
            "ai_agents": self.check_ai_agents(),
            "image_generation": self.check_image_generation(),
            "ios_game_engine": self.check_ios_game_engine()
        }
