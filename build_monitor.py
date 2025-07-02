"""
Build Monitor - Real-time Xcode build tracking
"""

import subprocess
import json
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import threading
from build_diagnostics import BuildDiagnosticsDB

class XcodeBuildMonitor:
    """Monitors Xcode builds and captures diagnostics in real-time"""
    
    def __init__(self, project_path: str, diagnostics_db: BuildDiagnosticsDB):
        self.project_path = Path(project_path)
        self.diagnostics_db = diagnostics_db
        self.current_build_id = None
        self.build_start_time = None
        self.is_monitoring = False
        self.callbacks = []
        
        # Xcode log patterns
        self.error_pattern = re.compile(r'(.+?):(\d+):(\d+): error: (.+)')
        self.warning_pattern = re.compile(r'(.+?):(\d+):(\d+): warning: (.+)')
        self.build_start_pattern = re.compile(r'Build target (\w+)')
        self.build_end_pattern = re.compile(r'BUILD (SUCCEEDED|FAILED)')
    
    def add_build_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback to be called on build events"""
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """Start monitoring Xcode builds"""
        self.is_monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Check for recent build activity
                self._check_build_logs()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logging.error(f"Build monitor error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _check_build_logs(self):
        """Check Xcode derived data for recent build logs"""
        try:
            # Get Xcode derived data path
            result = subprocess.run([
                'defaults', 'read', 'com.apple.dt.Xcode', 'IDEApplicationwideBuildSettings'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                # Default path if can't read settings
                derived_data = Path.home() / "Library/Developer/Xcode/DerivedData"
            else:
                # Parse derived data path from settings
                derived_data = Path.home() / "Library/Developer/Xcode/DerivedData"
            
            # Find recent build logs
            self._process_recent_logs(derived_data)
            
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logging.error(f"Error checking build logs: {e}")
    
    def _process_recent_logs(self, derived_data_path: Path):
        """Process recent build logs for diagnostics"""
        if not derived_data_path.exists():
            return
        
        # Look for recent .xcactivitylog files
        for project_dir in derived_data_path.iterdir():
            if not project_dir.is_dir():
                continue
                
            logs_dir = project_dir / "Logs" / "Build"
            if not logs_dir.exists():
                continue
            
            # Get most recent log file
            log_files = list(logs_dir.glob("*.xcactivitylog"))
            if not log_files:
                continue
            
            most_recent_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # Check if this is a new log we haven't processed
            if self._should_process_log(most_recent_log):
                self._parse_build_log(most_recent_log)
    
    def _should_process_log(self, log_file: Path) -> bool:
        """Check if we should process this log file"""
        # Simple check based on modification time
        # In a more robust implementation, we'd track processed logs
        mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        time_diff = datetime.now() - mod_time
        
        # Only process logs modified in the last 5 minutes
        return time_diff.total_seconds() < 300
    
    def _parse_build_log(self, log_file: Path):
        """Parse an Xcode build log file"""
        try:
            # Use xclogparser to extract readable format
            result = subprocess.run([
                'xclogparser', 'dump', '--file', str(log_file), '--output_format', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self._process_parsed_log(json.loads(result.stdout))
            else:
                # Fallback to direct log reading if xclogparser fails
                self._parse_log_directly(log_file)
                
        except subprocess.TimeoutExpired:
            logging.warning("Log parsing timed out")
        except json.JSONDecodeError:
            logging.warning("Failed to parse build log JSON")
        except Exception as e:
            logging.error(f"Error parsing build log: {e}")
    
    def _process_parsed_log(self, log_data: Dict[str, Any]):
        """Process parsed build log data"""
        if not log_data:
            return
        
        # Extract build information
        build_status = "success"
        warnings_count = 0
        errors_count = 0
        diagnostics = []
        
        # Process build steps and issues
        for step in log_data.get('buildSteps', []):
            for issue in step.get('issues', []):
                severity = issue.get('type', '').lower()
                if severity == 'error':
                    errors_count += 1
                    build_status = "error"
                elif severity == 'warning':
                    warnings_count += 1
                    if build_status == "success":
                        build_status = "warning"
                
                diagnostics.append({
                    'severity': severity,
                    'file_path': issue.get('documentURL', '').replace('file://', ''),
                    'line_number': issue.get('startingLineNumber'),
                    'message': issue.get('detail', '')
                })
        
        # Record build event
        if diagnostics or build_status != "success":
            self._record_build_event(build_status, warnings_count, errors_count, diagnostics)
    
    def _record_build_event(self, build_status: str, warnings_count: int, 
                           errors_count: int, diagnostics: List[Dict[str, Any]]):
        """Record a build event and its diagnostics"""
        # Calculate duration if we have build start time
        duration = None
        if self.build_start_time:
            duration = (datetime.now() - self.build_start_time).total_seconds()
        
        # Record build event
        build_event_id = self.diagnostics_db.record_build_event(
            project_path=str(self.project_path),
            build_status=build_status,
            duration=duration,
            warnings_count=warnings_count,
            errors_count=errors_count
        )
        
        # Record diagnostics
        for diag in diagnostics:
            category = self.diagnostics_db.categorize_error(diag['message'])
            self.diagnostics_db.record_diagnostic(
                build_event_id=build_event_id,
                severity=diag['severity'],
                file_path=diag['file_path'],
                line_number=diag['line_number'],
                message=diag['message'],
                category=category
            )
        
        # Notify callbacks
        build_info = {
            'build_event_id': build_event_id,
            'status': build_status,
            'warnings': warnings_count,
            'errors': errors_count,
            'duration': duration,
            'diagnostics': diagnostics
        }
        
        for callback in self.callbacks:
            try:
                callback(build_info)
            except Exception as e:
                logging.error(f"Build callback error: {e}")
    
    def get_current_build_status(self) -> Dict[str, Any]:
        """Get current build status"""
        trends = self.diagnostics_db.get_build_trends(days=1)
        recent_issues = self.diagnostics_db.get_frequent_issues(limit=3, days=1)
        
        return {
            "monitoring": self.is_monitoring,
            "recent_builds": trends.get("total_builds", 0),
            "success_rate": f"{trends.get('success_rate', 0) * 100:.1f}%",
            "avg_duration": f"{trends.get('avg_build_duration', 0):.1f}s" if trends.get('avg_build_duration') else "N/A",
            "recent_issues": recent_issues,
            "last_check": datetime.now().isoformat()
        }
    
    def get_solution_for_error(self, error_message: str) -> Optional[Dict[str, Any]]:
        """Get solution for a specific error message"""
        return self.diagnostics_db.get_solution_for_message(error_message)
    
    def record_successful_fix(self, error_message: str, solution: str, fix_pattern: str = None):
        """Record that an error was successfully fixed"""
        import hashlib
        message_hash = hashlib.md5(error_message.encode()).hexdigest()
        self.diagnostics_db.add_solution(message_hash, solution, fix_pattern)
