"""
Git status checking utilities
"""
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class GitStatusChecker:
    """Checks Git repository status"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def get_git_status(self) -> Dict[str, Any]:
        """Get current git status"""
        try:
            # Check if git repo exists
            git_dir = self.project_root / ".git"
            if not git_dir.exists():
                return {"available": False, "message": "Not a git repository"}
            
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            is_dirty = bool(status_result.stdout.strip()) if status_result.returncode == 0 else True
            
            # Count untracked files
            untracked = len([line for line in status_result.stdout.split('\n') if line.startswith('??')])
            
            # Get last commit info
            log_result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%h|%s|%ad", "--date=format:%Y-%m-%d %H:%M:%S %z"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            last_commit = {}
            if log_result.returncode == 0 and log_result.stdout:
                parts = log_result.stdout.strip().split('|')
                if len(parts) == 3:
                    last_commit = {
                        "hash": parts[0],
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
