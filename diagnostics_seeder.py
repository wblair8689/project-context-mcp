"""
Build Diagnostics Seeder
Pre-populates the diagnostics database with known solutions
"""

import hashlib
from build_diagnostics import BuildDiagnosticsDB

def seed_known_solutions(diagnostics_db: BuildDiagnosticsDB):
    """Seed the database with known error solutions"""
    
    known_solutions = [
        {
            "error": "Extra argument 'specifier' in call",
            "solution": "Use String(format: \"%.0f\", value) instead of \\(value, specifier: \"%.0f\") in string interpolation",
            "fix_pattern": "Replace \\\\(.*?, specifier: \".*?\"\\\\) with String(format: \"pattern\", value)",
            "category": "string_formatting"
        },
        {
            "error": "Initialization of immutable value '.*' was never used; consider replacing with assignment to '_' or removing it",
            "solution": "Replace unused variable with let _ = expression or remove the variable entirely",
            "fix_pattern": "let unusedVar = expr -> let _ = expr",
            "category": "unused_code"
        },
        {
            "error": "Immutable value '.*' was never used; consider replacing with '_' or removing it",
            "solution": "Replace unused loop variable with underscore: for i in range -> for _ in range",
            "fix_pattern": "for unusedVar in -> for _ in",
            "category": "unused_code"
        },
        {
            "error": "Reference to captured var '.*' in concurrently-executing code; this is an error in the Swift 6 language mode",
            "solution": "Use immutable variables or MainActor.run { } to avoid capturing mutable state in concurrent contexts",
            "fix_pattern": "Create immutable copy before async context or use MainActor isolation",
            "category": "concurrency"
        },
        {
            "error": "Cannot find type '.*' in scope",
            "solution": "Add missing import statement for the type or check spelling",
            "fix_pattern": "import MissingModule",
            "category": "imports"
        },
        {
            "error": "Value of type '.*' has no member '.*'",
            "solution": "Check the API documentation for correct property/method names or add required extensions",
            "fix_pattern": "Verify property names or add extension",
            "category": "type_errors"
        },
        {
            "error": "Type '.*' cannot conform to protocol '.*'",
            "solution": "Implement required protocol methods or check protocol requirements",
            "fix_pattern": "Add required protocol conformance methods",
            "category": "type_errors"
        },
        {
            "error": "Missing return in a function expected to return '.*'",
            "solution": "Add return statement with appropriate value or change function to return Void",
            "fix_pattern": "return appropriateValue",
            "category": "syntax"
        }
    ]
    
    for solution_data in known_solutions:
        error_message = solution_data["error"]
        message_hash = hashlib.md5(error_message.encode()).hexdigest()
        
        diagnostics_db.add_solution(
            message_hash=message_hash,
            solution_text=solution_data["solution"],
            fix_pattern=solution_data["fix_pattern"]
        )
        
        # Use logging instead of print to avoid corrupting MCP JSON-RPC
        import logging
        logging.getLogger(__name__).debug(f"✅ Seeded solution for: {error_message[:50]}...")

if __name__ == "__main__":
    from pathlib import Path
    
    # Example usage
    db_path = Path("./data/build_diagnostics.db")
    db = BuildDiagnosticsDB(db_path)
    seed_known_solutions(db)
    print("Database seeded with known solutions!")
