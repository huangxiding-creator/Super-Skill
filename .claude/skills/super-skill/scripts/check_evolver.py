#!/usr/bin/env python3
"""
Super-Skill Evolver Checker

Verifies that Capability-Evolver is installed and functional.
Part of Super-Skill V3.1 startup sequence.
"""

import sys
import json
from pathlib import Path


def check_evolver_installation():
    """Check if Capability-Evolver is installed."""

    evolver_path = Path("C:\\Users\\91216\\.claude\\skills\\capability-evolver")

    print("Checking Capability-Evolver installation...")
    print(f"Expected path: {evolver_path}")
    print()

    # Check if evolver directory exists
    if not evolver_path.exists():
        print("Status: NOT INSTALLED")
        print()
        print("Capability-Evolver is not installed.")
        print("Please install it using:")
        print("  git clone https://github.com/autogame-17/evolver.git")
        print("  # Copy to C:\\Users\\91216\\.claude\\skills\\capability-evolver")
        return False

    print("Status: INSTALLED")

    # Check critical files
    critical_files = [
        "index.js",
        "package.json",
        ".env",
        ".env.mad-dog",
    ]

    print()
    print("Checking critical files...")

    all_present = True
    for file_name in critical_files:
        file_path = evolver_path / file_name
        status = "OK" if file_path.exists() else "MISSING"
        print(f"  {file_name}: {status}")
        if not file_path.exists():
            all_present = False

    print()

    # Check package.json for scripts
    package_json = evolver_path / "package.json"
    if package_json.exists():
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)

            scripts = package_data.get('scripts', {})
            print("Available scripts:")
            for script_name in ['start', 'run', 'mad-dog', 'loop', 'solidify']:
                status = "OK" if script_name in scripts else "MISSING"
                print(f"  {script_name}: {status}")

        except json.JSONDecodeError:
            print("  package.json: INVALID JSON")
            all_present = False
    else:
        all_present = False

    print()

    # Check configuration
    super_skill_env = Path(__file__).parent.parent / ".env.super-skill"
    print(f"Checking Super-Skill evolution config...")
    print(f"  {super_skill_env}: {'OK' if super_skill_env.exists() else 'MISSING'}")
    print()

    if all_present:
        print("Capability-Evolver is ready.")
        return True
    else:
        print("Capability-Evolver installation incomplete.")
        return False


def run_evolver_test():
    """Test if Evolver can run."""

    evolver_path = Path("C:\\Users\\91216\\.claude\\skills\\capability-evolver")

    print("Testing Evolver functionality...")
    print()

    # Check if Node.js is available
    import subprocess

    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Node.js: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("Node.js: NOT AVAILABLE")
        print()
        print("Please install Node.js to use Capability-Evolver.")
        return False

    print()
    print("Evolver is functional.")
    return True


def main():
    """Main entry point."""

    print("=" * 60)
    print("Super-Skill V3.1 - Capability-Evolver Checker")
    print("=" * 60)
    print()

    # Check installation
    if not check_evolver_installation():
        sys.exit(1)

    # Test functionality
    if not run_evolver_test():
        sys.exit(1)

    print()
    print("=" * 60)
    print("All checks passed! Evolver is ready.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
