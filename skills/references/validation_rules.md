# Validation Rules Reference

Rationale for each check and finding in validate.py. Read this when users ask "why is this a warning?" or need deeper context on a specific rule.

## Hard-Rule Checks (Script Produces Verdicts)

These are mechanical, unambiguous checks. The script can definitively judge pass/fail without context.

### Structure Checks

#### skill_md_exists (fail)
SKILL.md is the only required file in a skill. Without it, the skill cannot be discovered or activated.

#### frontmatter_exists (fail)
YAML frontmatter (`---` delimited block at the top) is how the skill system identifies the skill name and description. Without frontmatter, the skill is invisible to Claude.

#### frontmatter_name / frontmatter_description (fail)
Both `name` and `description` are required fields. `name` identifies the skill; `description` determines when Claude activates it.

#### directory_layout (warn)
Standard directories are: `scripts/`, `references/`, `templates/`, `assets/`. Other directories may work but deviate from convention, making the skill harder for others to understand.

### Naming Checks

#### name_kebab_case (fail)
Skill names must be lowercase kebab-case (`my-skill`). This ensures consistency across installations, file systems, and URLs.

**Good:** `cors-audit`, `tech-research`, `hifi-download`
**Bad:** `CorsAudit`, `cors_audit`, `CORS-Audit`

#### name_length (fail)
Maximum 64 characters. Longer names cause issues in file paths and UI display.

#### name_no_consecutive_hyphens (fail)
Consecutive hyphens (`my--skill`) suggest a typo and cause URL/path issues.

#### name_matches_directory (warn)
The frontmatter `name` should match the directory name. Mismatches cause confusion when installing and referencing the skill.

### Content Checks

#### description_length (warn)
Descriptions under 50 characters are too terse to give Claude enough context for activation. Aim for 100–200 characters covering: what the skill does, when to use it, and example trigger phrases.

#### body_length (warn)
The SKILL.md body (after frontmatter) should be at least 10 lines. Shorter bodies typically lack sufficient instructions for Claude to execute the skill correctly.

#### heading_structure (warn)
SKILL.md should have at least 2 headings to provide organizational structure. A single heading or none suggests the instructions are unstructured.

### Path Checks

#### referenced_files_exist (fail)
If SKILL.md mentions `scripts/main.py` or `references/guide.md`, those files must exist. Missing files cause runtime errors when Claude tries to execute or read them.

#### scripts_executable (warn)
Shell scripts (`.sh`) need execute permission to run directly. Without it, Claude must use `bash scripts/helper.sh` instead of `./scripts/helper.sh`.

### Security Checks

#### no_secrets (fail)
API keys, tokens, and credentials must never be hardcoded. Use environment variables (`$API_KEY`) or config files (`~/.claude/<skill-name>/.env`).

### Completeness Checks

#### no_template_placeholders (fail)
`{{PLACEHOLDER}}` markers are template variables that should have been replaced during scaffold generation. Their presence indicates a broken generation process.

---

## Soft Findings (Script Detects, Agent Judges)

These findings need context to determine if they're real issues. The script provides data and location info; the reviewing agent reads the actual content and makes the call.

### todo_markers
**What it detects:** `TODO` markers anywhere in the skill directory.

**Why it's a finding, not a verdict:** TODO in a `.tmpl` template file is intentional scaffolding — the template is supposed to contain TODO markers for users to fill in. TODO in the actual SKILL.md body or script logic indicates unfinished work.

**Agent judgment guide:**
- `.tmpl` file → dismiss (intentional)
- SKILL.md description or workflow → promote to warning (unfinished)
- Script comment like `# TODO: Add error handling` → promote to warning
- Reference doc discussion of TODOs → dismiss (meta-discussion)

### hardcoded_paths
**What it detects:** Absolute paths like `/Users/<name>/` or `/home/<name>/`.

**Why it's a finding, not a verdict:** A `references/` doc might use `/Users/alice/project/` as an illustrative example. A script using `/Users/bob/.config/tool` is a real portability issue.

**Agent judgment guide:**
- In `references/` docs as examples → dismiss
- In scripts or SKILL.md prose as actual paths → promote to warning
- In `.env.example` as placeholder → dismiss

### pii_patterns
**What it detects:** Email addresses that don't match known non-PII patterns.

**Why it's a finding, not a verdict:** An email in a config example (`admin@yourcompany.com`) is different from a real personal email in a script.

**Agent judgment guide:**
- `@example.com`, `@yourcompany.com`, in `.env.example` → dismiss
- Real personal email in script or SKILL.md → promote to warning

### script_conventions
**What it detects:** Presence/absence of JSON output, preflight, stderr handling, and exit code patterns in scripts.

**Why it's a finding, not a verdict:** These conventions only apply to L0+/L1 skills that have scripts. An L0 pure-prompt skill with no scripts directory should not be flagged.

**Agent judgment guide:**
- L0 skill with no scripts → dismiss entirely
- L0+/L1 skill missing patterns → promote relevant items to suggestions in semantic review
