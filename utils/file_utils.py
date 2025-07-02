"""
File system utility functions for Project Context Server
"""
from pathlib import Path
from typing import List, Dict, Any
import subprocess


def should_ignore_file(file_path: Path) -> bool:
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


def get_all_project_files(project_root: Path) -> List[Path]:
    """Get all project files (excluding ignored ones)"""
    all_files = []
    for root, dirs, files in project_root.walk():
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not should_ignore_file(root / d)]
        
        for file in files:
            file_path = root / file
            if not should_ignore_file(file_path):
                all_files.append(file_path)
    
    return all_files


def analyze_project_structure(project_root: Path) -> Dict[str, Any]:
    """Analyze the project structure"""
    structure = {
        "directories": {},
        "file_types": {},
        "total_files": 0,
        "total_lines": 0
    }
    
    # Count files by directory and type
    for file_path in get_all_project_files(project_root):
        # Directory stats
        dir_name = file_path.parent.name
        if dir_name not in structure["directories"]:
            structure["directories"][dir_name] = 0
        structure["directories"][dir_name] += 1
        
        # File type stats
        ext = file_path.suffix or 'no_extension'
        if ext not in structure["file_types"]:
            structure["file_types"][ext] = 0
        structure["file_types"][ext] += 1
        
        structure["total_files"] += 1
        
        # Count lines for text files
        if ext in ['.py', '.swift', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.txt']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    structure["total_lines"] += sum(1 for _ in f)
            except:
                pass
    
    return structure


def count_lines_recursive(directory: Path, extensions: List[str]) -> int:
    """Count total lines of code in files with given extensions"""
    total_lines = 0
    for ext in extensions:
        result = subprocess.run(
            ['find', str(directory), '-name', f'*.{ext}', '-exec', 'wc', '-l', '{}', '+'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            # Parse wc output
            lines = result.stdout.strip().split('\n')
            if lines and 'total' in lines[-1]:
                total_lines += int(lines[-1].split()[0])
            elif lines and lines[0].strip():
                # Single file case
                try:
                    total_lines += int(lines[0].split()[0])
                except:
                    pass
    return total_lines
