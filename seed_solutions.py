"""
Seed the diagnostics database with solutions we just discovered
"""

from build_awareness import BuildAwarenessManager
from pathlib import Path

def seed_recent_solutions():
    """Seed the database with solutions from today's session"""
    
    project_root = "/Users/williamblair/AI-Game-Evolution-Platform"
    data_dir = Path(project_root) / "project_context_mcp" / "data"
    
    # Initialize build awareness
    build_awareness = BuildAwarenessManager(project_root, data_dir)
    
    # Record the solutions we just implemented
    recent_fixes = [
        {
            "error": "Extra argument 'specifier' in call",
            "solution": "Replace '\\(value, specifier: \"%.0f\")' with 'String(format: \"%.0f\", value)' - Swift string interpolation doesn't support specifier parameter"
        },
        {
            "error": "Reference to captured var 'newVariants' in concurrently-executing code; this is an error in the Swift 6 language mode",
            "solution": "Use immutable closure pattern: let newVariants: [Type] = { var temp = []; /* build array */; return temp }() to complete array construction before MainActor.run"
        },
        {
            "error": "Initialization of immutable value 'avgFitness' was never used; consider replacing with assignment to '_' or removing it",
            "solution": "Replace 'let avgFitness = value' with 'let _ = value' to acknowledge calculated value without using it"
        },
        {
            "error": "Immutable value 'i' was never used; consider replacing with '_' or removing it",
            "solution": "Replace 'for i in 0..<count' with 'for _ in 0..<count' when loop index isn't needed"
        }
    ]
    
    print("🌱 Seeding diagnostics database with recent solutions...")
    
    for fix in recent_fixes:
        build_awareness.record_manual_fix(fix["error"], fix["solution"])
    
    print(f"✅ Seeded {len(recent_fixes)} solutions to diagnostics database")
    
    # Test retrieval
    print("\n🔍 Testing solution retrieval:")
    test_error = "Extra argument 'specifier' in call"
    solution = build_awareness.diagnostics_db.get_solution_for_message(test_error)
    if solution:
        print(f"Found solution for '{test_error}': {solution['solution'][:60]}...")
    else:
        print(f"No solution found for '{test_error}'")

if __name__ == "__main__":
    seed_recent_solutions()
