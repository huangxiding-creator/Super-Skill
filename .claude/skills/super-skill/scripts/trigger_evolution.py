#!/usr/bin/env python3
"""
Super-Skill Evolution Trigger

Automatically triggers Capability-Evolver after project completion.
Part of Super-Skill V3.1 Phase 12 evolution workflow.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def trigger_evolution(project_dir: str = None):
    """Trigger Capability-Evolver to analyze and optimize Super-Skill."""

    print("=" * 70)
    print("Super-Skill V3.1 - Evolution Trigger")
    print("=" * 70)
    print()

    if project_dir:
        print(f"Project Directory: {project_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    evolver_path = Path("C:\\Users\\91216\\.claude\\skills\\capability-evolver")
    super_skill_path = Path("C:\\Users\\91216\\.claude\\skills\\super-skill")

    # Verify evolver exists
    if not evolver_path.exists():
        print("ERROR: Capability-Evolver not found!")
        print(f"Expected: {evolver_path}")
        print()
        print("Please install Capability-Evolver:")
        print("  git clone https://github.com/autogame-17/evolver.git")
        return 1

    # Verify Super-Skill exists
    if not super_skill_path.exists():
        print("ERROR: Super-Skill not found!")
        print(f"Expected: {super_skill_path}")
        return 1

    print("Starting evolution process...")
    print()

    # Change to evolver directory
    import os
    original_dir = os.getcwd()
    os.chdir(evolver_path)

    try:
        # Run evolver with target
        print("Executing: node index.js run")
        print(f"Target: {super_skill_path}")
        print()

        result = subprocess.run(
            ["node", "index.js", "run"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr)

        print()
        print("-" * 70)

        if result.returncode == 0:
            print("Evolution analysis completed successfully!")

            # Check if evolver created any files
            evolution_summary = super_skill_path / "EVOLUTION_SUMMARY.md"
            if evolution_summary.exists():
                print()
                print(f"Evolution summary created: {evolution_summary}")

            return 0
        else:
            print(f"Evolution failed with code: {result.returncode}")
            return 1

    except subprocess.TimeoutExpired:
        print("ERROR: Evolution timed out after 5 minutes")
        return 1

    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    finally:
        os.chdir(original_dir)


def main():
    """Main entry point."""

    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    return trigger_evolution(project_dir)


if __name__ == "__main__":
    sys.exit(main())
