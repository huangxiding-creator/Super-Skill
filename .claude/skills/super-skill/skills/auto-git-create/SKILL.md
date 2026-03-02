---
name: auto-git-create
description: Automated GitHub repository creation from terminal. Integrates with Super-Skill Phase 7 (Project Initialization) and Phase 11 (Deployment) for seamless project setup and publishing workflow.
tags: [git, github, automation, repository, initialization]
version: 1.0.0
source: https://github.com/sagar-datta/auto-git-create
integrated-with: super-skill v3.5+
---

# Auto Git Create Skill

This skill automates the creation of GitHub repositories directly from the terminal, streamlining the project initialization and deployment workflow.

## When to Use This Skill

Use this skill when:
- Starting a new project that needs a GitHub repository (Phase 7)
- Initializing project structure with automated git setup
- Deploying projects to GitHub (Phase 11)
- Creating standardized project boilerplate
- Setting up development environment for new repositories

## Core Functionality

### Automated Repository Creation

```
1. Create new directory and navigate into it
2. Prompt for repository description
3. Create GitHub repository via API
4. Generate README.md file
5. Initialize git repository
6. Stage and commit initial files
7. Add remote origin
8. Push to main/master branch
9. Open VS Code (optional)
```

## Prerequisites

### Required Tools
- `git` - Version control
- `gh` (GitHub CLI) or `curl` with GitHub token
- Code editor (VS Code recommended)

### Authentication Setup

**Option 1: GitHub CLI (Recommended)**
```bash
# Install GitHub CLI
brew install gh  # macOS
winget install GitHub.cli  # Windows

# Authenticate
gh auth login
```

**Option 2: Personal Access Token**
```bash
# Create token at https://github.com/settings/tokens
# Required scopes: repo, user

# Set environment variable
export GITHUB_TOKEN="your-token-here"
```

## Implementation

### Shell Function (Bash/Zsh)

```bash
# Add to ~/.bashrc or ~/.zshrc

auto-git-create() {
    local repo_name="$1"
    local description="$2"

    if [[ -z "$repo_name" ]]; then
        echo "Usage: auto-git-create <repo-name> [description]"
        return 1
    fi

    # Prompt for description if not provided
    if [[ -z "$description" ]]; then
        read -p "Enter repository description: " description
    fi

    # Create and enter directory
    mkdir -p "$repo_name" && cd "$repo_name" || return 1

    # Create README
    echo "# $repo_name\n\n$description" > README.md

    # Initialize git
    git init
    git add README.md
    git commit -m "Initial commit"

    # Create GitHub repository
    gh repo create "$repo_name" \
        --public \
        --description "$description" \
        --source=. \
        --remote=origin \
        --push

    # Open VS Code
    code .
}
```

### Enhanced Version with Options

```bash
auto-git-create() {
    local repo_name=""
    local description=""
    local visibility="public"
    local open_editor=true
    local add_gitignore=true
    local add_license=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --private) visibility="private" ;;
            --no-editor) open_editor=false ;;
            --no-gitignore) add_gitignore=false ;;
            --no-license) add_license=false ;;
            --desc=*) description="${1#*=}" ;;
            *) repo_name="$1" ;;
        esac
        shift
    done

    if [[ -z "$repo_name" ]]; then
        echo "Usage: auto-git-create <repo-name> [options]"
        echo "Options:"
        echo "  --private        Create private repository"
        echo "  --no-editor      Don't open VS Code"
        echo "  --no-gitignore   Skip .gitignore creation"
        echo "  --no-license     Skip LICENSE creation"
        echo "  --desc=DESC      Set repository description"
        return 1
    fi

    # Prompt for description if not provided
    if [[ -z "$description" ]]; then
        read -p "Enter repository description: " description
    fi

    # Create and enter directory
    mkdir -p "$repo_name" && cd "$repo_name" || return 1
    echo "Created directory: $repo_name"

    # Create README
    cat > README.md << EOF
# $repo_name

$description

## Getting Started

\`\`\`bash
# Install dependencies
npm install

# Run development server
npm run dev
\`\`\`

## License

MIT
EOF
    echo "Created README.md"

    # Create .gitignore
    if [[ "$add_gitignore" == true ]]; then
        cat > .gitignore << EOF
# Dependencies
node_modules/

# Build
dist/
build/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
*.log
EOF
        echo "Created .gitignore"
    fi

    # Create LICENSE
    if [[ "$add_license" == true ]]; then
        cat > LICENSE << EOF
MIT License

Copyright (c) $(date +%Y)

Permission is hereby granted, free of charge, to any person obtaining a copy...
EOF
        echo "Created LICENSE"
    fi

    # Initialize git
    git init
    git add .
    git commit -m "Initial commit: Project setup"
    echo "Initialized git repository"

    # Create GitHub repository
    local visibility_flag="--public"
    if [[ "$visibility" == "private" ]]; then
        visibility_flag="--private"
    fi

    gh repo create "$repo_name" \
        $visibility_flag \
        --description "$description" \
        --source=. \
        --remote=origin \
        --push

    echo "Created GitHub repository: https://github.com/$(gh api user --jq '.login')/$repo_name"

    # Open VS Code
    if [[ "$open_editor" == true ]]; then
        code .
    fi
}
```

## Integration with Super-Skill

### Phase 7: Project Initialization

Auto-git-create integrates into project initialization:

1. **Repository Creation**
   - Use auto-git-create after project structure is defined
   - Automate GitHub repository setup
   - Initialize with standard files (README, .gitignore, LICENSE)

2. **Standardization**
   - Consistent project structure across all projects
   - Pre-configured git settings
   - Standard documentation templates

3. **Workflow Integration**
   ```
   Phase 7.1 → Define project structure
   Phase 7.2 → Run auto-git-create
   Phase 7.3 → Configure development environment
   Phase 7.4 → Setup CI/CD scaffolding
   ```

### Phase 11: Deployment

Auto-git-create supports deployment:

1. **Initial Deployment**
   - Push to remote repository
   - Trigger CI/CD pipelines
   - Enable GitHub Actions

2. **Repository Management**
   - Create release branches
   - Tag versions
   - Generate release notes

## Command Reference

### Basic Usage

```bash
# Create public repository with prompts
auto-git-create my-project

# Create with description
auto-git-create my-project --desc="A sample project"

# Create private repository
auto-git-create my-project --private
```

### Advanced Options

```bash
# Minimal setup (no editor, no extra files)
auto-git-create my-project --no-editor --no-gitignore --no-license

# Full setup with all options
auto-git-create my-project \
    --desc="Full-stack web application" \
    --private \
    --editor
```

## Error Handling

```bash
# Check for gh CLI
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    return 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub"
    echo "Run: gh auth login"
    return 1
fi

# Check if directory already exists
if [[ -d "$repo_name" ]]; then
    echo "Error: Directory '$repo_name' already exists"
    return 1
fi
```

## Customization

### Project Templates

```bash
# Create with specific template
auto-git-create-react() {
    auto-git-create "$1" --desc="$2"
    npx create-react-app . --template typescript
    git add .
    git commit -m "Add React TypeScript template"
    git push origin main
}

# Create Next.js project
auto-git-create-next() {
    auto-git-create "$1" --desc="$2"
    npx create-next-app@latest . --typescript --tailwind --eslint
    git add .
    git commit -m "Add Next.js template"
    git push origin main
}
```

### Platform-Specific Variants

```bash
# Windows PowerShell version
function New-GitRepo {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [string]$Description = "",
        [switch]$Private
    )

    New-Item -ItemType Directory -Name $Name | Set-Location
    "# $Name`n\n$Description" | Out-File -FilePath README.md

    git init
    git add README.md
    git commit -m "Initial commit"

    $visibility = if ($Private) { "--private" } else { "--public" }
    gh repo create $Name $visibility --description $Description --source=. --push

    code .
}
```

## Best Practices

1. **Always provide meaningful descriptions**
   - Helps with repository discovery
   - Improves documentation

2. **Use appropriate visibility**
   - Public for open-source
   - Private for proprietary work

3. **Include standard files**
   - README.md with project overview
   - .gitignore for common exclusions
   - LICENSE for legal clarity

4. **Configure branch protection**
   - Protect main/master branch
   - Require PR reviews
   - Enable status checks

## Workflow Examples

### Starting a New Feature Project

```bash
# Create repository
auto-git-create feature-x --desc="New feature implementation"

# Setup development environment
npm init -y
npm install -D typescript jest eslint prettier

# Initialize project structure
mkdir -p src/{components,utils,types} tests

# Commit initial structure
git add .
git commit -m "Add project structure"
git push origin main
```

### Creating a Microservice

```bash
# Create repository with private visibility
auto-git-create user-service --desc="User management microservice" --private

# Initialize Node.js project
npm init -y
npm install express typescript @types/express

# Setup Docker
cat > Dockerfile << EOF
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
EOF

git add .
git commit -m "Add Docker configuration"
git push origin main
```

## Checklist

### Before Creating Repository
- [ ] GitHub CLI installed and authenticated
- [ ] Project name is unique and descriptive
- [ ] Description prepared
- [ ] Visibility decided (public/private)

### After Creating Repository
- [ ] README.md created with project overview
- [ ] .gitignore configured for project type
- [ ] LICENSE file added
- [ ] Branch protection rules configured
- [ ] CI/CD pipeline enabled (GitHub Actions)

## Deliverables

- GitHub repository with initial commit
- Standard project files (README, .gitignore, LICENSE)
- Configured remote origin
- Development environment ready

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-01 | Initial integration with Super-Skill V3.5 |

---

## License

MIT License - Based on [auto-git-create](https://github.com/sagar-datta/auto-git-create)
