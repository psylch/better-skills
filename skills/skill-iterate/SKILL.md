---
name: skill-iterate
description: "Analyze an existing Claude Code skill and suggest improvements based on best practices. Reads the skill's SKILL.md, scripts, and references to identify quality issues, missing patterns, and optimization opportunities. Provides prioritized suggestions with before/after examples. This skill should be used when improving a skill, reviewing skill quality, optimizing skill performance, or when the user says 'improve skill', 'iterate on skill', 'review my skill', '改进技能', '优化 skill'."
---

# Skill Iterate

Analyze a Claude Code skill and suggest improvements based on runtime UX best practices. Combines automated profile extraction with analytical reasoning to produce prioritized, actionable improvement suggestions.

## How It Works

1. Identify the skill to analyze
2. Extract a structured profile with `analyze.sh`
3. Read the skill's SKILL.md content directly
4. Compare against improvement patterns from the knowledge base
5. Present findings: strengths, issues, and prioritized suggestions
6. Interactively apply improvements if the user agrees

## Dialogue Flow

### Step 1: Identify the Skill

Ask the user for the skill directory path. Auto-detect if the current working directory contains a SKILL.md. Accept absolute or relative paths.

### Step 2: Extract Profile

Run the analyzer to get a structured skill profile:

```bash
bash {SKILL_DIR}/scripts/analyze.sh <skill-path>
```

Where `{SKILL_DIR}` is the directory containing this SKILL.md file. The script outputs JSON with quantitative facts about the skill: level, section headings, script inventory, feature flags, TODO count, etc.

### Step 3: Read the Skill

Read the target skill's SKILL.md file directly (using the Read tool) to understand its full content, purpose, and workflow.

If the skill has scripts or references, read key files as needed for deeper analysis.

### Step 4: Load Improvement Patterns

Read `references/improvement_patterns.md` to load the knowledge base of common improvement patterns organized by category.

### Step 5: Analyze and Present

Compare the skill profile and content against improvement patterns. Present findings in this order:

1. **Strengths** — What the skill does well. Acknowledge good practices before suggesting changes.

2. **Issues by Priority**:
   - **High** — Problems that affect functionality or user experience (missing preflight, broken paths, no error handling)
   - **Medium** — Convention violations or quality gaps (poor description, missing workflow section, no degradation handling)
   - **Low** — Polish items (TODO placeholders, formatting, naming tweaks)

3. **Suggestions** — For each issue, provide:
   - What to change and why
   - A concrete before/after example or specific instruction
   - Which file to edit

### Step 6: Interactive Improvement

After presenting findings, ask the user which suggestions to implement. Options:

- **Fix all** — Apply all suggested changes
- **Pick and choose** — Let the user select specific suggestions
- **None** — Just use the analysis as a reference

For each selected suggestion, make the edit directly (using file editing tools), then confirm the change. After all selected changes, optionally re-run `analyze.sh` to show the updated profile.

## Analysis Dimensions

| Dimension | What to evaluate |
|-----------|------------------|
| **Description quality** | Length, trigger phrases, third-person voice, specificity |
| **Workflow clarity** | Numbered steps, decision points, AskUserQuestion usage |
| **Runtime robustness** | Preflight completeness, setup separation, degradation handling |
| **Script quality** | JSON output, error handling, token awareness, exit codes |
| **Documentation** | Troubleshooting tables, reference organization, no TODOs |
| **Security** | Credential handling, no hardcoded paths or secrets |

## Improvement Patterns Reference

For the full knowledge base of improvement patterns with examples, read `references/improvement_patterns.md`.
