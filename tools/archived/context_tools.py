"""
Context management MCP tools
"""
import json
from typing import Any, Optional
from datetime import datetime


def register_tools(server):
    """Register context management tools with the server"""
    
    @server.mcp.tool()
    async def initialize_conversation(trigger_phrase: Optional[str] = None) -> str:
        """Initialize conversation with full context"""
        try:
            context = server.conversation_initializer.initialize_new_conversation(trigger_phrase)
            return json.dumps(context, indent=2)
        except Exception as e:
            return f"Error initializing conversation: {str(e)}"
    
    @server.mcp.tool()
    async def generate_context_summary() -> str:
        """Generate comprehensive context summary"""
        try:
            # Get all status information
            infrastructure = server.infrastructure_checker.get_infrastructure_status()
            swift_status = server.swift_checker.get_swift_project_status()
            git_status = server.git_checker.get_git_status()
            
            summary = {
                "project": server.config.get("project_name", "Unknown"),
                "phase": server.config.get("current_phase", "Unknown"),
                "infrastructure_ready": sum(1 for s in infrastructure.values() if "✅" in s),
                "infrastructure_total": len(infrastructure),
                "swift_files": swift_status.get("swift_files_count", 0),
                "build_ready": "✅" in swift_status.get("build_server_status", ""),
                "git_branch": git_status.get("branch", "unknown"),
                "has_changes": git_status.get("is_dirty", False)
            }
            
            # Format as readable summary
            summary_text = f"""
Project: {summary['project']}
Phase: {summary['phase']}
Infrastructure: {summary['infrastructure_ready']}/{summary['infrastructure_total']} components ready
Swift Implementation: {summary['swift_files']} files
Build System: {'Ready' if summary['build_ready'] else 'Not configured'}
Git: {summary['git_branch']} branch {'(has changes)' if summary['has_changes'] else '(clean)'}
"""
            return summary_text.strip()
            
        except Exception as e:
            return f"Error generating context summary: {str(e)}"
    @server.mcp.tool()
    async def get_feature_group_status(group_name: str) -> str:
        """Get status of a specific feature group"""
        try:
            # Map group names to checker methods
            group_checkers = {
                "project_context_mcp": server.infrastructure_checker.check_project_context_mcp,
                "genetic_evolution": server.infrastructure_checker.check_genetic_evolution,
                "ai_agents": server.infrastructure_checker.check_ai_agents,
                "image_generation": server.infrastructure_checker.check_image_generation,
                "ios_game_engine": server.infrastructure_checker.check_ios_game_engine,
                "xcode_automation": server.infrastructure_checker.check_xcode_automation
            }
            
            if group_name not in group_checkers:
                return f"Unknown feature group: {group_name}. Valid groups: {', '.join(group_checkers.keys())}"
            
            status = group_checkers[group_name]()
            
            return json.dumps({
                "feature_group": group_name,
                "status": status,
                "is_active": group_name == server.config.get("active_feature_group", "")
            }, indent=2)
            
        except Exception as e:
            return f"Error getting feature group status: {str(e)}"
    
    @server.mcp.tool()
    async def update_project_phase(new_phase: str) -> str:
        """Update the current development phase"""
        try:
            # Update config
            server.config["current_phase"] = new_phase
            
            # Save config
            config_file = server.config_path / "project_config.json"
            with open(config_file, 'w') as f:
                json.dump(server.config, f, indent=2)
            
            return f"✅ Project phase updated to: {new_phase}"
            
        except Exception as e:
            return f"Error updating project phase: {str(e)}"
    
    @server.mcp.tool()
    async def store_session_context(context: str) -> str:
        """Store important context from current session"""
        try:
            # Load existing contexts
            contexts_file = server.data_path / "session_contexts.json"
            if contexts_file.exists():
                with open(contexts_file, 'r') as f:
                    contexts = json.load(f)
            else:
                contexts = []
            
            # Add new context
            contexts.append({
                "timestamp": datetime.now().isoformat(),
                "context": context
            })
            
            # Keep only last 10 contexts
            contexts = contexts[-10:]
            
            # Save
            with open(contexts_file, 'w') as f:
                json.dump(contexts, f, indent=2)
            
            return f"✅ Context stored successfully"
            
        except Exception as e:
            return f"Error storing session context: {str(e)}"
    
    @server.mcp.tool()
    async def get_previous_context() -> str:
        """Retrieve context from recent sessions"""
        try:
            contexts_file = server.data_path / "session_contexts.json"
            if not contexts_file.exists():
                return "No previous context found"
            
            with open(contexts_file, 'r') as f:
                contexts = json.load(f)
            
            if not contexts:
                return "No previous context found"
            
            # Format recent contexts
            result = "Recent session contexts:\n\n"
            for ctx in contexts[-3:]:  # Last 3 contexts
                timestamp = ctx['timestamp']
                context = ctx['context']
                result += f"**{timestamp}:**\n{context}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error retrieving previous context: {str(e)}"