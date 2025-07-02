#!/usr/bin/env python3
"""
Quick launcher for the Project Context Web Dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_socketio
        print("✅ Web dependencies are installed")
        return True
    except ImportError:
        print("❌ Missing web dependencies")
        return False

def install_dependencies():
    """Install required web dependencies"""
    requirements_file = Path(__file__).parent / "web_requirements.txt"
    if requirements_file.exists():
        print("📦 Installing web dependencies...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    else:
        print("❌ Requirements file not found")
        return False

def main():
    """Main launcher function"""
    print("🌐 AI Game Evolution Platform - Dashboard Launcher")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n📦 Installing required dependencies...")
        if not install_dependencies():
            print("❌ Could not install dependencies. Please run:")
            print("   pip install flask flask-socketio")
            sys.exit(1)
    
    # Import and run dashboard
    try:
        from web_dashboard import ProjectDashboard
        
        # Default configuration
        project_root = "/Users/williamblair/AI-Game-Evolution-Platform"
        port = 5000
        host = "127.0.0.1"
        
        print(f"\n🚀 Starting dashboard...")
        print(f"📁 Project: {project_root}")
        print(f"🔗 URL: http://{host}:{port}")
        print(f"🔄 Auto-refresh: 30 seconds")
        print("\n💡 Tip: The dashboard will update automatically as your project changes!")
        print("📱 Tip: Open the URL in your browser to see the live dashboard")
        print("\n🛑 Press Ctrl+C to stop the dashboard")
        print("-" * 60)
        
        # Create and run dashboard
        dashboard = ProjectDashboard(project_root, port)
        dashboard.run(debug=False, host=host)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project_context_mcp directory")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
