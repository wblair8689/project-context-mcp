"""
Xcode Runtime Monitor Module for Project Context MCP
Handles runtime error monitoring, console capture, and crash analysis
"""

import asyncio
import subprocess
import re
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator
import queue
import threading

class XcodeRuntimeMonitor:
    """Monitor and analyze Xcode runtime errors and console output"""
    
    def __init__(self, bundle_id: str = "com.evolution.master"):
        self.bundle_id = bundle_id
        self.log_queue = queue.Queue(maxsize=10000)  # Limit queue size
        self.error_queue = queue.Queue(maxsize=1000)
        self.log_file = f"/tmp/xcode_runtime_{bundle_id.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.error_patterns = {
            'fatal': r'Fatal error:.*',
            'crash': r'Thread \d+:.*signal',
            'exception': r'(?:NS)?Exception|exception',
            'assertion': r'Assertion failed|precondition failed',
            'range': r'Range requires lowerBound.*upperBound',
            'nil': r'unexpectedly found nil|force unwrap',
            'memory': r'EXC_BAD_ACCESS|memory',
            'index': r'Index out of range|index.*bounds'
        }
        
        self.stream_process = None
        self.monitoring = False
        self.monitor_task = None
        
    async def start_monitoring(self) -> Dict:
        """Start monitoring console output"""
        if self.monitoring:
            return {
                "status": "already_running",
                "log_file": self.log_file
            }
        
        # Build the command
        cmd = [
            "xcrun", "simctl", "spawn", "booted", "log", "stream",
            "--level=debug",
            "--style=syslog",
            "--predicate", f"subsystem contains '{self.bundle_id}' OR processImagePath endswith '{self.bundle_id.split('.')[-1]}'"
        ]
        
        try:
            # Start the streaming process
            self.stream_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.monitoring = True
            
            # Start the monitoring task
            self.monitor_task = asyncio.create_task(self._monitor_stream())
            
            return {
                "status": "monitoring_started",
                "bundle_id": self.bundle_id,
                "log_file": self.log_file,
                "pid": self.stream_process.pid
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _monitor_stream(self):
        """Monitor the log stream and process entries"""
        try:
            with open(self.log_file, 'w') as log_f:
                async for line in self._read_stream():
                    # Write to file
                    log_f.write(line + '\n')
                    log_f.flush()
                    
                    # Parse and queue
                    parsed = self._parse_log_line(line)
                    if parsed:
                        # Add to general log queue
                        try:
                            self.log_queue.put_nowait(parsed)
                        except queue.Full:
                            # Remove oldest to make room
                            self.log_queue.get_nowait()
                            self.log_queue.put_nowait(parsed)
                        
                        # Add to error queue if it's an error
                        if parsed.get("is_error"):
                            try:
                                self.error_queue.put_nowait(parsed)
                            except queue.Full:
                                # Remove oldest error
                                self.error_queue.get_nowait()
                                self.error_queue.put_nowait(parsed)
                            
                            # Handle critical errors
                            if parsed.get("error_type") in ["fatal", "crash"]:
                                await self._capture_crash_context(parsed)
                                
        except Exception as e:
            # Use logging instead of print to avoid corrupting MCP JSON-RPC
            import logging
            logging.getLogger(__name__).error(f"Monitor stream error: {e}")
        finally:
            self.monitoring = False
    
    async def _read_stream(self) -> AsyncIterator[str]:
        """Read lines from the process stream"""
        while self.monitoring and self.stream_process and self.stream_process.stdout:
            line = await self.stream_process.stdout.readline()
            if not line:
                break
            yield line.decode('utf-8').strip()
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """Parse a log line into structured data"""
        if not line:
            return None
        
        parsed = {
            "timestamp": datetime.now().isoformat(),
            "raw": line,
            "is_error": False,
            "error_type": None,
            "level": "info"
        }
        
        # Check for error patterns
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                parsed["is_error"] = True
                parsed["error_type"] = error_type
                parsed["level"] = "error"
                
                # Extract specific details for range errors
                if error_type == "range":
                    match = re.search(r'Range\(uncheckedBounds: \(lower: (-?\d+), upper: (-?\d+)\)\)', line)
                    if match:
                        parsed["range_lower"] = int(match.group(1))
                        parsed["range_upper"] = int(match.group(2))
                        parsed["range_issue"] = f"Lower ({match.group(1)}) > Upper ({match.group(2)})"
                
                break
        
        return parsed
    
    async def _capture_crash_context(self, error: Dict):
        """Capture crash context when fatal error detected"""
        context_file = f"/tmp/crash_context_{self.bundle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Get recent logs for context
        recent_logs = self.get_recent_logs(100)
        recent_errors = self.get_recent_errors(20)
        
        context = {
            "fatal_error": error,
            "bundle_id": self.bundle_id,
            "timestamp": datetime.now().isoformat(),
            "recent_logs": recent_logs,
            "recent_errors": recent_errors,
            "log_file": self.log_file
        }
        
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        error["crash_context_file"] = context_file
    
    def get_recent_logs(self, count: int = 100) -> List[Dict]:
        """Get recent logs from the queue"""
        logs = []
        temp_list = []
        
        # Empty queue into list
        while not self.log_queue.empty() and len(temp_list) < count * 2:
            try:
                temp_list.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        
        # Take the most recent ones
        logs = temp_list[-count:]
        
        # Put back the rest
        for log in temp_list:
            try:
                self.log_queue.put_nowait(log)
            except queue.Full:
                break
        
        return logs
    
    def get_recent_errors(self, count: int = 50) -> List[Dict]:
        """Get recent errors only"""
        errors = []
        temp_list = []
        
        # Empty error queue
        while not self.error_queue.empty():
            try:
                temp_list.append(self.error_queue.get_nowait())
            except queue.Empty:
                break
        
        # Take most recent
        errors = temp_list[-count:]
        
        # Put back the rest
        for error in temp_list:
            try:
                self.error_queue.put_nowait(error)
            except queue.Full:
                break
        
        return errors
    
    def analyze_errors(self) -> Dict:
        """Analyze current errors and provide insights"""
        errors = self.get_recent_errors()
        
        if not errors:
            return {
                "error_count": 0,
                "insights": "No runtime errors detected"
            }
        
        # Group by type
        error_types = {}
        for error in errors:
            err_type = error.get("error_type", "unknown")
            if err_type not in error_types:
                error_types[err_type] = []
            error_types[err_type].append(error)
        
        insights = {
            "error_count": len(errors),
            "error_types": {k: len(v) for k, v in error_types.items()},
            "most_recent": errors[-1] if errors else None,
            "suggestions": []
        }
        
        # Add specific suggestions
        if "range" in error_types:
            range_error = error_types["range"][-1]
            insights["suggestions"].append({
                "type": "range",
                "issue": range_error.get("range_issue", "Range bounds error"),
                "fixes": [
                    "Ensure lowerBound <= upperBound before creating Range",
                    "Use min/max: Range(min(a,b)...max(a,b))",
                    "Add validation: guard lower <= upper else { return }"
                ]
            })
        
        if "nil" in error_types:
            insights["suggestions"].append({
                "type": "nil_reference",
                "fixes": [
                    "Use optional binding: if let value = optional { }",
                    "Use nil-coalescing: value ?? defaultValue",
                    "Add guard statements for early return"
                ]
            })
        
        return insights
    
    async def stop_monitoring(self) -> Dict:
        """Stop monitoring"""
        self.monitoring = False
        
        if self.stream_process:
            self.stream_process.terminate()
            await self.stream_process.wait()
        
        if self.monitor_task:
            await self.monitor_task
        
        return {
            "status": "stopped",
            "log_file": self.log_file,
            "errors_captured": self.error_queue.qsize()
        }
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "monitoring": self.monitoring,
            "bundle_id": self.bundle_id,
            "log_file": self.log_file,
            "logs_in_queue": self.log_queue.qsize(),
            "errors_in_queue": self.error_queue.qsize(),
            "process_running": self.stream_process is not None and self.stream_process.returncode is None
        }