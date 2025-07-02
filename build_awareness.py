"""
Enhanced Build Awareness Integration
Integrates build monitoring with project context
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from build_diagnostics import BuildDiagnosticsDB
from build_monitor import XcodeBuildMonitor

class BuildAwarenessManager:
    """Manages build awareness for the project context system"""
    
    def __init__(self, project_path: str, data_dir: Path):
        self.project_path = project_path
        self.data_dir = data_dir
        
        # Initialize components
        db_path = data_dir / "build_diagnostics.db"
        self.diagnostics_db = BuildDiagnosticsDB(db_path)
        self.build_monitor = XcodeBuildMonitor(project_path, self.diagnostics_db)
        
        # Set up monitoring
        self.build_monitor.add_build_callback(self._on_build_event)
        
        # Seed known solutions
        self._seed_known_solutions()
    
    def start_monitoring(self):
        """Start real-time build monitoring"""
        self.build_monitor.start_monitoring()
    
    def stop_monitoring(self):
        """Stop build monitoring"""
        self.build_monitor.stop_monitoring()
    
    def _on_build_event(self, build_info: Dict[str, Any]):
        """Handle build events"""
        logging.info(f"🔨 Build event: {build_info['status']} - {build_info['errors']} errors, {build_info['warnings']} warnings")
        
        # Update project status cache
        self._update_build_status_cache(build_info)
    
    def _update_build_status_cache(self, build_info: Dict[str, Any]):
        """Update cached build status for quick access"""
        status_file = self.data_dir / "current_build_status.json"
        
        status = {
            "last_build_time": datetime.now().isoformat(),
            "build_status": build_info['status'],
            "warnings_count": build_info['warnings'],
            "errors_count": build_info['errors'],
            "duration": build_info.get('duration'),
            "diagnostics": build_info.get('diagnostics', [])
        }
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def get_enhanced_build_status(self) -> Dict[str, Any]:
        """Get comprehensive build status with diagnostics insights"""
        # Get current status
        current_status = self._get_cached_build_status()
        
        # Get trends and analytics
        trends = self.diagnostics_db.get_build_trends(days=7)
        frequent_issues = self.diagnostics_db.get_frequent_issues(limit=5, days=7)
        
        # Get solutions for current errors
        current_solutions = []
        if current_status.get('diagnostics'):
            for diag in current_status['diagnostics']:
                if diag.get('severity') == 'error':
                    solution = self.diagnostics_db.get_solution_for_message(diag['message'])
                    if solution:
                        current_solutions.append({
                            'error': diag['message'],
                            'file': diag.get('file_path', ''),
                            'line': diag.get('line_number', 0),
                            'solution': solution['solution'],
                            'confidence': solution['success_count']
                        })
        
        return {
            "current_build": current_status,
            "build_health": {
                "success_rate_7d": f"{trends.get('success_rate', 0) * 100:.1f}%",
                "avg_build_time": f"{trends.get('avg_build_duration', 0):.1f}s" if trends.get('avg_build_duration') else "N/A",
                "total_builds_7d": trends.get('total_builds', 0),
                "status": self._get_health_status(trends)
            },
            "immediate_solutions": current_solutions,
            "frequent_issues": frequent_issues,
            "problematic_files": trends.get('problematic_files', []),
            "monitoring_active": self.build_monitor.is_monitoring
        }
    
    def _get_cached_build_status(self) -> Dict[str, Any]:
        """Get cached build status"""
        status_file = self.data_dir / "current_build_status.json"
        
        if status_file.exists():
            with open(status_file, 'r') as f:
                return json.load(f)
        
        return {
            "last_build_time": None,
            "build_status": "unknown",
            "warnings_count": 0,
            "errors_count": 0,
            "diagnostics": []
        }
    
    def _get_health_status(self, trends: Dict[str, Any]) -> str:
        """Determine overall build health status"""
        success_rate = trends.get('success_rate', 0)
        
        if success_rate >= 0.9:
            return "excellent"
        elif success_rate >= 0.7:
            return "good"
        elif success_rate >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def _seed_known_solutions(self):
        """Seed the database with known solutions"""
        known_solutions = [
            {
                "error": "Extra argument 'specifier' in call",
                "solution": "Replace string interpolation with String(format:). Change '\\(value, specifier: \"%.0f\")' to 'String(format: \"%.0f\", value)'",
                "pattern": r"\\([^,]+, specifier: \"[^\"]+\"\\)",
                "category": "string_formatting"
            },
            {
                "error": "Reference to captured var .* in concurrently-executing code",
                "solution": "Use immutable closure to build array before MainActor.run block, or ensure all mutations happen on MainActor",
                "pattern": r"Reference to captured var .* in concurrently-executing code",
                "category": "concurrency"
            },
            {
                "error": "Initialization of immutable value .* was never used; consider replacing with assignment to '_' or removing it",
                "solution": "Replace unused variable with underscore: 'let _ = value' or remove the assignment entirely",
                "pattern": r"Initialization of immutable value .* was never used",
                "category": "unused_code"
            },
            {
                "error": "Immutable value .* was never used; consider replacing with '_' or removing it",
                "solution": "Replace unused variable with underscore. For loop variables: 'for _ in 0..<count'",
                "pattern": r"Immutable value .* was never used",
                "category": "unused_code"
            }
        ]
        
        for solution_data in known_solutions:
            # Create a hash for the error pattern
            import hashlib
            message_hash = hashlib.md5(solution_data["error"].encode()).hexdigest()
            
            self.diagnostics_db.add_solution(
                message_hash=message_hash,
                solution_text=solution_data["solution"],
                fix_pattern=solution_data.get("pattern")
            )
    
    def record_manual_fix(self, error_message: str, solution_applied: str):
        """Record when a manual fix was successfully applied"""
        self.build_monitor.record_successful_fix(error_message, solution_applied)
        logging.info(f"✅ Recorded successful fix for: {error_message[:50]}...")
