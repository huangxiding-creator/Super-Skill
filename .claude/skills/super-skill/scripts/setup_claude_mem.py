#!/usr/bin/env python3
"""
Super-Skill Claude-Mem Integration Script

Installs and configures Claude-Mem persistent memory system
for Super-Skill V3.2+
"""

import sys
import os
import subprocess
from pathlib import Path


def check_nodejs():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_claude_mem_installed():
    """Check if Claude-Mem is already installed."""
    claude_mem_path = Path("C:\\Users\\91216\\.claude\\skills\\claude-mem")
    return claude_mem_path.exists()


def install_claude_mem():
    """Install Claude-Mem from local cloned repository."""

    claude_mem_path = Path("C:\\Users\\91216\\.claude\\skills\\claude-mem")

    print("=" * 70)
    print("Super-Skill V3.2 - Claude-Mem Integration Setup")
    print("=" * 70)
    print()

    # Check Node.js
    print("Checking prerequisites...")
    if not check_nodejs():
        print("Status: FAILED")
        print()
        print("Node.js is not installed or not in PATH.")
        print("Please install Node.js >= 18.0.0 from https://nodejs.org/")
        return False

    print("Node.js: OK")
    print()

    # Check if Claude-Mem already cloned
    if not claude_mem_path.exists():
        print("Claude-Mem not found in skills directory.")
        print()
        print("Please clone Claude-Mem first:")
        print("  cd C:\\Users\\91216\\.claude\\skills")
        print("  git clone https://github.com/thedotmack/claude-mem.git")
        print()
        return False

    print("Claude-Mem source: FOUND")
    print()

    # Install dependencies
    print("Installing Claude-Mem dependencies...")
    print(f"Working directory: {claude_mem_path}")
    print()

    try:
        # Install npm dependencies
        result = subprocess.run(
            ["npm", "install"],
            cwd=claude_mem_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )

        if result.returncode != 0:
            print("Status: FAILED")
            print()
            print("npm install failed:")
            print(result.stderr)
            return False

        print("npm install: OK")
        print()

        # Build Claude-Mem
        print("Building Claude-Mem...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=claude_mem_path,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print("Status: FAILED")
            print()
            print("npm run build failed:")
            print(result.stderr)
            return False

        print("npm run build: OK")
        print()

        # Create configuration directory
        config_dir = Path.home() / ".claude-mem"
        config_dir.mkdir(exist_ok=True)
        print(f"Configuration directory: {config_dir}")
        print()

        # Create data directory
        data_dir = Path.home() / ".claude-mem" / "data"
        data_dir.mkdir(exist_ok=True, parents=True)
        print(f"Data directory: {data_dir}")
        print()

        print("=" * 70)
        print("Claude-Mem installation completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Start Claude-Mem worker:")
        print("   cd C:\\Users\\91216\\.claude\\skills\\claude-mem")
        print("   npm run worker:start")
        print()
        print("2. Verify Claude-Mem is running:")
        print("   npm run worker:status")
        print()
        print("3. Access web interface (optional):")
        print("   Open http://localhost:37777 in your browser")
        print()

        return True

    except subprocess.TimeoutExpired:
        print("Status: FAILED")
        print()
        print("Installation timed out after 5 minutes")
        return False

    except Exception as e:
        print("Status: FAILED")
        print()
        print(f"Error: {e}")
        return False


def verify_claude_mem():
    """Verify Claude-Mem installation and status."""

    claude_mem_path = Path("C:\\Users\\91216\\.claude\\skills\\claude-mem")

    print("=" * 70)
    print("Super-Skill V3.2 - Claude-Mem Verification")
    print("=" * 70)
    print()

    # Check if installed
    if not claude_mem_path.exists():
        print("Claude-Mem: NOT INSTALLED")
        print()
        print("Please run setup first:")
        print("  python scripts/setup_claude_mem.py")
        return False

    print("Claude-Mem: INSTALLED")
    print(f"Location: {claude_mem_path}")
    print()

    # Check node_modules
    node_modules = claude_mem_path / "node_modules"
    if not node_modules.exists():
        print("Dependencies: NOT INSTALLED")
        print()
        print("Please run:")
        print("  cd C:\\Users\\91216\\.claude\\skills\\claude-mem")
        print("  npm install")
        return False

    print("Dependencies: OK")
    print()

    # Check dist
    dist = claude_mem_path / "dist"
    if not dist.exists():
        print("Build: NOT BUILT")
        print()
        print("Please run:")
        print("  cd C:\\Users\\91216\\.claude\\skills\\claude-mem")
        print("  npm run build")
        return False

    print("Build: OK")
    print()

    # Check worker status
    print("Checking worker status...")
    try:
        result = subprocess.run(
            ["npm", "run", "worker:status"],
            cwd=claude_mem_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("Worker: RUNNING")
            print(result.stdout)
        else:
            print("Worker: NOT RUNNING")
            print()
            print("Start the worker with:")
            print("  cd C:\\Users\\91216\\.claude\\skills\\claude-mem")
            print("  npm run worker:start")

    except Exception as e:
        print(f"Worker: UNKNOWN ({e})")

    print()
    print("=" * 70)
    print("Verification complete.")
    print("=" * 70)

    return True


def main():
    """Main entry point."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Super-Skill Claude-Mem Integration"
    )
    parser.add_argument(
        "action",
        choices=["install", "verify"],
        help="Action to perform"
    )

    args = parser.parse_args()

    if args.action == "install":
        success = install_claude_mem()
        return 0 if success else 1

    elif args.action == "verify":
        success = verify_claude_mem()
        return 0 if success else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
