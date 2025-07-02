"""
Configuration management utilities
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load project configuration"""
    config_file = config_path / "project_config.json"
    
    default_config = {
        "project_name": "AI Game Evolution Platform",
        "current_phase": "Phase 1: Foundation & Integration",
        "active_feature_group": "unified_context_mcp",
        "feature_groups": [
            "project_context_mcp",
            "genetic_evolution", 
            "ai_agents",
            "image_generation",
            "ios_game_engine"
        ],
        "update_schedule": {
            "infrastructure_check": 3600,  # 1 hour
            "git_status_check": 300,       # 5 minutes
            "feature_rotation": 86400      # 24 hours
        }
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return default_config
    else:
        # Save default config
        config_path.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
