# Distribution Guide

How to distribute Claude Code skills via skills.sh and GitHub.

## Repository Structure

A distributable skill repository follows this structure:

```
<repo-name>/
├── .claude-plugin/
│   ├── plugin.json           # Skill metadata
│   └── marketplace.json      # Registry entry
├── skills/
│   └── <skill-name>/         # The skill itself
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
├── README.md
├── README.zh.md (optional)
├── LICENSE
└── .gitignore
```

## plugin.json

Describes the skill package:

```json
{
  "name": "skill-name",
  "description": "What the skill does",
  "version": "1.0.0",
  "author": {"name": "owner"},
  "homepage": "https://github.com/owner/repo",
  "license": "MIT"
}
```

## marketplace.json

Registry entry for discovery:

```json
{
  "name": "owner-repo",
  "owner": {"name": "owner"},
  "plugins": [{
    "name": "skill-name",
    "description": "...",
    "version": "1.0.0",
    "source": "./"
  }]
}
```

## Installation Methods

Users install skills in three ways:

1. **skills.sh** (recommended): `npx skills add owner/repo -g -y`
2. **Manual clone**: `git clone ... ~/.claude/skills/skill-name`
3. **Plugin marketplace**: `/plugin marketplace add owner/repo`

## Versioning (semver)

- **Patch** (1.0.x): Bug fixes, typo corrections, documentation updates
- **Minor** (1.x.0): New features, additional references, non-breaking changes
- **Major** (x.0.0): Breaking changes (renamed commands, restructured workflows, removed features)

Update the version in both `plugin.json` and `marketplace.json`.

## Publishing Checklist

Before publishing:

1. SKILL.md has complete frontmatter (name + description with trigger phrases)
2. All referenced files exist (scripts, references, assets)
3. No hardcoded paths, secrets, or PII
4. No remaining TODO or template placeholders
5. Scripts follow JSON output convention
6. README has installation instructions and usage examples
7. LICENSE file present
8. .gitignore excludes .env, __pycache__, .venv, .DS_Store

## Multi-Skill Repositories

For collections of related skills (like better-skills), use a monorepo:

```
better-skills/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/
│   ├── skill-a/
│   ├── skill-b/
│   └── skill-c/
└── README.md
```

All skills share one `plugin.json` and `marketplace.json`. Skills are auto-discovered from the `skills/` directory.
