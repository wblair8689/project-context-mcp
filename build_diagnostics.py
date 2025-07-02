"""
Build Diagnostics Database
Tracks build errors, warnings, and their solutions
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import hashlib

class BuildDiagnosticsDB:
    """Database for tracking build diagnostics and solutions"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Build events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS build_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    build_status TEXT NOT NULL,  -- success, warning, error
                    duration_seconds REAL,
                    warnings_count INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    scheme TEXT,
                    target TEXT
                )
            """)
            
            # Diagnostics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS diagnostics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    build_event_id INTEGER,
                    severity TEXT NOT NULL,  -- error, warning, info
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    message TEXT NOT NULL,
                    message_hash TEXT NOT NULL,  -- for grouping similar messages
                    category TEXT,  -- syntax, concurrency, imports, etc.
                    FOREIGN KEY (build_event_id) REFERENCES build_events (id)
                )
            """)
            
            # Solutions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_hash TEXT NOT NULL,
                    solution_text TEXT NOT NULL,
                    fix_pattern TEXT,  -- regex or description of fix
                    success_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Error patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    common_causes TEXT,
                    fix_suggestions TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_seen TEXT
                )
            """)
            
            conn.commit()
    
    def record_build_event(self, project_path: str, build_status: str, 
                          duration: Optional[float] = None, 
                          warnings_count: int = 0, errors_count: int = 0,
                          scheme: Optional[str] = None, target: Optional[str] = None) -> int:
        """Record a build event and return the event ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO build_events 
                (timestamp, project_path, build_status, duration_seconds, 
                 warnings_count, errors_count, scheme, target)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                project_path,
                build_status,
                duration,
                warnings_count,
                errors_count,
                scheme,
                target
            ))
            return cursor.lastrowid
    
    def record_diagnostic(self, build_event_id: int, severity: str, 
                         file_path: str, line_number: Optional[int], 
                         message: str, category: Optional[str] = None) -> int:
        """Record a diagnostic (error/warning) and return diagnostic ID"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO diagnostics 
                (build_event_id, severity, file_path, line_number, message, message_hash, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                build_event_id,
                severity,
                file_path,
                line_number,
                message,
                message_hash,
                category
            ))
            return cursor.lastrowid
    
    def add_solution(self, message_hash: str, solution_text: str, 
                    fix_pattern: Optional[str] = None) -> int:
        """Add or update a solution for a specific error message"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if solution already exists
            existing = conn.execute(
                "SELECT id, success_count FROM solutions WHERE message_hash = ?",
                (message_hash,)
            ).fetchone()
            
            if existing:
                # Update existing solution
                conn.execute("""
                    UPDATE solutions 
                    SET solution_text = ?, fix_pattern = ?, success_count = success_count + 1, updated_at = ?
                    WHERE id = ?
                """, (solution_text, fix_pattern, now, existing[0]))
                return existing[0]
            else:
                # Create new solution
                cursor = conn.execute("""
                    INSERT INTO solutions (message_hash, solution_text, fix_pattern, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (message_hash, solution_text, fix_pattern, now, now))
                return cursor.lastrowid
    
    def get_solution_for_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Get the best solution for a given error message"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT solution_text, fix_pattern, success_count, updated_at
                FROM solutions 
                WHERE message_hash = ?
                ORDER BY success_count DESC, updated_at DESC
                LIMIT 1
            """, (message_hash,)).fetchone()
            
            if result:
                return {
                    "solution": result[0],
                    "fix_pattern": result[1],
                    "success_count": result[2],
                    "last_updated": result[3]
                }
        return None
    
    def get_recent_diagnostics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent diagnostics from the last N hours"""
        cutoff_date = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute("""
                SELECT d.severity, d.file_path, d.line_number, d.message, 
                       d.category, be.timestamp, be.build_status
                FROM diagnostics d
                JOIN build_events be ON d.build_event_id = be.id
                WHERE be.timestamp >= ?
                ORDER BY be.timestamp DESC
            """, (cutoff_date,)).fetchall()
            
            diagnostics = []
            for row in results:
                diagnostics.append({
                    "severity": row[0],
                    "file_path": row[1],
                    "line_number": row[2],
                    "message": row[3],
                    "category": row[4],
                    "timestamp": row[5],
                    "build_status": row[6]
                })
            
            return diagnostics
    
    def get_frequent_issues(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """Get most frequent build issues in the last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute("""
                SELECT d.message, d.category, d.file_path, COUNT(*) as frequency,
                       s.solution_text, s.fix_pattern
                FROM diagnostics d
                JOIN build_events b ON d.build_event_id = b.id
                LEFT JOIN solutions s ON d.message_hash = s.message_hash
                WHERE b.timestamp > ? AND d.severity = 'error'
                GROUP BY d.message_hash
                ORDER BY frequency DESC
                LIMIT ?
            """, (cutoff_date, limit)).fetchall()
            
            return [
                {
                    "message": row[0],
                    "category": row[1],
                    "file_path": row[2],
                    "frequency": row[3],
                    "solution": row[4],
                    "fix_pattern": row[5]
                }
                for row in results
            ]
    
    def get_build_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get build success trends and metrics"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Success rate
            total_builds = conn.execute(
                "SELECT COUNT(*) FROM build_events WHERE timestamp > ?",
                (cutoff_date,)
            ).fetchone()[0]
            
            successful_builds = conn.execute(
                "SELECT COUNT(*) FROM build_events WHERE timestamp > ? AND build_status = 'success'",
                (cutoff_date,)
            ).fetchone()[0]
            
            # Average build time
            avg_duration = conn.execute(
                "SELECT AVG(duration_seconds) FROM build_events WHERE timestamp > ? AND duration_seconds IS NOT NULL",
                (cutoff_date,)
            ).fetchone()[0]
            
            # Most problematic files
            problematic_files = conn.execute("""
                SELECT d.file_path, COUNT(*) as issue_count
                FROM diagnostics d
                JOIN build_events b ON d.build_event_id = b.id
                WHERE b.timestamp > ? AND d.severity IN ('error', 'warning')
                GROUP BY d.file_path
                ORDER BY issue_count DESC
                LIMIT 5
            """, (cutoff_date,)).fetchall()
            
            return {
                "total_builds": total_builds,
                "successful_builds": successful_builds,
                "success_rate": successful_builds / total_builds if total_builds > 0 else 0,
                "avg_build_duration": avg_duration,
                "problematic_files": [
                    {"file": row[0], "issues": row[1]} 
                    for row in problematic_files
                ]
            }
    
    def categorize_error(self, message: str) -> str:
        """Automatically categorize an error message"""
        message_lower = message.lower()
        
        if "import" in message_lower or "module" in message_lower:
            return "imports"
        elif "string" in message_lower and ("format" in message_lower or "specifier" in message_lower):
            return "string_formatting"
        elif "concurrency" in message_lower or "actor" in message_lower or "captured" in message_lower:
            return "concurrency"
        elif "syntax" in message_lower or "expected" in message_lower:
            return "syntax"
        elif "type" in message_lower and ("mismatch" in message_lower or "cannot" in message_lower):
            return "type_errors"
        elif "unused" in message_lower:
            return "unused_code"
        else:
            return "other"
    
    def learn_from_recent_fixes(self):
        """Analyze recent successful builds to learn solution patterns"""
        # This could be enhanced to automatically detect solution patterns
        # from successful builds that followed errors
        pass
    
    def record_fix(self, error_message: str, solution: str) -> bool:
        """Record that a fix was attempted for a specific error message"""
        message_hash = hashlib.md5(error_message.encode()).hexdigest()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if this solution already exists
                existing = conn.execute("""
                    SELECT id, success_count FROM solutions 
                    WHERE message_hash = ? AND solution_text = ?
                """, (message_hash, solution)).fetchone()
                
                if existing:
                    # Update success count
                    conn.execute("""
                        UPDATE solutions 
                        SET success_count = success_count + 1, updated_at = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), existing[0]))
                else:
                    # Add new solution
                    conn.execute("""
                        INSERT INTO solutions (message_hash, solution_text, success_count, created_at, updated_at)
                        VALUES (?, ?, 1, ?, ?)
                    """, (message_hash, solution, datetime.now().isoformat(), datetime.now().isoformat()))
                
                return True
        except Exception as e:
            logging.error(f"Failed to record fix: {e}")
            return False
