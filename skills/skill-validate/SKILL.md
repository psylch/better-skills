---
name: skill-validate
description: "Validate an existing Claude Code skill's structure, conventions, and runtime readiness. Checks SKILL.md frontmatter, naming conventions, description quality, path integrity, script output contracts, security patterns, and best-practice compliance. Produces a graded report with actionable fix suggestions. This skill should be used when verifying a skill before publishing, reviewing skill quality, checking skill structure, or when the user says 'validate skill', 'check skill', '验证技能', '检查 skill'."
---

# Skill Validate

Validate a Claude Code skill directory against best-practice conventions. Produces a structured report with pass/warn/fail checks, an overall grade, and actionable fix suggestions.

## How It Works

1. Identify the skill directory to validate
2. Run `validate.py` to perform automated checks
3. Present the report, highlighting failures first
4. Suggest specific fixes for any issues found

## Dialogue Flow

### Step 1: Identify the Skill

Ask the user for the skill directory path. Auto-detect if the current working directory contains a SKILL.md (meaning the user is already inside a skill directory). Accept absolute or relative paths.

### Step 2: Run Validation

```bash
python3 {SKILL_DIR}/scripts/validate.py run --path <skill-path>
```

Where `{SKILL_DIR}` is the directory containing this SKILL.md file. Resolve it at runtime.

For detailed output with fix suggestions:
```bash
python3 {SKILL_DIR}/scripts/validate.py run --path <skill-path> --format detailed
```

For strict mode (warnings treated as failures):
```bash
python3 {SKILL_DIR}/scripts/validate.py run --path <skill-path> --strict
```

The script outputs JSON to stdout:
```json
{
  "status": "ok",
  "path": "/path/to/skill",
  "score": {"total": 22, "pass": 18, "warn": 3, "fail": 1},
  "grade": "B",
  "checks": [
    {"id": "skill_md_exists", "category": "structure", "severity": "pass", "message": "SKILL.md found"}
  ],
  "hint": "18/22 checks passed, 3 warnings, 1 failure."
}
```

### Step 3: Present the Report

Format the report for the user:

1. **Grade and summary** — Show the letter grade (A/B/C/D/F) and score line
2. **Failures first** — List all `fail` severity checks with their `fix` suggestions
3. **Warnings** — List all `warn` severity checks
4. **Passes** — Optionally list passes if user asks for the full report

If the grade is A or B, congratulate and suggest publishing with `skill-publish`.
If there are failures, offer to help fix them directly (Claude can edit the files).

## Check Categories

| Category | What it checks |
|----------|----------------|
| **structure** | SKILL.md exists, frontmatter present, required fields |
| **naming** | Kebab-case, length, no consecutive hyphens, matches directory |
| **content** | Description quality, trigger phrases, workflow section |
| **paths** | Referenced files exist, scripts have execute permission |
| **scripts** | JSON output pattern, preflight subcommand, error handling |
| **security** | No hardcoded paths, no secrets, no PII patterns |
| **completeness** | No TODO placeholders, no template markers |

## Grading

- **A** — All checks pass, zero warnings
- **B** — All checks pass, some warnings
- **C** — 1–2 failures
- **D** — 3+ failures
- **F** — SKILL.md missing or no valid frontmatter

## Validation Rules Reference

For the rationale behind each check rule, read `references/validation_rules.md`.
