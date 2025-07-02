#!/usr/bin/env python3
"""Test if we can reload the server's modules"""
import sys
import importlib

# Add the project path to sys.path
sys.path.insert(0, '/Users/williamblair/AI-Game-Evolution-Platform/project_context_mcp')

# Try to reload specific modules
try:
    if 'context_server' in sys.modules:
        print("context_server is loaded, attempting reload...")
        importlib.reload(sys.modules['context_server'])
        print("Successfully reloaded context_server")
    else:
        print("context_server is not loaded")
        
    # List all loaded modules from the project
    project_modules = [name for name in sys.modules.keys() 
                      if 'project_context_mcp' in name or 
                      name in ['context_server', 'conversation_initializer', 
                               'build_diagnostics', 'build_monitor']]
    print(f"\nLoaded project modules: {project_modules}")
    
except Exception as e:
    print(f"Error: {e}")
