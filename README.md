# better-skills

[中文文档](README.zh.md)

A skill development toolkit for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — create, review, and publish skills with runtime UX best practices baked in.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| [**skill-creator**](skills/skill-creator/) | Create new skills from best-practice templates | Available |
| [**skill-review**](skills/skill-review/) | Validate structure, suggest improvements, and apply fixes | Available |
| [**skill-publish**](skills/skill-publish/) | Package and publish skills for distribution | Available |

## Installation

### Via skills.sh (recommended)

```bash
npx skills add psylch/better-skills -g -y
```

### Manual Install

```bash
git clone https://github.com/psylch/better-skills.git ~/.claude/skills/better-skills
```

Restart Claude Code after installation.

## Prerequisites

- **Claude Code** or any agent that supports [skills.sh](https://skills.sh/)
- **Python 3.11+** (for scaffold scripts — stdlib only, no external dependencies)

## What's Inside

### skill-creator

Guides you through creating a new skill via interactive dialogue — name, level (L0/L0+/L1), environment strategy (stdlib/uv/venv), and output directory. Generates ready-to-edit templates with preflight framework, JSON output conventions, and error handling baked in.

### skill-review

Reviews a skill by combining automated validation (22+ checks across 7 categories, graded A–F) with analytical improvement suggestions based on best practices. Presents a unified report with the grade, issues, and prioritized suggestions with before/after examples. Can interactively apply fixes.

### skill-publish

Packages a skill into a complete GitHub repository: generates README (EN + ZH), LICENSE, plugin.json, marketplace.json, .gitignore, and the proper directory structure. Optionally initializes git and creates a GitHub repo.

### Skill Levels

**L0** — SKILL.md is the entire skill. Best for workflow guides and domain knowledge.

**L0+** — SKILL.md plus lightweight helper scripts for environment detection and status caching.

**L1** — Scripts handle core business logic. SKILL.md orchestrates. Scripts follow MCP tool design principles.

## Project Structure

```
better-skills/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/
│   ├── skill-creator/        # L1: scaffold.py + templates
│   ├── skill-review/         # L1: validate.py + analyze.sh
│   └── skill-publish/        # L1: publish.py + templates
├── README.md
├── README.zh.md
└── LICENSE
```

## License

MIT
