#!/usr/bin/env python3
"""
Super-Skill Project Initialization Script

This script helps quickly initialize a new project with all necessary documentation
templates following the 8-phase development workflow.

Usage:
    python init_project.py <project_name> [output_dir]

Example:
    python init_project.py my-awesome-project ./projects
"""

import os
import sys
from datetime import datetime
from pathlib import Path


# Template files to create
TEMPLATE_FILES = [
    "KNOWLEDGE_BASE_TEMPLATE.md",
    "REQUIREMENTS_TEMPLATE.md",
    "ARCHITECTURE_TEMPLATE.md",
    "API_DESIGN_TEMPLATE.md",
    "DATABASE_SCHEMA_TEMPLATE.md",
    "TECHNICAL_IMPLEMENTATION_TEMPLATE.md",
    "DEVELOPMENT_PLAN_TEMPLATE.md",
    "TEST_PLAN_TEMPLATE.md",
    "DEPLOYMENT_PLAN_TEMPLATE.md",
    "PROGRESS_TEMPLATE.md",
    "ITERATION_LOG_TEMPLATE.md",
    "PROJECT_SUMMARY_TEMPLATE.md",
]


def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent


def get_references_dir():
    """Get the references directory."""
    return get_script_dir().parent / "references"


def create_project_structure(project_name: str, output_dir: Path) -> Path:
    """Create the project directory structure."""
    project_path = output_dir / project_name

    # Create main project directory
    project_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    dirs_to_create = [
        "docs",
        "src",
        "tests",
        "scripts",
        "docs/phase0",
        "docs/phase1",
        "docs/phase2",
        "docs/phase3",
        "docs/phase4",
        "docs/phase5",
        "docs/phase6",
        "docs/phase7",
        "docs/phase8",
    ]

    for dir_name in dirs_to_create:
        (project_path / dir_name).mkdir(parents=True, exist_ok=True)

    return project_path


def copy_template_files(project_path: Path, project_name: str):
    """Copy and customize template files to the project."""
    refs_dir = get_references_dir()
    docs_dir = project_path / "docs"

    # Copy available templates
    for template_file in TEMPLATE_FILES:
        template_path = refs_dir / template_file

        if template_path.exists():
            # Remove '_TEMPLATE' suffix and create actual file
            output_name = template_file.replace("_TEMPLATE", "")
            output_path = docs_dir / output_name

            # Read template
            content = template_path.read_text(encoding="utf-8")

            # Replace placeholders
            content = content.replace("[Project Name]", project_name)
            content = content.replace("[Date]", datetime.now().strftime("%Y-%m-%d"))

            # Write customized template
            output_path.write_text(content, encoding="utf-8")
            print(f"Created: {output_path.relative_to(project_path)}")
        else:
            print(f"Skipped: {template_file} (not found in references)")


def create_readme(project_path: Path, project_name: str):
    """Create a README.md with project overview."""
    readme_content = f"""# {project_name}

## Project Overview

This project follows the **Super-Skill 8-Phase Development Workflow**.

## Current Phase

**Phase:** Initialization
**Status:** Project setup started on {datetime.now().strftime("%Y-%m-%d")}

## Project Structure

```
{project_name}/
├── docs/              # Documentation for each phase
│   ├── KNOWLEDGE_BASE.md
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   └── ...
├── src/               # Source code
├── tests/             # Test files
└── scripts/           # Build and utility scripts
```

## Super-Sill Workflow

This project follows these phases:

- **Phase 0:** Project Initialization & Knowledge Preparation
- **Phase 1:** Requirements Engineering
- **Phase 2:** Architecture Design
- **Phase 3:** Detailed Planning
- **Phase 4:** Agile Development
- **Phase 5:** CI & Quality Assurance
- **Phase 6:** Intelligent Iteration
- **Phase 7:** Delivery & Deployment
- **Phase 8:** Project Summary

## Getting Started

1. Review and customize the documentation templates in `docs/`
2. Start with Phase 0: Complete `KNOWLEDGE_BASE.md`
3. Follow each phase sequentially, completing gate checks
4. Track progress in `PROGRESS.md`

## Documentation

See the [docs](docs/) directory for detailed project documentation.
"""

    (project_path / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"Created: README.md")


def create_gitignore(project_path: Path):
    """Create a .gitignore file."""
    gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Build outputs
dist/
build/
*.log

# OS
.DS_Store
Thumbs.db

# Project specific
docs/**/*.md.template
"""

    (project_path / ".gitignore").write_text(gitignore_content, encoding="utf-8")
    print(f"Created: .gitignore")


def main():
    if len(sys.argv) < 2:
        print("Usage: python init_project.py <project_name> [output_dir]")
        print("\nExample:")
        print("  python init_project.py my-awesome-project")
        print("  python init_project.py my-awesome-project ./projects")
        sys.exit(1)

    project_name = sys.argv[1]
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    print(f"\n{'='*60}")
    print(f"Super-Skill Project Initialization")
    print(f"{'='*60}\n")
    print(f"Project Name: {project_name}")
    print(f"Output Directory: {output_dir.absolute()}\n")

    # Create project structure
    print("Creating project structure...")
    project_path = create_project_structure(project_name, output_dir)

    # Copy template files
    print("\nCopying template files...")
    copy_template_files(project_path, project_name)

    # Create README
    print("\nCreating project files...")
    create_readme(project_path, project_name)
    create_gitignore(project_path)

    print(f"\n{'='*60}")
    print(f"Project initialized successfully!")
    print(f"{'='*60}\n")
    print(f"Project Location: {project_path.absolute()}")
    print(f"\nNext Steps:")
    print(f"1. cd {project_path}")
    print(f"2. Review and customize documentation in docs/")
    print(f"3. Start with Phase 0: Complete KNOWLEDGE_BASE.md")
    print(f"4. Track progress in PROGRESS.md\n")


if __name__ == "__main__":
    main()
