---
name: skill-review
description: "Review a agent skill by running automated validation checks and suggesting improvements based on best practices. Combines structural validation (graded report with pass/warn/fail checks) with analytical improvement suggestions (prioritized with before/after examples). Can interactively apply fixes. This skill should be used when reviewing a skill, validating skill structure, improving skill quality, checking skill conventions, or when the user says 'review skill', 'validate skill', 'check skill', 'improve skill', 'iterate on skill', '走查技能', '验证技能', '检查 skill', '改进技能', '优化 skill'."
---

# Skill Review

Review a agent skill by combining automated validation with analytical improvement suggestions. Produces a graded report, identifies quality issues, and can interactively apply fixes.

## How It Works

1. Identify the skill to review
2. Run automated validation checks with `validate.py`
3. Extract a structured profile with `analyze.sh`
4. Read the skill content and compare against improvement patterns
5. Present findings: grade, issues, and prioritized suggestions
6. Interactively apply improvements if the user agrees

## Dialogue Flow

### Step 1: Identify the Skill

Ask the user for the skill directory path. Auto-detect if the current working directory contains a SKILL.md. Accept absolute or relative paths.

### Step 2: Automated Validation

Run the validator to get a graded report:

```bash
python3 {SKILL_DIR}/scripts/validate.py run --path <skill-path>
```

Where `{SKILL_DIR}` is the directory containing this SKILL.md file.

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

### Step 3: Profile Extraction

Run the analyzer to get a structured skill profile:

```bash
bash {SKILL_DIR}/scripts/analyze.sh analyze <skill-path>
```

The script outputs JSON with quantitative facts about the skill: level, section headings, script inventory, feature flags, unfinished-placeholder count, etc.

### Step 4: Deep Analysis

Read the target skill's SKILL.md file directly (using the Read tool) to understand its full content, purpose, and workflow. If the skill has scripts or references, read key files as needed.

Then read `references/improvement_patterns.md` to load the knowledge base of common improvement patterns.

### Step 5: Present Findings

Format the report for the user in this order:

1. **Grade and summary** — Show the letter grade (A/B/C/D/F) and score line from validation
2. **Failures** — List all `fail` severity checks with their `fix` suggestions
3. **Warnings** — List all `warn` severity checks
4. **Improvement suggestions** — Beyond pass/fail checks, compare the skill against improvement patterns and suggest enhancements:
   - What to change and why
   - A concrete before/after example or specific instruction
   - Which file to edit
   - Priority: High (affects functionality/UX), Medium (convention violations), Low (polish)

If the grade is A or B with no improvement suggestions, congratulate and suggest publishing with `skill-publish`.

### Step 6: Interactive Improvement

After presenting findings, ask the user which issues and suggestions to address. Options:

- **Fix all** — Apply all suggested changes
- **Pick and choose** — Let the user select specific items
- **None** — Just use the analysis as a reference

For each selected item, make the edit directly (using file editing tools), then confirm the change. After all selected changes, optionally re-run `validate.py` to show the updated grade.

## Check Categories (Automated Validation)

| Category | What it checks |
|----------|----------------|
| **structure** | SKILL.md exists, frontmatter present, required fields |
| **naming** | Kebab-case, length, no consecutive hyphens, matches directory |
| **content** | Description quality, trigger phrases, workflow section |
| **paths** | Referenced files exist, scripts have execute permission |
| **scripts** | JSON output pattern, preflight subcommand, error handling |
| **security** | No hardcoded paths, no secrets, no PII patterns |
| **completeness** | No unfinished placeholders, no template markers |

## Grading

- **A** — All checks pass, zero warnings
- **B** — All checks pass, some warnings
- **C** — 1–2 failures
- **D** — 3+ failures
- **F** — SKILL.md missing or no valid frontmatter

## Analysis Dimensions (Improvement Suggestions)

| Dimension | What to evaluate |
|-----------|-----------------|
| **Description quality** | Length, trigger phrases, third-person voice, specificity |
| **Workflow clarity** | Numbered steps, decision points, AskUserQuestion usage |
| **Runtime robustness** | Preflight completeness, setup separation, degradation handling |
| **Script quality** | JSON output, error handling, token awareness, exit codes |
| **Documentation** | Troubleshooting tables, reference organization, no TODOs |
| **Security** | Credential handling, no hardcoded paths or secrets |

## References

For the rationale behind each validation check, read `references/validation_rules.md`.

For the full knowledge base of improvement patterns with examples, read `references/improvement_patterns.md`.

For skill design conventions and quick reference, read `references/best_practices.md`.
