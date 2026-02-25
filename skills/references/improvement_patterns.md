# Improvement Patterns Knowledge Base

Organized by category. Each pattern includes: what to look for, why it matters, and how to fix it.

## Description Quality

### Short or vague description
**Look for:** `description_length < 50` or generic terms like "helps with" without specifics.
**Why:** The description is the primary activation signal. Claude decides whether to invoke a skill based almost entirely on the description. Vague descriptions lead to missed activations or false triggers.
**Fix:** Expand to 100–200 chars. Include: what the skill does, when to use it, and 2–3 trigger phrases in quotes.

**Before:**
```yaml
description: "A skill for working with APIs"
```
**After:**
```yaml
description: "Validate and test REST API endpoints with automated contract checks, response schema validation, and performance benchmarking. This skill should be used when testing APIs, validating response schemas, or when the user says 'check my API', 'test endpoint', '测试接口'."
```

### Missing trigger phrases
**Look for:** `description_has_trigger_phrases: false`
**Why:** Without trigger phrases, Claude may not know what user input should activate the skill.
**Fix:** Add "when the user says '...'" or "Use when..." patterns. Include both English and Chinese if targeting bilingual users.

### Second-person voice
**Look for:** "you", "your" in description.
**Why:** Descriptions are consumed by Claude (an AI), not by users directly. Third-person voice ("This skill validates...") is clearer for AI consumption.

## Workflow Clarity

### No workflow section
**Look for:** Missing `## Workflow`, `## How It Works`, or `## Process` section.
**Why:** Without a clear step-by-step process, Claude must improvise the execution flow, leading to inconsistent behavior.
**Fix:** Add a numbered workflow section. Each step should be a clear action with expected inputs/outputs.

### Missing AskUserQuestion guidance
**Look for:** Interactive skills without mention of `AskUserQuestion`.
**Why:** Skills that need user input should explicitly instruct Claude to use AskUserQuestion rather than free-form questions. This ensures consistent UX with structured choices.

### Overly long SKILL.md
**Look for:** `total_lines > 300` with content that belongs in references.
**Why:** SKILL.md loads into context every time the skill activates. Detailed reference material should be in `references/` and loaded on demand.
**Fix:** Move detailed docs to `references/<topic>.md`, keep SKILL.md under 200 lines with just the workflow and essential context.

## Runtime Robustness

### Missing preflight
**Look for:** L0+/L1 skill with `has_preflight: false`.
**Why:** Without preflight, Claude discovers missing dependencies only when a command fails mid-workflow, leading to confusing error messages and wasted user time.
**Fix:** Add a `preflight` subcommand that checks all dependencies, credentials, and services. Return standardized JSON:
```json
{"ready": true, "dependencies": {...}, "credentials": {...}, "services": {...}}
```
Also add a **Check → Fix table** in SKILL.md so each preflight failure has a specific remediation (e.g., "Chrome not found → Install Chrome or set `CHROME_PATH`"). Generic "preflight failed" without per-item guidance is insufficient.

### No setup separation
**Look for:** L1 skill with `has_setup: false`.
**Why:** First-time setup (installing deps, creating config files) should be a separate step from business logic. Mixing them makes errors harder to diagnose.
**Fix:** Add a `setup` subcommand that handles one-time initialization. Document automatic vs. manual steps separately.

### No degradation handling
**Look for:** `has_degradation: false` in skills with optional features or external dependencies.
**Why:** When an optional dependency is unavailable, the skill should gracefully degrade rather than fail entirely. Without explicit degradation rules, Claude doesn't know which features are optional.
**Fix:** Add a Degradation section listing which features can be skipped, with fallback behavior for each.

### No troubleshooting section
**Look for:** `has_troubleshooting: false`.
**Why:** Common issues recurring across sessions waste user time. A troubleshooting table lets Claude quickly diagnose and fix known problems.
**Fix:** Add a table: Symptom | Likely Cause | Fix.

## Script Quality

### No JSON output pattern
**Look for:** Scripts without `json.dumps` or structured echo.
**Why:** Unstructured text output forces Claude to parse free-form text, which is unreliable. JSON output lets Claude extract exact values.
**Fix:** Use `json.dumps()` for all stdout output. Include a `hint` field with human-readable summaries.

### No error handling to stderr
**Look for:** Errors printed to stdout or no error handling at all.
**Why:** Mixing errors with normal output makes parsing impossible. Claude needs to distinguish success from failure programmatically.
**Fix:** Write error JSON to stderr: `{"error": "code", "hint": "...", "recoverable": true/false}`. Use exit code 1 for recoverable, 2 for fatal.

### No token awareness
**Look for:** Scripts that dump unbounded data without `--limit` or `--format` options.
**Why:** Large outputs consume context window tokens and slow down Claude's reasoning.
**Fix:** Add `--limit N` and `--format concise|detailed|json` flags. Default to concise with reasonable limits.

## Documentation

### Unfinished-work placeholders remaining
**Look for:** `todo_count > 0`.
**Why:** Unfinished-work markers indicate incomplete sections. They confuse users and reduce confidence in the skill.
**Fix:** Replace each placeholder with actual content or remove the section if not applicable.

### Unresolved template placeholders
**Look for:** `template_placeholder_count > 0`.
**Why:** `{{PLACEHOLDER}}` markers mean the scaffold generation didn't complete properly. These will appear as literal text in the skill.
**Fix:** Replace each `{{PLACEHOLDER}}` with the intended value.

### Poor reference file naming
**Look for:** Generic names like `commands.md`, `reference.md`, `guide.md`.
**Why:** Claude and users should understand a file's contents from its name alone.
**Fix:** Use the pattern `<content-type>_<specificity>.md`. Example: `api_endpoints.md`, `database_schema.md`.

## User Experience

### Long-running operations not in background mode
**Look for:** Skills with download dashboards, web UIs, or server processes that aren't marked for background execution.
**Why:** If Claude runs a long-lived process synchronously, it blocks the conversation — the user gets no feedback, and Claude can't continue with follow-up actions.
**Fix:** In SKILL.md, explicitly instruct Claude to run long-running commands with `run_in_background: true`. Example: `**run this command in the background** (use run_in_background: true in Bash) since the dashboard is a long-running server process`.

### No post-completion status reporting
**Applies when:** Skill produces artifacts (files, downloads, API mutations, published drafts). Skip for purely informational skills (config wizards, research, audits that only print results).
**Look for:** `has_completion_report: false` in profile, combined with file-creation or API-mutation operations.
**Why:** Users shouldn't have to search the filesystem for output files. After any operation that produces artifacts, the skill should report: file path, file size, and any remaining quotas or limits.
**Fix:** Add a structured Completion Report section in SKILL.md with a template covering: Input, Method, Result, Files created, and Next Steps. See `best_practices.md` for the full template.

### No progress checklist for multi-step workflows
**Applies when:** Workflow has 4+ sequential steps. Skip for simple 1-3 step or non-linear workflows.
**Look for:** `has_checklist: false` in profile, combined with 4+ step headings.
**Why:** Without visible progress tracking, users lose context in long workflows. If interrupted, there's no way to see where things left off. Claude may also skip or repeat steps.
**Fix:** Add a checklist block at the start of the workflow section:
```
Progress:
- [ ] Step 1: ...
- [ ] Step 2: ...
```

### Rigid input requirements
**Applies when:** Skill accepts file or content input from the user. Skip for dialogue-driven skills with no file input (e.g., config wizards, skill-creator).
**Look for:** `has_input_adaptation: false` in profile, combined with file path parameters in the workflow.
**Why:** Users provide input in whatever form they have. Rejecting valid-but-wrong-format input creates unnecessary friction. Skills that auto-detect and convert input types feel dramatically more polished.
**Fix:** Add input type detection logic. Accept multiple formats and convert as needed.

**Before:**
```markdown
## Input
Provide a markdown file path.
```
**After:**
```markdown
## Input Detection
| Input Type | Detection | Action |
|------------|-----------|--------|
| HTML file | `.html` extension | Skip conversion, proceed |
| Markdown file | `.md` extension | Convert to HTML first |
| Plain text | Not a file path | Save as markdown, then convert |
```

### No user preference persistence
**Applies when:** Skill has recurring per-user config (theme, author, output dir) that stays the same across sessions. Skip for skills where each invocation genuinely needs fresh parameters (e.g., skill-creator collects different name/level each time).
**Look for:** `has_preference_persistence: false` in profile, combined with repeated configuration questions across sessions.
**Why:** Repeating configuration is tedious. Users expect their choices to be remembered. First-time setup should happen once, not every time.
**Fix:** Separate secrets from preferences:
- **Secrets** (API tokens, keys) → `.env` file, loaded by scripts, stays in `.gitignore`
- **Preferences** (theme, author, default flags) → config file (e.g., `EXTEND.md`), safe to version control

Both use the same discovery pattern: project-level (`<cwd>/.baoyu-skills/<skill>/`) → user-level (`$HOME/.baoyu-skills/<skill>/`). On first run, guide the user through setup and let them choose which level to save to. On subsequent runs, load silently. See `best_practices.md` for the full convention.

### Missing cross-skill dependency handling
**Applies when:** SKILL.md references or invokes another skill by name. Skip for self-contained skills.
**Look for:** `has_cross_skill_handling: false` in profile, combined with other skill names in the content.
**Why:** Users may not have all skills installed. A hard failure with a cryptic error is a poor experience. Offering installation instructions or a manual workaround respects the user's time.
**Fix:** Check for dependency skills at workflow start. If missing, present options: install the dependency, provide alternative input manually, or cancel. Never hard-fail without guidance.

### No language matching
**Applies when:** Skill is published publicly or targets multilingual users. Skip for personal/internal skills with a single-language audience.
**Look for:** `has_language_section: false` in profile.
**Why:** Users expect responses in their own language. A skill that always replies in English alienates Chinese-speaking users, and vice versa.
**Fix:** Add a Language section at the top of SKILL.md: `**Match user's language**: Respond in the same language the user uses.`

## Setup Flow Integrity

### Preflight circular dependency (bootstrap safety)
**Look for:** Preflight command uses a tool/library to format output that is itself one of the dependencies being checked.
**Why:** If the tool is missing, preflight crashes before it can report the problem. The user gets an opaque shell error instead of actionable guidance.
**Fix:** Use plain printf/echo for output when checked dependencies are also used for formatting. Only use the dependency after confirming it's available.

### Preflight only checks existence, not validity
**Look for:** Preflight checks `if env_var is not empty` but never makes a test API call or login attempt.
**Why:** A user could enter wrong credentials, pass preflight, and only discover the error on first real use. First-time UX is ruined.
**Fix:** Add a lightweight live validation step — one API call per credential. If too expensive, at least validate format (regex pattern match).

### Missing .gitignore for credential files
**Look for:** Skill directory or repo root has no `.gitignore`, or `.gitignore` doesn't cover `.env` files.
**Why:** `.env` files containing API keys or passwords will be committed and potentially pushed to public repos.
**Fix:** Add `.gitignore` with `.env`, `.env.*`, `*.pyc`, `__pycache__/`, `.cache/`.

### Dual-path credential confusion
**Look for:** SKILL.md says "edit .env file" but script error messages say "run: script config set --key VALUE". Or multiple config locations with unclear precedence.
**Why:** Users and Claude get conflicting guidance. One path may work while the other silently does nothing.
**Fix:** Pick one canonical configuration method. Make all error messages, SKILL.md, and help text point to the same method.

### Config overwrite without backup (setup skills)
**Look for:** L0 setup skills that write config files (mkdir -p + write) without checking if files already exist.
**Why:** Users lose their existing customizations with no warning and no way to recover.
**Fix:** Check for existing files, offer backup/skip/merge, provide rollback instructions.

### Stale token not falling back to fresh login
**Look for:** Scripts that cache auth tokens and use cached token directly without fallback to re-authentication when the cached token expires.
**Why:** Token expiration is inevitable. If the code doesn't fall back to email/password re-login, users hit a dead end with "login failed" even though valid credentials exist.
**Fix:** Try cached token → on failure, try fresh login with stored credentials → only die if both fail.

## Security

### Hardcoded user paths
**Look for:** Absolute paths containing platform-specific user directories (e.g. `~` expanded to full paths).
**Why:** These break on other machines and leak personal information in public skills.
**Fix:** Use relative paths, environment variables, or `~/.claude/<skill-name>/` conventions.

### Credentials in code
**Look for:** API keys, tokens, or passwords in script files.
**Why:** Hardcoded secrets are a critical security risk. They get committed to git and shared publicly.
**Fix:** Use environment variables (`os.environ.get("API_KEY")`) or config files (`~/.claude/<skill-name>/.env`). Provide a `.env.example` template.
