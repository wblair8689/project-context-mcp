"""
Test the Project Tracker functionality
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_tracker import ProjectTracker

def test_project_tracker():
    """Test basic project tracker functionality"""
    
    # Use the actual project root
    project_root = Path(__file__).parent.parent.parent
    tracker = ProjectTracker(str(project_root))
    
    print("🧪 Testing Project Tracker")
    print(f"📁 Project Root: {project_root}")
    
    # Test getting project status
    print("\n📊 Getting project status...")
    status = tracker.get_project_status()
    
    print(f"✅ Git available: {status['git_status']['available']}")
    print(f"📝 Total files: {status['file_counts']['total']}")
    print(f"🐍 Python files: {status['file_counts']['python']}")
    print(f"📱 Swift files: {status['file_counts']['swift']}")
    
    # Test feature group scanning
    print(f"\n🗂️ Feature groups found: {len(status['feature_groups'])}")
    for group in status['feature_groups']:
        exists_indicator = "✅" if group['exists'] else "❌"
        readme_indicator = "📝" if group.get('has_readme') else "❌"
        print(f"  {exists_indicator} {group['name']} {readme_indicator}")
    
    # Test recent commits
    print(f"\n📝 Recent commits: {len(status['recent_activity'])}")
    for commit in status['recent_activity'][:2]:
        print(f"  🔹 {commit['hash']}: {commit['message'][:50]}...")
    
    # Test feature group details
    print(f"\n🔍 Testing feature group details...")
    details = tracker.get_feature_group_details("project_context_mcp")
    if details:
        print(f"  📁 Files in project_context_mcp: {len(details['files'])}")
        for file_info in details['files'][:3]:
            print(f"    📄 {file_info['name']}")
    else:
        print("  ❌ Could not get feature group details")
    
    print("\n🎉 Project Tracker test completed!")
    return True

if __name__ == "__main__":
    test_project_tracker()
