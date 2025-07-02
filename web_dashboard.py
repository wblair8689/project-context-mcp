"""
Web Dashboard for Project Context MCP Server
Real-time project status visualization with live updates
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import os
import sys

# Add project context MCP to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from context_server import UnifiedProjectContextServer

class ProjectDashboard:
    def __init__(self, project_root: str, port: int = 5000):
        self.project_root = project_root
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'project-context-dashboard-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize project context server
        self.context_server = UnifiedProjectContextServer(project_root)
        
        # Dashboard state
        self.dashboard_data = {}
        self.update_interval = 30  # seconds
        self.last_update = None
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio()
        
        # Start background update thread
        self.update_thread = threading.Thread(target=self._background_updates, daemon=True)
        self.update_thread.start()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for current project status"""
            try:
                return jsonify(self._get_dashboard_data())
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/refresh')
        def api_refresh():
            """Force refresh project data"""
            try:
                self._update_dashboard_data()
                return jsonify({"success": True, "last_update": self.last_update})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/history')
        def api_history():
            """Get project history/timeline"""
            try:
                history = self._get_project_history()
                return jsonify(history)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/readme/<feature_group>')
        def api_readme(feature_group):
            """Get README content for a specific feature group"""
            try:
                readme_path = Path(self.project_root) / feature_group / "README.md"
                if readme_path.exists():
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return jsonify({
                        "success": True,
                        "feature_group": feature_group,
                        "content": content,
                        "exists": True
                    })
                else:
                    return jsonify({
                        "success": False,
                        "feature_group": feature_group,
                        "error": "README.md not found",
                        "exists": False
                    }), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def _setup_socketio(self):
        """Setup WebSocket events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Client connected"""
            print(f"📱 Client connected: {request.sid}")
            # Send current data to new client
            emit('status_update', self._get_dashboard_data())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Client disconnected"""
            print(f"📱 Client disconnected: {request.sid}")
        
        @self.socketio.on('request_refresh')
        def handle_refresh():
            """Client requested refresh"""
            self._update_dashboard_data()
            self.socketio.emit('status_update', self.dashboard_data)
    
    def _get_dashboard_data(self) -> dict:
        """Get comprehensive dashboard data"""
        if not self.dashboard_data or self._needs_update():
            self._update_dashboard_data()
        return self.dashboard_data
    
    def _update_dashboard_data(self):
        """Update dashboard data from project context server"""
        try:
            # Get infrastructure and implementation status
            infra_status = self.context_server._get_infrastructure_status()
            swift_status = self.context_server._get_swift_project_status()
            git_status = self.context_server._get_git_status()
            
            # Calculate metrics
            readiness = self.context_server._calculate_overall_readiness(infra_status, swift_status)
            next_steps = self.context_server._get_next_steps(infra_status, swift_status)
            
            # Get project structure
            structure = self.context_server._analyze_project_structure()
            
            # Build comprehensive dashboard data
            self.dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "project_name": self.context_server.config["project_name"],
                "current_phase": self.context_server.config["current_phase"],
                "overall_readiness": readiness,
                
                "infrastructure": {
                    "status": infra_status,
                    "completion_percentage": self._calculate_infra_percentage(infra_status),
                    "total_groups": len(infra_status),
                    "complete_groups": sum(1 for status in infra_status.values() if "Complete" in str(status))
                },
                
                "implementation": {
                    "status": swift_status,
                    "xcode_projects_count": len(swift_status.get("xcode_projects", [])),
                    "swift_files_count": swift_status.get("swift_files_count", 0),
                    "completion_percentage": self._calculate_impl_percentage(swift_status)
                },
                
                "project_structure": structure,
                
                "git": git_status,
                
                "next_steps": next_steps,
                
                "health_indicators": self._get_health_indicators(infra_status, swift_status),
                
                "recent_activity": self._get_recent_activity()
            }
            
            self.last_update = datetime.now().isoformat()
            
        except Exception as e:
            print(f"❌ Error updating dashboard data: {e}")
            self.dashboard_data = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_infra_percentage(self, infra_status: dict) -> float:
        """Calculate infrastructure completion percentage"""
        if not infra_status:
            return 0.0
        complete = sum(1 for status in infra_status.values() if "Complete" in str(status))
        return (complete / len(infra_status)) * 100
    
    def _calculate_impl_percentage(self, swift_status: dict) -> float:
        """Calculate implementation completion percentage"""
        score = 0
        if swift_status.get("xcode_projects"):
            score += 25
        if swift_status.get("swift_files_count", 0) > 0:
            score += 25
        if "Ready" in str(swift_status.get("ios_template_ready", "")):
            score += 25
        if "configured" in str(swift_status.get("build_server_status", "")):
            score += 25
        return score
    
    def _get_health_indicators(self, infra_status: dict, swift_status: dict) -> dict:
        """Get project health indicators"""
        health = {
            "overall": "good",
            "issues": [],
            "warnings": [],
            "strengths": []
        }
        
        # Check for issues
        incomplete_infra = [group for group, status in infra_status.items() if "Missing" in str(status)]
        if incomplete_infra:
            health["issues"].append(f"Missing infrastructure: {', '.join(incomplete_infra)}")
        
        if not swift_status.get("xcode_projects"):
            health["issues"].append("No Xcode projects found")
        
        if "not" in swift_status.get("build_server_status", "").lower():
            health["warnings"].append("Build server not configured")
        
        # Check for strengths
        if len(swift_status.get("xcode_projects", [])) > 5:
            health["strengths"].append(f"{len(swift_status.get('xcode_projects', []))} Xcode projects available")
        
        if swift_status.get("swift_files_count", 0) > 20:
            health["strengths"].append(f"{swift_status.get('swift_files_count')} Swift files implemented")
        
        # Determine overall health
        if health["issues"]:
            health["overall"] = "critical" if len(health["issues"]) > 2 else "warning"
        elif health["warnings"]:
            health["overall"] = "warning"
        else:
            health["overall"] = "excellent"
        
        return health
    
    def _get_recent_activity(self) -> list:
        """Get recent project activity"""
        activities = []
        
        # Check recent file modifications
        try:
            import subprocess
            result = subprocess.run([
                'git', 'log', '--oneline', '-10', '--since=7 days ago'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        hash_msg = line.strip().split(' ', 1)
                        if len(hash_msg) == 2:
                            activities.append({
                                "type": "commit",
                                "description": hash_msg[1],
                                "hash": hash_msg[0],
                                "timestamp": "recent"  # Could enhance with actual timestamp
                            })
        except:
            pass
        
        return activities[:5]  # Last 5 activities
    
    def _get_project_history(self) -> dict:
        """Get project development history"""
        return {
            "milestones": [
                {"date": "2024-12", "title": "Project Inception", "status": "completed"},
                {"date": "2025-01", "title": "Core Infrastructure", "status": "completed"},
                {"date": "2025-02", "title": "AI Agents Implementation", "status": "completed"},
                {"date": "2025-03", "title": "iOS Game Engine", "status": "completed"},
                {"date": "2025-04", "title": "Integration & Testing", "status": "in_progress"},
                {"date": "2025-05", "title": "Production Deployment", "status": "planned"}
            ],
            "feature_timeline": [
                {"feature": "Project Context MCP", "completed": "2025-01-15"},
                {"feature": "Genetic Evolution", "completed": "2025-02-01"},
                {"feature": "AI Agents (LangGraph)", "completed": "2025-02-15"},
                {"feature": "Image Generation", "completed": "2025-03-01"},
                {"feature": "iOS Game Engine", "completed": "2025-03-15"},
                {"feature": "Xcode Automation", "completed": "2025-04-01"}
            ]
        }
    
    def _needs_update(self) -> bool:
        """Check if dashboard data needs updating"""
        if not self.last_update:
            return True
        
        last_update_time = datetime.fromisoformat(self.last_update.replace('Z', '+00:00').replace('+00:00', ''))
        return (datetime.now() - last_update_time).seconds > self.update_interval
    
    def _background_updates(self):
        """Background thread for periodic updates"""
        while True:
            try:
                time.sleep(self.update_interval)
                if self._needs_update():
                    old_data = self.dashboard_data.copy()
                    self._update_dashboard_data()
                    
                    # Emit update to all connected clients
                    if self.dashboard_data != old_data:
                        self.socketio.emit('status_update', self.dashboard_data)
                        print(f"📡 Dashboard updated and broadcasted at {datetime.now()}")
            except Exception as e:
                print(f"❌ Background update error: {e}")
    
    def run(self, debug: bool = False, host: str = '127.0.0.1'):
        """Run the web dashboard"""
        print(f"🌐 Starting Project Context Dashboard")
        print(f"📁 Project: {self.project_root}")
        print(f"🔗 URL: http://{host}:{self.port}")
        print(f"🔄 Auto-refresh: {self.update_interval}s")
        
        self.socketio.run(
            self.app, 
            host=host, 
            port=self.port, 
            debug=debug,
            allow_unsafe_werkzeug=True
        )


def main():
    """Main entry point for the dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Context Web Dashboard")
    parser.add_argument("--project-root", 
                       default="/Users/williamblair/AI-Game-Evolution-Platform",
                       help="Root directory of the project")
    parser.add_argument("--port", type=int, default=5000, help="Web server port")
    parser.add_argument("--host", default="127.0.0.1", help="Web server host")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--update-interval", type=int, default=30, help="Update interval in seconds")
    
    args = parser.parse_args()
    
    # Create and run dashboard
    dashboard = ProjectDashboard(args.project_root, args.port)
    dashboard.update_interval = args.update_interval
    
    try:
        dashboard.run(debug=args.debug, host=args.host)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")


if __name__ == "__main__":
    main()
