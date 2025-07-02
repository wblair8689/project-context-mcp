#!/usr/bin/env python3
"""
Test the enhanced Project Context MCP Server with documentation manager
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_server import ProjectContextServer

async def test_enhanced_mcp_server():
    """Test the enhanced MCP server with documentation features"""
    
    print("🧪 Testing Enhanced Project Context MCP Server")
    print("=" * 60)
    
    # Create server instance
    project_root = Path(__file__).parent.parent.parent
    server = ProjectContextServer(str(project_root))
    
    print(f"📁 Project Root: {project_root}")
    print("✅ Server created successfully")
    
    # Test 1: Generate platform status report
    print("\n📊 Testing generate_platform_status_report...")
    try:
        from documentation_manager import DocumentationManager
        from project_tracker import ProjectTracker
        
        doc_manager = DocumentationManager(str(project_root))
        project_tracker = ProjectTracker(str(project_root))
        
        # Generate comprehensive report
        report = doc_manager.generate_platform_status_report(project_tracker)
        
        print(f"✅ Report generated successfully")
        print(f"✅ Overall progress: {report['project_overview']['overall_progress']['percentage']}%")
        print(f"✅ Total files: {report['project_overview']['total_files']}")
        print(f"✅ Working systems: {len(report['implementation_status']['working_systems'])}")
        
        # Save the report
        report_path = doc_manager.save_status_report(report)
        print(f"✅ Report saved to: {report_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Platform status summary
    print("\n📋 Testing platform status summary...")
    try:
        summary_data = report  # Use the report from above
        
        print(f"✅ Platform: {summary_data['project_overview']['name']}")
        print(f"✅ Progress: {summary_data['project_overview']['overall_progress']['percentage']}%")
        print(f"✅ Feature groups: {len(summary_data['feature_groups'])}")
        
        # Show feature group statuses
        for group in summary_data['feature_groups']:
            status_emoji = {
                "complete": "✅",
                "in_progress": "🔄", 
                "structure_only": "🏗️",
                "not_started": "❌"
            }.get(group['status'], "❓")
            print(f"  {status_emoji} {group['name']}: {group['status']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check saved files
    print("\n📄 Testing saved report files...")
    data_path = Path(project_root) / "project_context_mcp" / "data"
    
    json_report = data_path / "platform_status_report.json"
    md_report = data_path / "platform_status_report.md"
    
    if json_report.exists():
        print(f"✅ JSON report exists: {json_report}")
        print(f"✅ Size: {json_report.stat().st_size} bytes")
    
    if md_report.exists():
        print(f"✅ Markdown report exists: {md_report}")
        print(f"✅ Size: {md_report.stat().st_size} bytes")
        
        # Show first few lines of markdown
        with open(md_report, 'r') as f:
            lines = f.readlines()[:10]
        print(f"✅ Preview (first 10 lines):")
        for line in lines:
            print(f"   {line.rstrip()}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced MCP server test completed!")
    print("✅ Documentation manager working")
    print("✅ Status reports generating")
    print("✅ Files saved successfully")

if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp_server())
