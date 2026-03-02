#!/usr/bin/env python3
"""
Super-Skill Package Script

Creates a .skill file (zip archive) from the skill directory.
"""

import zipfile
import sys
from pathlib import Path


def create_skill_zip(skill_dir: Path, output_dir: Path = None):
    """Create a .skill zip file from the skill directory."""

    if not skill_dir.exists():
        print(f"Error: Skill directory '{skill_dir}' does not exist.")
        sys.exit(1)

    skill_name = skill_dir.name

    if output_dir is None:
        output_file = skill_dir.parent / f"{skill_name}.skill"
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{skill_name}.skill"

    # Files to include
    files_to_include = [
        "SKILL.md",
        "MEMORY.md",
        "CHANGELOG.md",
        "README_V3.md",
        "CLAUDE_MEM.md",
    ]

    # Directories to include
    dirs_to_include = [
        "scripts",
        "references",
        "assets",
    ]

    print(f"Creating {skill_name}.skill...")
    print(f"Source: {skill_dir}")
    print(f"Output: {output_file}\n")

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add documentation files
        for filename in files_to_include:
            file_path = skill_dir / filename
            if file_path.exists():
                zipf.write(file_path, filename)
                print(f"Added: {filename}")

        # Add scripts
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            for file in scripts_dir.rglob("*"):
                if file.is_file():
                    arcname = f"scripts/{file.relative_to(scripts_dir)}"
                    zipf.write(file, arcname)
                    print(f"Added: {arcname}")

        # Add references
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            for file in refs_dir.rglob("*"):
                if file.is_file():
                    arcname = f"references/{file.relative_to(refs_dir)}"
                    zipf.write(file, arcname)
                    print(f"Added: {arcname}")

        # Add assets
        assets_dir = skill_dir / "assets"
        if assets_dir.exists():
            for file in assets_dir.rglob("*"):
                if file.is_file():
                    arcname = f"assets/{file.relative_to(assets_dir)}"
                    zipf.write(file, arcname)
                    print(f"Added: {arcname}")

    file_size = output_file.stat().st_size
    print(f"\nSkill package created successfully!")
    print(f"Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"Location: {output_file.absolute()}\n")

    return output_file


if __name__ == "__main__":
    skill_dir = Path(__file__).parent.parent

    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = None

    create_skill_zip(skill_dir, output_dir)
