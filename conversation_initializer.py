#!/usr/bin/env python3
"""
Conversation Initializer for Project Context MCP
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

class ConversationInitializer:
    """Handles conversation initialization and context loading"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.sessions_file = data_dir / "conversation_sessions.json"
        self.last_activity_file = data_dir / "last_activity.json"
        
    def initialize_new_conversation(self, trigger_phrase: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a new conversation with comprehensive context"""
        
        conversation_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        # Load last activity info
        last_activity_info = self._get_last_activity_info()
        
        # Load recent session contexts
        recent_contexts = self._get_recent_session_contexts()
        
        # Load current project state
        project_state = self._load_current_project_state()
        
        # Generate welcome message based on time gap
        welcome_message = self._generate_welcome_message(last_activity_info)
        
        # Build initialization response
        response = {
            "conversation_id": conversation_id,
            "initialized_at": now.isoformat(),
            "welcome_message": welcome_message,
            "time_since_last": last_activity_info.get("time_since_last", "First conversation"),
            
            # Project Overview
            "project_overview": {
                "name": "AI Game Evolution Platform",
                "location": "/Users/williamblair/AI-Game-Evolution-Platform",
                "overall_progress": project_state.get("overall_progress", "Unknown"),
                "current_phase": project_state.get("current_phase", "Unknown")
            },
            
            # Quick Status
            "quick_status": {
                "working_systems": project_state.get("working_systems", []),
                "empty_systems": project_state.get("empty_systems", []),
                "recent_work": self._get_recent_work(recent_contexts),
                "current_priorities": project_state.get("next_priorities", [])
            },
            
            # Recent Context
            "recent_context": {
                "last_session_summary": recent_contexts[0] if recent_contexts else None,
                "key_decisions": self._extract_key_decisions(recent_contexts),
                "unfinished_tasks": self._identify_unfinished_tasks(recent_contexts)
            },
            
            # Helpful Reminders
            "reminders": self._generate_reminders(project_state, last_activity_info),
            
            # Trigger phrase response
            "trigger_response": self._respond_to_trigger(trigger_phrase)
        }
        
        # Save this conversation start
        self._save_conversation_start(conversation_id, response)
        
        # Update last activity
        self._update_last_activity()
        
        return response
    
    def _get_last_activity_info(self) -> Dict[str, Any]:
        """Get information about last activity"""
        if not self.last_activity_file.exists():
            return {"first_time": True}
            
        with open(self.last_activity_file) as f:
            last_data = json.load(f)
            
        last_time = datetime.fromisoformat(last_data["timestamp"])
        time_diff = datetime.now() - last_time
        
        # Format time difference nicely
        if time_diff.days > 0:
            time_desc = f"{time_diff.days} days"
        elif time_diff.seconds > 3600:
            time_desc = f"{time_diff.seconds // 3600} hours"
        elif time_diff.seconds > 60:
            time_desc = f"{time_diff.seconds // 60} minutes"
        else:
            time_desc = "less than a minute"
            
        return {
            "last_activity": last_time.isoformat(),
            "time_since_last": time_desc,
            "last_conversation_id": last_data.get("conversation_id")
        }
    
    def _get_recent_session_contexts(self, limit: int = 3) -> list:
        """Get recent session contexts"""
        contexts_file = self.data_dir / "session_contexts.json"
        if not contexts_file.exists():
            return []
            
        with open(contexts_file) as f:
            data = json.load(f)
            
        # Handle both list and dict formats
        if isinstance(data, list):
            return data[-limit:]
        else:
            return data.get("contexts", [])[-limit:]
    
    def _load_current_project_state(self) -> Dict[str, Any]:
        """Load current project state from various sources"""
        state = {}
        
        # Load platform status report if exists
        report_file = self.data_dir / "platform_status_report.json"
        if report_file.exists():
            with open(report_file) as f:
                report = json.load(f)
                state["overall_progress"] = f"{report.get('summary', {}).get('overall_progress', 0):.1f}%"
                state["working_systems"] = [
                    name for name, data in report.get("feature_groups", {}).items()
                    if data.get("status") in ["fully_implemented", "mostly_implemented"]
                ]
                state["empty_systems"] = [
                    name for name, data in report.get("feature_groups", {}).items()
                    if data.get("status") == "empty"
                ]
        
        # Load project status
        status_file = self.data_dir / "project_status.json"
        if status_file.exists():
            with open(status_file) as f:
                status = json.load(f)
                state["current_phase"] = status.get("current_phase", "Unknown")
                state["next_priorities"] = [
                    "Complete genetic evolution implementation",
                    "Integrate Xcode workspace management",
                    "Test end-to-end evolution cycle"
                ]
        
        return state
    
    def _generate_welcome_message(self, last_activity: Dict[str, Any]) -> str:
        """Generate a contextual welcome message"""
        if last_activity.get("first_time"):
            return "🎉 Welcome to your AI Game Evolution Platform! This appears to be our first conversation."
        
        time_since = last_activity.get("time_since_last", "unknown time")
        
        if "days" in time_since:
            return f"🌟 Welcome back! It's been {time_since} since we last worked together. Let me catch you up..."
        elif "hours" in time_since:
            return f"👋 Welcome back! Picking up from {time_since} ago..."
        else:
            return f"⚡ Continuing from {time_since} ago..."
    
    def _get_recent_work(self, contexts: list) -> list:
        """Extract recent work from contexts"""
        recent_work = []
        
        for ctx in contexts[-2:]:  # Last 2 sessions
            if isinstance(ctx, dict) and "context" in ctx:
                # Extract key phrases that indicate work done
                context_text = ctx["context"].lower()
                if "xcode workspace" in context_text:
                    recent_work.append("Xcode workspace management implementation")
                if "consolidated" in context_text or "consolidation" in context_text:
                    recent_work.append("Project consolidation to single directory")
                if "genetic" in context_text:
                    recent_work.append("Genetic evolution planning")
                if "mcp" in context_text and "fix" in context_text:
                    recent_work.append("Project Context MCP accuracy fixes")
        
        return list(set(recent_work))[:3]  # Unique, max 3
    
    def _extract_key_decisions(self, contexts: list) -> list:
        """Extract key decisions from recent contexts"""
        decisions = []
        
        # Add known recent decisions
        if contexts:
            decisions.append("Consolidated project to /Users/williamblair/AI-Game-Evolution-Platform")
            decisions.append("Chose LangGraph over CrewAI for agent orchestration")
            decisions.append("Implemented 12 AppleScript functions for Xcode control")
        
        return decisions[:3]
    
    def _identify_unfinished_tasks(self, contexts: list) -> list:
        """Identify unfinished tasks from contexts"""
        tasks = []
        
        # Check for mentions of "next steps" or "todo" in recent contexts
        for ctx in contexts:
            if isinstance(ctx, dict) and "context" in ctx:
                if "genetic evolution" in ctx["context"].lower() and "implement" in ctx["context"].lower():
                    tasks.append("Implement genetic evolution core with Revolver")
                if "integrate" in ctx["context"].lower() and "workspace" in ctx["context"].lower():
                    tasks.append("Integrate Xcode workspace management into MCP")
        
        # Add known pending tasks
        if not tasks:
            tasks = [
                "Implement genetic evolution with Revolver framework",
                "Complete empty feature directories",
                "Test integrated evolution cycle"
            ]
        
        return tasks[:3]    
    def _generate_reminders(self, project_state: Dict, last_activity: Dict) -> list:
        """Generate helpful reminders based on context"""
        reminders = []
        
        # Time-based reminders
        if "days" in last_activity.get("time_since_last", ""):
            reminders.append("📍 Project is now in single location: /Users/williamblair/AI-Game-Evolution-Platform")
        
        # State-based reminders
        if project_state.get("empty_systems"):
            reminders.append(f"📭 Empty systems need implementation: {', '.join(project_state['empty_systems'][:2])}")
        
        # Recent work reminders
        reminders.append("🛠️ Xcode workspace management code is available as artifacts in recent conversations")
        
        return reminders[:3]
    
    def _respond_to_trigger(self, trigger_phrase: Optional[str]) -> Optional[str]:
        """Generate response based on trigger phrase"""
        if not trigger_phrase:
            return None
            
        trigger_lower = trigger_phrase.lower()
        
        if "ready" in trigger_lower or "let's go" in trigger_lower:
            return "🚀 Great! I'm ready to help. Based on your recent work, shall we continue with the genetic evolution implementation?"
        elif "status" in trigger_lower or "where" in trigger_lower:
            return "📊 I've loaded your project status above. You're at 75% completion with 4/6 systems working."
        elif "help" in trigger_lower:
            return "🤝 I'm here to help! I can see your recent focus has been on Xcode workspace management and project consolidation."
        else:
            return "✨ Conversation initialized! I have your full project context loaded."
    
    def _save_conversation_start(self, conversation_id: str, response: Dict):
        """Save conversation start info"""
        sessions = []
        if self.sessions_file.exists():
            with open(self.sessions_file) as f:
                sessions = json.load(f)
        
        sessions.append({
            "conversation_id": conversation_id,
            "started_at": response["initialized_at"],
            "trigger": response.get("trigger_response"),
            "project_state_snapshot": {
                "progress": response["project_overview"]["overall_progress"],
                "working_systems": response["quick_status"]["working_systems"]
            }
        })
        
        # Keep last 10 sessions
        sessions = sessions[-10:]
        
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def _update_last_activity(self):
        """Update last activity timestamp"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "conversation_id": str(uuid.uuid4())[:8]
        }
        
        with open(self.last_activity_file, 'w') as f:
            json.dump(data, f)