# Contributing to Super-Skill / 贡献指南

Thank you for your interest in contributing to Super-Skill! / 感谢你对 Super-Skill 的关注！

## How to Contribute / 如何贡献

### 1. Report Issues / 报告问题

- Use [GitHub Issues](https://github.com/huangxiding-creator/Super-Skill/issues)
- Include: Super-Skill version, Claude Code version, expected vs actual behavior
- 使用 [GitHub Issues](https://github.com/huangxiding-creator/Super-Skill/issues) 提交问题

### 2. Add New Sub-Skills / 添加新子技能

Create a new directory under `skills/`:

```
skills/your-skill-name/
└── SKILL.md          # Skill definition
```

**SKILL.md Template:**
```markdown
---
name: your-skill-name
description: One-line description. TRIGGER when [specific condition].
---

# Your Skill Name

## Purpose
What this skill does and when to use it.

## Usage
How to invoke and configure this skill.

## Patterns
Specific patterns, code examples, and best practices.
```

**Guidelines:**
- Keep SKILL.md under 300 lines
- Use progressive disclosure (main file + references)
- Include clear TRIGGER conditions in description
- Provide concrete examples, not abstract descriptions

### 3. Improve Existing Skills / 改进现有技能

- Read the skill's SKILL.md first
- Follow the autoresearch simplicity criterion: equal performance + simpler = keep
- Test changes before submitting PR

### 4. Translate Documentation / 翻译文档

- We welcome translations into any language
- Follow the bilingual format: English first, then translation
- Keep technical terms consistent

## Development Workflow / 开发流程

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/Super-Skill.git

# 2. Create a feature branch
git checkout -b feature/your-feature

# 3. Make changes and test
npx skills add .claude/skills/super-skill --global --yes

# 4. Commit with conventional format
git commit -m "feat: add your-feature description"

# 5. Push and create PR
git push origin feature/your-feature
```

## Commit Convention / 提交规范

| Type | Description |
|------|-------------|
| `feat:` | New feature / 新功能 |
| `fix:` | Bug fix / 修复 |
| `refactor:` | Code refactor / 重构 |
| `docs:` | Documentation / 文档 |
| `skill:` | New or updated skill / 新增或更新技能 |
| `test:` | Testing / 测试 |
| `chore:` | Maintenance / 维护 |

## Code of Conduct / 行为准则

- Be respectful and constructive
- Focus on the improvement, not the person
- Welcome newcomers and help them get started
- 尊重他人，建设性交流
- 欢迎新手并帮助他们上手

## License / 许可证

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
