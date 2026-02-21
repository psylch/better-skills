# Validation Rules Reference

Rationale and examples for each check in validate.py. Read this when users ask "why is this a warning?" or need deeper context on a specific rule.

## Structure Checks

### skill_md_exists (fail)
SKILL.md is the only required file in a skill. Without it, the skill cannot be discovered or activated.

### frontmatter_exists (fail)
YAML frontmatter (`---` delimited block at the top) is how the skill system identifies the skill name and description. Without frontmatter, the skill is invisible to Claude.

### frontmatter_name / frontmatter_description (fail)
Both `name` and `description` are required fields. `name` identifies the skill; `description` determines when Claude activates it.

### directory_layout (warn)
Standard directories are: `scripts/`, `references/`, `templates/`, `assets/`. Other directories may work but deviate from convention, making the skill harder for others to understand.

## Naming Checks

### name_kebab_case (fail)
Skill names must be lowercase kebab-case (`my-skill`). This ensures consistency across installations, file systems, and URLs.

**Good:** `cors-audit`, `tech-research`, `hifi-download`
**Bad:** `CorsAudit`, `cors_audit`, `CORS-Audit`

### name_length (fail)
Maximum 64 characters. Longer names cause issues in file paths and UI display.

### name_no_consecutive_hyphens (fail)
Consecutive hyphens (`my--skill`) suggest a typo and cause URL/path issues.

### name_matches_directory (warn)
The frontmatter `name` should match the directory name. Mismatches cause confusion when installing and referencing the skill.

## Content Checks

### description_length (warn)
Descriptions under 50 characters are too terse to give Claude enough context for activation. Aim for 100–200 characters covering: what the skill does, when to use it, and example trigger phrases.

### description_trigger_phrases (warn)
Including phrases like "Use when..." or "when the user says '...'" helps Claude understand when to activate the skill. Without these, the skill may not trigger at the right time.

### description_third_person (warn)
Descriptions should use third-person voice ("This skill validates..." not "You can validate..."). This is an AI consumption convention — Claude reads descriptions to decide whether to activate.

### workflow_section (warn)
A Workflow, How It Works, or Process section gives Claude the step-by-step procedure to follow. Without it, Claude must improvise the execution flow.

## Path Checks

### referenced_files_exist (fail)
If SKILL.md mentions `scripts/main.py` or `references/guide.md`, those files must exist. Missing files cause runtime errors when Claude tries to execute or read them.

### scripts_executable (warn)
Shell scripts (`.sh`) need execute permission to run directly. Without it, Claude must use `bash scripts/helper.sh` instead of `./scripts/helper.sh`.

## Script Checks

### script_json_output (warn)
Scripts should output structured JSON (via `json.dumps` or `echo '{...}'`). This follows the MCP tool convention and allows Claude to parse results programmatically.

### script_preflight (warn)
A `preflight` subcommand checks environment readiness before running business logic. This prevents confusing runtime errors by catching missing dependencies early.

### script_error_handling (warn)
Errors should be written to stderr as JSON with `error`, `hint`, and `recoverable` fields. This allows Claude to distinguish errors from normal output and take appropriate action.

### script_exit_codes (warn)
Convention: exit 0 = success, exit 1 = recoverable error (Claude can retry or fix), exit 2 = fatal error (user must intervene).

## Security Checks

### no_hardcoded_paths (warn)
Absolute paths like `/Users/<username>/` or `/home/<username>/` break on other machines and leak personal information. Use relative paths or environment variables.

### no_secrets (fail)
API keys, tokens, and credentials must never be hardcoded. Use environment variables (`$API_KEY`) or config files (`~/.claude/<skill-name>/.env`).

### no_pii (warn)
Personal email addresses and other PII should not appear in public skills. Use placeholders like `user@example.com`.

## Completeness Checks

### no_todo_placeholders (warn)
Unfinished-work markers (e.g. `T0D0`) indicate incomplete sections. Replace them before publishing.

### no_template_placeholders (fail)
`{{PLACEHOLDER}}` markers are template variables that should have been replaced during scaffold generation. Their presence indicates a broken generation process.
