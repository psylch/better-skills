---
name: skill-creator
description: "Create new agent skills with best-practice templates. Guides through skill level selection (L0 pure prompt, L0+ with helper scripts, L1 with business scripts), environment strategy (stdlib/uv/venv), and generates ready-to-edit project files following runtime UX best practices. This skill should be used when creating a new skill, scaffolding a skill project, initializing skill templates, or when the user says 'help me build a skill', 'create a skill', '创建技能', '新建 skill'."
---

# Skill Creator

Create new agent skills by guiding the user through a series of choices, then generating a ready-to-edit project structure with best practices baked in.

## How It Works

1. Collect requirements through dialogue (AskUserQuestion)
2. Call `scaffold.py` with the collected parameters (non-interactive)
3. Report what was generated and guide next steps

## Dialogue Flow

Follow these steps in order. Use AskUserQuestion for steps 1–4.

### Step 1: Skill Name

Ask the user for a skill name. Validate it meets these rules:
- Lowercase letters, digits, and hyphens only
- Must start with a letter, end with a letter or digit
- No consecutive hyphens
- Maximum 64 characters

If invalid, explain the constraint and ask again.

### Step 2: Skill Level

Ask the user to choose a skill level:

**L0 — Pure Prompt**: Only a SKILL.md file. All capabilities come from Claude's built-in tools, MCP servers, or general knowledge. Best for workflow guides, domain knowledge, configuration wizards. No scripts needed.

**L0+ — Prompt + Helper Scripts**: SKILL.md plus lightweight helper scripts for environment detection, status caching, or other auxiliary tasks. Core logic stays in the prompt. Best when Claude needs a preflight check or a small utility but handles business logic itself.

**L1 — Prompt + Business Scripts**: SKILL.md orchestrates CLI scripts that handle core business logic. Scripts accept parameters, return structured JSON, and follow MCP tool design principles. Best for skills that interact with APIs, process data, or perform operations that benefit from deterministic code.

### Step 3: Environment Strategy (L1 only)

If the user chose L1, ask which environment strategy to use:

**stdlib** — Python standard library only. Zero dependencies, zero environment issues. Choose this when `urllib`, `json`, `argparse`, `pathlib` are sufficient. This is the recommended default.

**uv** — Dependencies declared inline via PEP 723, executed with `uv run`. No persistent venv, global cache, version-isolated. Choose this when external packages are needed but a full venv is overkill.

**venv** — Traditional per-skill virtual environment with `run.sh` wrapper. Choose this only when dependencies require C extensions, or the skill runs long-lived processes.

### Step 4: Output Directory

Ask where to generate the skill. Default: current working directory. The script creates `skills/<name>/` under this directory.

## Generate

After collecting all parameters, run:

```bash
python3 {SKILL_DIR}/scripts/scaffold.py \
    --name <name> \
    --level <level> \
    [--env <strategy>] \
    --output <dir>
```

Where `{SKILL_DIR}` is the directory containing this SKILL.md file. Resolve it at runtime.

The script outputs JSON to stdout:
```json
{
  "status": "ok",
  "level": "l1",
  "env": "uv",
  "created": ["skills/my-skill/SKILL.md", "skills/my-skill/scripts/main.py", ...],
  "hint": "..."
}
```

If it fails, stderr contains JSON with `error`, `hint`, and `recoverable` fields.

## Post-Generation Guidance

After successful generation, tell the user:

1. **Edit SKILL.md** — Replace all `TODO` placeholders. The `description` field in frontmatter is critical — it determines when Claude activates the skill. Be specific and include trigger phrases.

2. **Customize scripts/** (L0+/L1) — The generated scripts are functional frameworks with TODO markers. Add your business logic.

3. **Test preflight** (L0+/L1) — Run the preflight command to verify the JSON output structure works:
   - L0+: `bash scripts/helper.sh preflight`
   - L1 stdlib: `python3 scripts/main.py preflight`
   - L1 uv: `uv run scripts/main.py preflight`
   - L1 venv: `bash scripts/run.sh preflight` (after setup)

4. **Add references/** — Put detailed reference documents here and reference them from SKILL.md with file read instructions. Keep SKILL.md lean.

5. **Ready to publish?** — Use the `skill-publish` skill (if installed) to wrap this into a complete GitHub repo with README, LICENSE, plugin.json, and marketplace.json.

## Best Practices Reference

For deeper questions about skill design — output formats, error handling patterns, environment strategies, preflight conventions — read `references/best_practices.md`.
