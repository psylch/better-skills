# Semantic Review Dimensions

Full checklist for each review dimension. The reviewing agent reads this to score each dimension 0-3.

**Scoring**: 3 = excellent, 2 = adequate, 1 = needs improvement, 0 = missing/broken

## 5.1 Description Quality (/3)

Read the frontmatter `description` field.

- [ ] Length ≥ 100 chars? (50-100 acceptable, <50 needs expansion)
- [ ] Contains trigger phrases? ("when the user says...", "Use when...")
- [ ] Third-person voice? (not "you/your" — description is consumed by AI)
- [ ] Specific about what the skill does, not vague ("helps with APIs")

→ Reference: `improvement_patterns.md` § Description Quality

## 5.2 Workflow Design (/3)

Read the workflow/process sections.

- [ ] Clear numbered steps with defined inputs/outputs?
- [ ] Decision points explicit? (if X then Y, else Z)
- [ ] Interactive steps specify AskUserQuestion where needed?
- [ ] SKILL.md total lines < 200? (if over, detailed content should be in `references/`)

→ Reference: `improvement_patterns.md` § Workflow Clarity

## 5.3 Runtime Robustness (/3)

**Only for L0+/L1 skills with scripts.** Score 3 automatically for L0 pure-prompt skills.

- [ ] Preflight covers all dependencies, credentials, services?
- [ ] Preflight failures have a Check → Fix table with specific remediation per item?
- [ ] Setup separated from business logic? (first-time init vs. daily use)
- [ ] Degradation strategy defined for optional dependencies?
- [ ] Troubleshooting table present? (Symptom | Resolution)

→ Reference: `best_practices.md` § Preflight Standard, § Degradation Patterns

## 5.4 Script Quality (/3)

**Only for skills with scripts.** Score 3 automatically for L0 skills without scripts.

- [ ] stdout JSON with `hint` field for all output?
- [ ] stderr JSON error handling with `error`, `hint`, `recoverable` fields?
- [ ] Exit codes: 0=success, 1=recoverable, 2=fatal?
- [ ] Token awareness: `--limit` or bounded output to avoid context explosion?

→ Reference: `best_practices.md` § Script Output Convention, § Token Awareness

## 5.5 UX Practices (/3)

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

→ Reference: `best_practices.md` § UX Practices, § Applicability Matrix

## 5.6 Setup Flow Integrity (/3)

**Applicability:** Applies to any skill that has a setup/preflight/configuration phase — including L0 setup skills (like terminal config wizards) and all L0+/L1 skills with scripts. Score 3 automatically ONLY for L0 skills that have no setup phase at all (e.g., pure research/informational skills).

This dimension evaluates whether a first-time user can go from zero to working without hitting dead ends. **Do not just check if pieces exist — trace the actual flow.**

- [ ] **Bootstrap safety**: Preflight does NOT depend on tools it's supposed to detect. (e.g., using `jq` to report `jq` is missing = circular dependency = 0 points)
- [ ] **Check-Fix completeness**: Every preflight check maps to a specific, actionable fix in SKILL.md — not just "check failed". Fix instructions include platform-specific commands.
- [ ] **Live validation**: Preflight tests that credentials/services actually work, not just that config values exist. (e.g., test API call, not just "env var is set")
- [ ] **Credential security**: `.gitignore` covers `.env` and sensitive files. No passwords passed via CLI args (shell history exposure). No plaintext secrets in committed files.
- [ ] **Setup separation**: First-time setup is clearly distinct from every-run workflow. No config mutations without user consent.
- [ ] **Error recovery**: Token/session expiration detected with clear re-auth guidance. Partial failures don't leave the skill in a broken state.
- [ ] **Single canonical path**: Only one way to configure credentials — not `.env` AND `config set` giving conflicting guidance in error messages.
- [ ] **Config safety** (for setup skills): Existing config files are detected and backed up before overwriting. User is offered backup/skip/merge choices.

→ Reference: `best_practices.md` § Setup Flow Integrity

---

## Finding Judgment Table

For each finding from the linter, read the `context_hint` and examine the actual locations. Judge whether each is a real issue:

| Finding | Is a problem | Not a problem |
|---------|-------------|---------------|
| `todo_markers` | In SKILL.md body, script logic, or description | In `.tmpl` template files (intentional scaffolding) |
| `hardcoded_paths` | In scripts or SKILL.md prose | In `references/` docs as illustrative examples |
| `pii_patterns` | Real personal emails in scripts/configs | Example emails in docs (`user@example.com` pattern) |
| `script_conventions` | L0+/L1 skill missing expected patterns | L0 pure-prompt skill with no scripts — skip entirely |

Promote findings you judge as real issues to warnings. Dismiss the rest with a brief note.

---

## Verification Subagent Prompt Template

When dispatching a verification subagent (Step 5), use this prompt structure:

```
You are an independent verification agent. Your job is to review a skill that was just modified and assess its current quality. You must form your own judgment — do not trust any prior assessment.

Skill path: <skill-path>
Review tools directory: <{SKILL_DIR}>

Steps:
1. Run: python3 <{SKILL_DIR}>/scripts/validate.py run --path <skill-path>
2. Run: bash <{SKILL_DIR}>/scripts/analyze.sh analyze <skill-path>
3. Read: <{SKILL_DIR}>/references/semantic_dimensions.md
4. Read the skill's SKILL.md and all scripts/references fully
5. Score each of the 6 dimensions (0-3), citing file:line as evidence
6. For any score < 3, list the specific checkbox that failed

Return format:
- Linter grade: <letter>
- Dimension scores: 5.1=X 5.2=X 5.3=X 5.4=X 5.5=X 5.6=X → Total: X/18
- PASS items: [list]
- FAIL items: [list with file:line evidence and specific failed checkbox]
```
