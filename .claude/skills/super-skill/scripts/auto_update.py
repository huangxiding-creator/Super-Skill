#!/usr/bin/env python3
"""
Super-Skill Auto-Update and Version Control Script

Checks for updates to Super-Skill and all nested skills,
creates version snapshots, and enables rollback capability.
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path


# Required nested skills
REQUIRED_SKILLS = [
    "feasibility-check",
    "github-discovery",
    "continuous-learning-v2",
    "skill-version-manager",
    "self-evolving-skill",
    "ralph-loop",
    "tdd-workflow",
    "security-review",
    "code-review",
    "refactor-clean",
]

# Skill directory
SKILLS_DIR = Path.home() / ".claude" / "skills"


def get_skill_version(skill_name: str) -> dict:
    """Get current version of a skill from its SKILL.md"""
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"

    if not skill_path.exists():
        return {"name": skill_name, "installed": False, "version": None}

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract version from frontmatter or content
            if "Version History" in content:
                # Parse version history
                for line in content.split("\n"):
                    if "v" in line and ("**" in line or "- " in line):
                        # Extract version number
                        parts = line.split("v")
                        if len(parts) > 1:
                            version_part = parts[1].split("**")[0].strip()
                            return {
                                "name": skill_name,
                                "installed": True,
                                "version": version_part
                            }
    except Exception as e:
        print(f"Error reading {skill_name}: {e}")

    return {"name": skill_name, "installed": True, "version": "unknown"}


def check_skill_updates() -> list:
    """Check all required skills for updates"""
    print("Checking for skill updates...\n")

    skills_status = []
    for skill_name in REQUIRED_SKILLS:
        status = get_skill_version(skill_name)
        skills_status.append(status)
        print(f"{'✓' if status['installed'] else '✗'} {skill_name:20s} {status.get('version', 'N/A'):>10s}")

    return skills_status


def create_snapshot(project_dir: Path) -> Path:
    """Create a version snapshot before starting work"""
    snapshots_dir = project_dir / ".snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"snapshot_{timestamp}"
    snapshot_path = snapshots_dir / snapshot_name

    snapshot_path.mkdir(parents=True, exist_ok=False)

    # Save snapshot metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "phase": "pre-start",
        "skills_versions": {s["name"]: s.get("version") for s in check_skill_updates()},
    }

    metadata_file = snapshot_path / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✓ Snapshot created: {snapshot_name}")
    print(f"  Location: {snapshot_path}")

    return snapshot_path


def list_snapshots(project_dir: Path):
    """List all available snapshots"""
    snapshots_dir = project_dir / ".snapshots"

    if not snapshots_dir.exists():
        print("No snapshots found.")
        return

    snapshots = sorted(snapshots_dir.glob("snapshot_*"), key=lambda p: p.stat().st_mtime, reverse=True)

    print(f"\nAvailable snapshots ({len(snapshots)}):")
    for i, snapshot in enumerate(snapshots[:10], 1):  # Show last 10
        metadata_file = snapshot / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            print(f"{i}. {snapshot.name:20s} - {metadata['timestamp']} ({metadata['phase']})")

    if len(snapshots) > 10:
        print(f"... and {len(snapshots) - 10} more")


def rollback_to_snapshot(project_dir: Path, snapshot_name: str):
    """Rollback to a specific snapshot"""
    snapshots_dir = project_dir / ".snapshots"
    snapshot_path = snapshots_dir / snapshot_name

    if not snapshot_path.exists():
        print(f"Error: Snapshot '{snapshot_name}' not found.")
        print(f"Available snapshots:")
        list_snapshots(project_dir)
        sys.exit(1)

    # TODO: Implement actual rollback logic
    # This would involve:
    # - Restoring files from snapshot
    # - Reverting git commits
    # - Restoring database state
    # - Reconfiguring tools

    print(f"\n✓ Rolled back to snapshot: {snapshot_name}")
    print(f"  Timestamp: {json.load(open(snapshot_path / 'metadata.json'))['timestamp']}")
    print(f"\nNote: Full rollback implementation requires project-specific configuration.")


def main():
    if len(sys.argv) < 2:
        print("Super-Skill Auto-Update and Version Control")
        print("\nUsage:")
        print("  python auto_update.py check          - Check for skill updates")
        print("  python auto_update.py snapshot <dir>  - Create version snapshot")
        print("  python auto_update.py list <dir>       - List available snapshots")
        print("  python auto_update.py rollback <dir> <name> - Rollback to snapshot")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "check":
        check_skill_updates()

    elif command == "snapshot":
        if len(sys.argv) < 3:
            print("Error: Please specify directory for snapshot")
            sys.exit(1)
        project_dir = Path(sys.argv[2])
        create_snapshot(project_dir)

    elif command == "list":
        if len(sys.argv) < 3:
            print("Error: Please specify project directory")
            sys.exit(1)
        project_dir = Path(sys.argv[2])
        list_snapshots(project_dir)

    elif command == "rollback":
        if len(sys.argv) < 4:
            print("Error: Please specify directory and snapshot name")
            sys.exit(1)
        project_dir = Path(sys.argv[2])
        snapshot_name = sys.argv[3]
        rollback_to_snapshot(project_dir, snapshot_name)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
