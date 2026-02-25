---
name: better-skill-review
description: "Review a agent skill by combining automated linting with structured semantic analysis. Runs hard-rule validation, evaluates contextual findings, then performs deep review against best practices (description quality, workflow design, runtime robustness, script conventions, UX patterns). Produces actionable improvement suggestions with before/after examples. This skill should be used when reviewing a skill, validating skill structure, improving skill quality, checking skill conventions, or when the user says 'review skill', 'validate skill', 'check skill', 'improve skill', 'iterate on skill', '走查技能', '验证技能', '检查 skill', '改进技能', '优化 skill'."
---

# Skill Review

## Language

**Match user's language**: Respond in the same language the user uses.

## Overview

Review a agent skill through three layers: automated linting (hard rules), contextual finding evaluation (agent judges with context), and structured semantic review (deep analysis against best practices). The linter catches mechanical issues; the agent catches design issues.

## Dialogue Flow

Progress:
- [ ] Step 1: Identify the skill
- [ ] Step 2: Automated linting (hard rules)
- [ ] Step 3: Profile extraction
- [ ] Step 4: Contextual findings review (agent judges)
- [ ] Step 5: Semantic review (deep analysis)
- [ ] Step 6: Present findings
- [ ] Step 7: Interactive improvement

### Step 1: Identify the Skill

Accept the skill location as a directory path containing SKILL.md. Auto-detect if the current working directory contains one.

### Step 2: Automated Linting

Run the validator for hard-rule checks:

```bash
python3 {SKILL_DIR}/scripts/validate.py run --path <skill-path>
```

The output contains two arrays:

- **`checks`**: Hard-rule verdicts (pass/warn/fail) — mechanical, unambiguous. These determine the linter grade.
- **`findings`**: Soft detections (data + context_hint) — need your judgment. No verdict yet.

Record the linter grade. Failures must be fixed; warnings are convention issues.

### Step 3: Profile Extraction

Run the analyzer for structured facts:

```bash
bash {SKILL_DIR}/scripts/analyze.sh analyze <skill-path>
```

Note the skill level (l0/l0plus/l1) and feature flags — you'll need these for Steps 4 and 5.

### Step 4: Contextual Findings Review

For each finding from Step 2, read the `context_hint` and examine the actual locations. Judge whether each is a real issue:

| Finding | Is a problem | Not a problem |
|---------|-------------|---------------|
| `todo_markers` | In SKILL.md body, script logic, or description | In `.tmpl` template files (intentional scaffolding) |
| `hardcoded_paths` | In scripts or SKILL.md prose | In `references/` docs as illustrative examples |
| `pii_patterns` | Real personal emails in scripts/configs | Example emails in docs (`user@example.com` pattern) |
| `script_conventions` | L0+/L1 skill missing expected patterns | L0 pure-prompt skill with no scripts — skip entirely |

Promote findings you judge as real issues to warnings. Dismiss the rest with a brief note.

### Step 5: Semantic Review

This is where real value is delivered. Read the skill's SKILL.md fully, then evaluate each dimension below. For each, give a score (0-3) and specific feedback.

**Scoring**: 3 = excellent, 2 = adequate, 1 = needs improvement, 0 = missing/broken

#### 5.1 Description Quality (/3)

Read the frontmatter `description` field.

- [ ] Length ≥ 100 chars? (50-100 acceptable, <50 needs expansion)
- [ ] Contains trigger phrases? ("when the user says...", "Use when...")
- [ ] Third-person voice? (not "you/your" — description is consumed by AI)
- [ ] Specific about what the skill does, not vague ("helps with APIs")

→ Reference: `references/improvement_patterns.md` § Description Quality

#### 5.2 Workflow Design (/3)

Read the workflow/process sections.

- [ ] Clear numbered steps with defined inputs/outputs?
- [ ] Decision points explicit? (if X then Y, else Z)
- [ ] Interactive steps specify AskUserQuestion where needed?
- [ ] SKILL.md total lines < 200? (if over, detailed content should be in `references/`)

→ Reference: `references/improvement_patterns.md` § Workflow Clarity

#### 5.3 Runtime Robustness (/3)

**Only for L0+/L1 skills with scripts.** Score 3 automatically for L0 pure-prompt skills.

- [ ] Preflight covers all dependencies, credentials, services?
- [ ] Preflight failures have a Check → Fix table with specific remediation per item?
- [ ] Setup separated from business logic? (first-time init vs. daily use)
- [ ] Degradation strategy defined for optional dependencies?
- [ ] Troubleshooting table present? (Symptom | Resolution)

→ Reference: `references/best_practices.md` § Preflight Standard, § Degradation Patterns

#### 5.4 Script Quality (/3)

**Only for skills with scripts.** Score 3 automatically for L0 skills without scripts.

- [ ] stdout JSON with `hint` field for all output?
- [ ] stderr JSON error handling with `error`, `hint`, `recoverable` fields?
- [ ] Exit codes: 0=success, 1=recoverable, 2=fatal?
- [ ] Token awareness: `--limit` or bounded output to avoid context explosion?

→ Reference: `references/best_practices.md` § Script Output Convention, § Token Awareness

#### 5.5 UX Practices (/3)

**Check the Applicability Matrix first** — only evaluate practices that apply to this skill. A missing practice with no applicable condition is the expected state, not a problem.

| Practice | Applies when | Skip when |
|----------|-------------|-----------|
| Language Matching | Published publicly or multilingual audience | Personal/single-language skill |
| Progress Checklist | 4+ sequential workflow steps | Simple 1-3 step or non-linear |
| Completion Report | Produces artifacts (files, API mutations) | Purely informational (research, audit) |
| Input Adaptation | Accepts file/content input from user | Dialogue-driven, no file input |
| Cross-skill Dependencies | References another skill by name | Self-contained |
| User Preferences | Recurring per-user config across sessions | Fresh parameters each invocation |

For each applicable practice that's missing, suggest adding it with a concrete example.

→ Reference: `references/best_practices.md` § UX Practices, § Applicability Matrix

### Step 6: Present Findings

Format the report:

```
[Skill Review] <skill-name>

═══ Linter ═══
Grade: <letter> (<pass>/<total> passed, <warn> warnings, <fail> failures)

Failures:
  ✗ <check_id>: <message> → Fix: <fix>

Warnings:
  ⚠ <check_id>: <message>

Findings (agent-reviewed):
  ✓ <finding_id>: dismissed — <reason>
  ⚠ <finding_id>: promoted to warning — <reason>

═══ Semantic Review ═══
5.1 Description Quality:   <score>/3  <one-line assessment>
5.2 Workflow Design:        <score>/3  <one-line assessment>
5.3 Runtime Robustness:     <score>/3  <one-line assessment>
5.4 Script Quality:         <score>/3  <one-line assessment>
5.5 UX Practices:           <score>/3  <one-line assessment>
                            ─────────
Semantic Score:             <total>/15

═══ Improvement Suggestions ═══
For each dimension scoring < 3, provide:
  1. What to change and why
  2. Which file to edit
  3. A concrete before/after example or specific instruction
  4. Priority: High (functionality/UX) / Medium (convention) / Low (polish)
```

If linter grade is A and semantic score ≥ 12: congratulate and suggest publishing with `better-skill-publish`.

### Step 7: Interactive Improvement

Ask the user which issues and suggestions to address:

- **Fix all** — Apply all suggested changes
- **Pick and choose** — Let the user select specific items
- **None** — Just use the analysis as a reference

For each selected item, make the edit directly, then confirm. After all changes, optionally re-run the linter to show updated results.

## Linter Check Categories

| Category | Checks (hard rules) |
|----------|-------------------|
| **structure** | SKILL.md exists, frontmatter present, required fields, directory layout |
| **naming** | Kebab-case, length, no consecutive hyphens, matches directory |
| **content** | Description length, body length, heading structure |
| **paths** | Referenced files exist, scripts have execute permission |
| **security** | No secrets (API key patterns), no template placeholders |

## Linter Grading

Grade is based on hard-rule checks only (not findings, not semantic review):

- **A** — All checks pass, zero warnings
- **B** — All checks pass, some warnings
- **C** — 1–2 failures
- **D** — 3+ failures
- **F** — SKILL.md missing or no valid frontmatter

## References

For the rationale behind each validation check, read `references/validation_rules.md`.

For the full knowledge base of improvement patterns with examples, read `references/improvement_patterns.md`.

For skill design conventions and quick reference, read `references/best_practices.md`.
