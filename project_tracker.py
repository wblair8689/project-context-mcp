"""
Project Tracker - Monitors project state and file changes
"""

import os
import json
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class ProjectTracker:
    """Tracks project state, changes, and feature group status"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.repo = None
        
        # Try to initialize git repo
        if GIT_AVAILABLE:
            try:
                self.repo = git.Repo(self.project_root)
            except git.exc.InvalidGitRepositoryError:
                # Use logging instead of print to avoid corrupting MCP JSON-RPC
                import logging
                logging.getLogger(__name__).debug(f"Warning: {project_root} is not a git repository")
        else:
            # Use logging instead of print to avoid corrupting MCP JSON-RPC
            import logging
            logging.getLogger(__name__).debug("Warning: GitPython not available - git features disabled")
    
    def get_recent_commits(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent git commits"""
        if not self.repo:
            return []
        
        commits = []
        for commit in self.repo.iter_commits(max_count=limit):
            commits.append({
                "hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files)
            })
        
        return commits
    
    def get_project_status(self) -> Dict[str, Any]:
        """Get comprehensive project status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "git_status": self._get_git_status(),
            "feature_groups": self._scan_feature_groups(),
            "file_counts": self._get_file_counts(),
            "recent_activity": self.get_recent_commits(3)
        }
        
        return status
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get current git repository status"""
        if not self.repo:
            return {"available": False}
        
        return {
            "available": True,
            "branch": self.repo.active_branch.name,
            "is_dirty": self.repo.is_dirty(),
            "untracked_files": len(self.repo.untracked_files),
            "last_commit": {
                "hash": self.repo.head.commit.hexsha[:8],
                "message": self.repo.head.commit.message.strip(),
                "date": self.repo.head.commit.committed_datetime.isoformat()
            }
        }
    
    def _scan_feature_groups(self) -> List[Dict[str, Any]]:
        """Scan for feature group directories"""
        feature_groups = []
        
        # Expected feature groups
        expected_groups = [
            "project_context_mcp",
            "genetic_evolution", 
            "ai_agents",
            "image_generation", 
            "ios_game_engine",
            "xcode_automation"
        ]
        
        for group_name in expected_groups:
            group_path = self.project_root / group_name
            
            group_info = {
                "name": group_name,
                "exists": group_path.exists(),
                "path": str(group_path)
            }
            
            if group_path.exists():
                # Count files using the filtering logic
                python_files = 0
                total_files = 0
                
                for file_path in group_path.rglob("*"):
                    if file_path.is_file() and not self._should_ignore_file(file_path):
                        total_files += 1
                        if file_path.suffix.lower() == ".py":
                            python_files += 1
                
                group_info.update({
                    "has_readme": (group_path / "README.md").exists(),
                    "python_files": python_files,
                    "total_files": total_files,
                    "subdirectories": len([d for d in group_path.iterdir() if d.is_dir() and not self._should_ignore_file(d)])
                })
            
            feature_groups.append(group_info)
        
        return feature_groups
    
    def _get_file_counts(self) -> Dict[str, int]:
        """Get file type counts for the project"""
        counts = {
            "python": 0,
            "swift": 0,
            "markdown": 0,
            "json": 0,
            "total": 0
        }
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                counts["total"] += 1
                
                suffix = file_path.suffix.lower()
                if suffix == ".py":
                    counts["python"] += 1
                elif suffix == ".swift":
                    counts["swift"] += 1
                elif suffix == ".md":
                    counts["markdown"] += 1
                elif suffix == ".json":
                    counts["json"] += 1
        
        return counts
    
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
    
    def get_feature_group_details(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific feature group"""
        group_path = self.project_root / group_name
        
        if not group_path.exists():
            return None
        
        details = {
            "name": group_name,
            "path": str(group_path),
            "exists": True,
            "files": [],
            "structure": {}
        }
        
        # Get file listing
        for file_path in group_path.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                rel_path = file_path.relative_to(group_path)
                details["files"].append({
                    "name": file_path.name,
                    "path": str(rel_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return details
