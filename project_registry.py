"""
Project Registry for managing multiple projects
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ProjectRegistry:
    """Manages multiple projects and their configurations"""
    
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_file = registry_path / "projects_registry.json"
        self.current_project_file = registry_path / "current_project.json"
        
        # Ensure directory exists
        registry_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize registry if it doesn't exist
        if not self.registry_file.exists():
            self._create_default_registry()
    
    def _create_default_registry(self):
        """Create default registry with common project examples"""
        default_registry = {
            "projects": {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.registry_file, 'w') as f:
            json.dump(default_registry, f, indent=2)
    
    def add_project(self, name: str, path: str, description: str = "", 
                   project_type: str = "general", xcode_enabled: bool = True) -> bool:
        """Add a new project to the registry"""
        try:
            registry = self.load_registry()
            
            # Validate path exists
            if not Path(path).exists():
                return False
            
            # Create project entry
            project_entry = {
                "name": name,
                "path": str(Path(path).resolve()),
                "description": description,
                "project_type": project_type,
                "xcode_enabled": xcode_enabled,
                "added_at": datetime.now().isoformat(),
                "last_accessed": None,
                "access_count": 0
            }
            
            registry["projects"][name] = project_entry
            registry["last_updated"] = datetime.now().isoformat()
            
            self._save_registry(registry)
            return True
            
        except Exception as e:
            print(f"Error adding project: {e}")
            return False
    
    def remove_project(self, name: str) -> bool:
        """Remove a project from the registry"""
        try:
            registry = self.load_registry()
            
            if name in registry["projects"]:
                del registry["projects"][name]
                registry["last_updated"] = datetime.now().isoformat()
                self._save_registry(registry)
                
                # If this was the current project, clear it
                current = self.get_current_project()
                if current and current.get("name") == name:
                    self.clear_current_project()
                
                return True
            return False
            
        except Exception as e:
            print(f"Error removing project: {e}")
            return False
    
    def list_projects(self) -> List[Dict]:
        """Get list of all registered projects"""
        registry = self.load_registry()
        projects = []
        
        for name, info in registry["projects"].items():
            projects.append({
                "name": name,
                "path": info["path"],
                "description": info.get("description", ""),
                "project_type": info.get("project_type", "general"),
                "xcode_enabled": info.get("xcode_enabled", True),
                "last_accessed": info.get("last_accessed"),
                "access_count": info.get("access_count", 0),
                "exists": Path(info["path"]).exists()
            })
        
        # Sort by access count (most used first), then by name
        projects.sort(key=lambda x: (-x["access_count"], x["name"]))
        return projects
    
    def get_project(self, name: str) -> Optional[Dict]:
        """Get project info by name"""
        registry = self.load_registry()
        if name in registry["projects"]:
            return registry["projects"][name]
        return None
    
    def set_current_project(self, name: str) -> bool:
        """Set the current active project"""
        project = self.get_project(name)
        if not project:
            return False
        
        try:
            # Update access tracking
            registry = self.load_registry()
            registry["projects"][name]["last_accessed"] = datetime.now().isoformat()
            registry["projects"][name]["access_count"] = registry["projects"][name].get("access_count", 0) + 1
            self._save_registry(registry)
            
            # Set as current
            current_project = {
                "name": name,
                "path": project["path"],
                "set_at": datetime.now().isoformat()
            }
            
            with open(self.current_project_file, 'w') as f:
                json.dump(current_project, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error setting current project: {e}")
            return False
    
    def get_current_project(self) -> Optional[Dict]:
        """Get the current active project"""
        try:
            if self.current_project_file.exists():
                with open(self.current_project_file, 'r') as f:
                    current = json.load(f)
                
                # Verify project still exists in registry
                if self.get_project(current["name"]):
                    return current
                else:
                    # Clean up invalid current project
                    self.clear_current_project()
            
            return None
            
        except Exception as e:
            print(f"Error getting current project: {e}")
            return None
    
    def clear_current_project(self):
        """Clear the current project selection"""
        try:
            if self.current_project_file.exists():
                os.remove(self.current_project_file)
        except Exception as e:
            print(f"Error clearing current project: {e}")
    
    def load_registry(self) -> Dict:
        """Load the projects registry"""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except Exception:
            self._create_default_registry()
            with open(self.registry_file, 'r') as f:
                return json.load(f)
    
    def _save_registry(self, registry: Dict):
        """Save the projects registry"""
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def auto_discover_projects(self, scan_paths: List[str] = None) -> List[Dict]:
        """Auto-discover potential projects in common locations"""
        if scan_paths is None:
            scan_paths = [
                "~/Projects",
                "~/Development", 
                "~/Developer",
                "~/Code",
                "/Users/Shared",
                "~/Desktop"
            ]
        
        discovered = []
        
        for path_str in scan_paths:
            path = Path(path_str).expanduser()
            if not path.exists():
                continue
            
            try:
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        # Check for common project indicators
                        project_type = self._detect_project_type(item)
                        if project_type:
                            discovered.append({
                                "name": item.name,
                                "path": str(item),
                                "project_type": project_type,
                                "description": f"Auto-discovered {project_type} project"
                            })
            except PermissionError:
                continue
        
        return discovered
    
    def _detect_project_type(self, path: Path) -> Optional[str]:
        """Detect the type of project based on files present"""
        # Check for common project files
        if (path / "package.json").exists():
            return "nodejs"
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "python"
        elif any(path.glob("*.xcodeproj")) or any(path.glob("*.xcworkspace")):
            return "xcode"
        elif (path / "Cargo.toml").exists():
            return "rust"
        elif (path / "go.mod").exists():
            return "go"
        elif (path / "pom.xml").exists() or (path / "build.gradle").exists():
            return "java"
        elif (path / ".git").exists():
            return "git"
        elif len(list(path.glob("*.py"))) > 0:
            return "python"
        elif len(list(path.glob("*.js"))) > 0 or len(list(path.glob("*.ts"))) > 0:
            return "javascript"
        
        return None
