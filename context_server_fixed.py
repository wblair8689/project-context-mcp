ago.days > 0:
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
        print(f"🚀 Starting Unified Project Context MCP Server")
        print(f"📁 Project Root: {args.project_root}")
        print(f"🔧 Debug: {args.debug}")
        
        server.run_server(transport=args.transport)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
