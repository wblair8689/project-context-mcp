"""
Swift and Xcode project checking functions
"""
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional


class SwiftProjectChecker:
    """Checks Swift/Xcode project status and configuration"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ios_path = project_root / "iOS"
    
    def find_xcode_projects(self) -> List[str]:
        """Find all Xcode projects"""
        if not self.ios_path.exists():
            return []
        
        projects = []
        for proj in self.ios_path.glob("**/*.xcodeproj"):
            projects.append(str(proj))
        for work in self.ios_path.glob("**/*.xcworkspace"):
            projects.append(str(work))
        
        return projects
    
    def find_swift_files(self) -> List[str]:
        """Find all Swift files"""
        if not self.ios_path.exists():
            return []
        
        swift_files = []
        for swift_file in self.ios_path.glob("**/*.swift"):
            # Skip certain directories
            if any(skip in str(swift_file) for skip in ['.build', 'DerivedData', 'Pods']):
                continue
            swift_files.append(str(swift_file))
        
        return swift_files
    
    def check_ios_template(self) -> str:
        """Check if iOS template is ready"""
        swift_files = self.find_swift_files()
        
        if len(swift_files) >= 50:
            return f"✅ Ready ({len(swift_files)} template files)"
        elif len(swift_files) > 0:
            return f"🟨 In progress ({len(swift_files)} files)"
        else:
            return "❌ Not found"

    def check_build_server(self) -> str:
        """Check if build server is configured"""
        build_server_json = self.project_root / "iOS" / "buildServer.json"
        xcode_build_server = self.project_root / "xcode_build_server"
        
        if build_server_json.exists():
            return "✅ Build server configured"
        elif xcode_build_server.exists():
            return "🟨 Build server present but not configured"
        else:
            return "❌ No build server configuration found"
    
    def get_last_build_info(self) -> str:
        """Get last build information"""
        # Check for build logs
        build_log_paths = [
            self.project_root / "iOS" / "build.log",
            self.project_root / "iOS" / ".build" / "last_build.log",
            self.project_root / "xcode_build_logs"
        ]
        
        for log_path in build_log_paths:
            if log_path.exists():
                if log_path.is_file():
                    # Get file modification time
                    import os
                    from datetime import datetime
                    mtime = os.path.getmtime(log_path)
                    last_build = datetime.fromtimestamp(mtime)
                    return f"✅ Last build: {last_build.strftime('%Y-%m-%d %H:%M')}"
                elif log_path.is_dir():
                    # Check for log files in directory
                    logs = list(log_path.glob("*.log"))
                    if logs:
                        return f"✅ Build logs found ({len(logs)} logs)"
        
        return "❌ No build logs found"
    
    def get_build_status(self) -> str:
        """Get current build status"""
        # This would normally check actual build status
        # For now, return based on available information
        if self.check_build_server().startswith("✅"):
            return "🟢 Build system ready"
        else:
            return "🔴 Build system not configured"
    
    def get_swift_project_status(self) -> Dict[str, Any]:
        """Get comprehensive Swift project status"""
        return {
            "xcode_projects": self.find_xcode_projects(),
            "swift_files_count": len(self.find_swift_files()),
            "ios_template_ready": self.check_ios_template(),
            "build_server_status": self.check_build_server(),
            "last_build": self.get_last_build_info()
        }
