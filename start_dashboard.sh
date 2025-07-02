#!/bin/bash
# Web Dashboard Startup Script
# Launches the AI Game Evolution Platform Web Dashboard

echo "🌐 AI Game Evolution Platform - Web Dashboard"
echo "=============================================="

# Change to the project context MCP directory
cd /Users/williamblair/AI-Game-Evolution-Platform/project_context_mcp

# Check if virtual environment exists
if [ ! -d "web_env" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv web_env
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source web_env/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import flask, flask_socketio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing web dependencies..."
    pip install flask flask-socketio
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Launch dashboard
echo ""
echo "🚀 Starting Web Dashboard..."
echo "📁 Project: AI Game Evolution Platform"
echo "🔗 URL: http://127.0.0.1:5000"
echo "💡 Open the URL in your browser to see the live dashboard"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Run the dashboard
python web_dashboard.py --project-root "/Users/williamblair/AI-Game-Evolution-Platform" --port 5000 --host 127.0.0.1
