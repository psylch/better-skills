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

### TODO placeholders remaining
**Look for:** `todo_count > 0`.
**Why:** TODO markers indicate unfinished work. They confuse users and reduce confidence in the skill.
**Fix:** Replace each TODO with actual content or remove the section if not applicable.

### Unresolved template placeholders
**Look for:** `template_placeholder_count > 0`.
**Why:** `{{PLACEHOLDER}}` markers mean the scaffold generation didn't complete properly. These will appear as literal text in the skill.
**Fix:** Replace each `{{PLACEHOLDER}}` with the intended value.

### Poor reference file naming
**Look for:** Generic names like `commands.md`, `reference.md`, `guide.md`.
**Why:** Claude and users should understand a file's contents from its name alone.
**Fix:** Use the pattern `<content-type>_<specificity>.md`. Example: `api_endpoints.md`, `database_schema.md`.

## Security

### Hardcoded user paths
**Look for:** Absolute paths containing `/Users/`, `/home/`, `C:\Users\`.
**Why:** These break on other machines and leak personal information in public skills.
**Fix:** Use relative paths, environment variables, or `~/.claude/<skill-name>/` conventions.

### Credentials in code
**Look for:** API keys, tokens, or passwords in script files.
**Why:** Hardcoded secrets are a critical security risk. They get committed to git and shared publicly.
**Fix:** Use environment variables (`os.environ.get("API_KEY")`) or config files (`~/.claude/<skill-name>/.env`). Provide a `.env.example` template.
