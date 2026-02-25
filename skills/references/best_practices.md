# Skill Runtime Best Practices — Quick Reference

Condensed from practical experience building 7+ production skills. For the full narrative, see the blog post.

## Skill Levels

**L0 (Pure Prompt)** — SKILL.md only. Claude uses built-in tools and MCP servers. No scripts, no environment concerns. Example: terminal configuration wizard, research orchestration.

**L0+ (Prompt + Helper)** — SKILL.md + lightweight scripts for environment detection or status caching. Core logic stays in the prompt. Example: tech-research with a browser backend detection script.

**L1 (Prompt + Business Scripts)** — Scripts handle core business logic. SKILL.md orchestrates calls. Scripts are essentially CLI tools designed for AI consumption — same principles as MCP tools apply.

## Script Output Convention

All script output follows this contract:

**Success → stdout as JSON:**
```json
{"status": "ok", "results": [...], "hint": "Human-readable summary"}
```

**Error → stderr as JSON:**
```json
{"error": "error_code", "hint": "What went wrong and what to do next", "recoverable": true}
```

**Exit codes:** 0 = success, 1 = recoverable error (Claude can try to fix), 2 = fatal error (user must intervene).

Include a `hint` field in every response — it's a natural-language summary that helps Claude communicate with the user efficiently.

## Preflight Standard

Every L0+ and L1 skill should have a `preflight` command that returns:

```json
{
  "ready": true,
  "dependencies": {
    "<name>": {"status": "ok|missing", "version": "...", "hint": "Install instructions"}
  },
  "credentials": {
    "<name>": {"status": "configured|not_configured", "hint": "...", "required": true}
  },
  "services": {
    "<name>": {"status": "running|not_running", "hint": "..."}
  }
}
```

`ready: true` means proceed. `ready: false` means follow hints before running business commands.

**Fix guidance table:** When preflight has multiple checks, provide a Check → Fix mapping table in SKILL.md so Claude (and users) know exactly how to resolve each failure:

```
| Check | Fix |
|-------|-----|
| Chrome not found | Install Chrome or set `CHROME_PATH` env var |
| API credentials | Follow guided setup in Step N |
| Missing tool X | `brew install x` / `apt install x` |
```

This avoids generic "preflight failed" messages and gives actionable remediation per item.

**Validate credentials by testing actual capability, not meta-endpoints.** Many APIs have multiple token types (user-level, account-level, service tokens) with different verification endpoints. Instead of calling a token-verify endpoint (which may not support all token types), test an actual API call the skill needs — e.g., list resources with `per_page=1`. This avoids false negatives from token-type mismatches.

## Environment Strategy Decision

```
Need external Python libraries?
├─ No → stdlib-only (zero cost, always prefer this)
└─ Yes
   ├─ Pure Python, 1-2 packages → consider vendoring into skill directory
   └─ More packages or C extensions?
      ├─ No long-running processes → uv run + PEP 723 inline deps
      └─ Long-running processes or complex deps → per-skill venv + run.sh
```

**uv run** is the sweet spot for most L1 skills with dependencies: no persistent venv, global dependency cache, automatic version isolation. The only prerequisite is `uv` itself (`brew install uv`).

## Unified Subcommands

Use consistent command names across all skills:

| Command | Purpose | When |
|---------|---------|------|
| `preflight` | Check environment readiness | Before any business logic |
| `setup` | First-time installation | When preflight reports missing items |
| `status` | Show current state | Anytime (configured services, login status) |
| Business commands | Skill-specific operations | After preflight passes |

## Credential Management

**Storage locations** (priority order):
1. Environment variables (`$SKILL_NAME_API_KEY`) — highest priority, per-session
2. Project-level: `<cwd>/.env` or `<cwd>/.baoyu-skills/<skill-name>/.env`
3. User-level: `~/.claude/<skill-name>/.env` or `~/.baoyu-skills/<skill-name>/.env`

**First-time setup flow:** When credentials are missing, don't just fail — guide the user:

```
[Credential] not found.

How to obtain:
1. Visit <service dashboard URL>
2. Create token with <required permissions>
3. Copy the token

Where to save?
A) Project-level: .env in current directory (this project only)
B) User-level: ~/.claude/<skill-name>/.env (all projects)
```

After the user chooses, write the `.env` file to the selected location. On subsequent runs, load it silently.

**Rules:**
- **Never ask for passwords/tokens in chat** — direct users to paste into a file or use the guided setup to write `.env`
- **Browser login state** → Status cache JSON with optimistic assumption + passive expiry
- **Provide `.env.example`** template so users know the expected format

## Degradation Patterns

| Pattern | When to use | Example |
|---------|-------------|---------|
| **Skip & report** | Optional data source unavailable | Grok offline → research with WebSearch only |
| **Auto-fallback** | Alternative backend available | Z-Library down → try Anna's Archive |
| **Disable service** | User explicitly opts out | No TIDAL membership → disable TIDAL source |
| **Halt & guide** | Hard dependency, no alternative | Quark APP not running → tell user to launch it |

## Setup Flow Integrity

The setup/onboarding flow is the most fragile part of any skill. A first-time user who hits a dead end during setup will never use the skill again. This section covers patterns that go beyond "does preflight exist" to "does the setup actually work end-to-end."

### Bootstrap Safety

Preflight must NOT depend on the tools it checks. This is the #1 setup UX bug.

**Anti-pattern (circular dependency):**
```bash
cmd_preflight() {
  # Uses jq to format output — but jq is one of the deps we're checking!
  jq -n --argjson ready "$ready" --argjson jq_dep "$jq_status" '...'
}
```

**Fix:** Use printf/echo for preflight output when a checked dependency is also used for formatting:
```bash
cmd_preflight() {
  if ! command -v jq &>/dev/null; then
    printf '{"ready":false,"dependencies":{"jq":{"status":"missing","hint":"brew install jq"}}}\n'
    return
  fi
  jq -n '...'  # Safe — jq is confirmed available
}
```

### Live Validation vs Existence Checks

Checking that a credential **exists** is not the same as checking that it **works**.

| Level | What it checks | Catches |
|-------|---------------|---------|
| Existence | Env var is non-empty | Missing config |
| Format | Value matches expected pattern | Typos, wrong field |
| **Live validation** | Actual API call succeeds | Expired tokens, wrong permissions, revoked keys |

Preflight should do **at minimum** existence checks. For credentials that are easy to validate (API keys with a lightweight endpoint), do live validation. For credentials that are expensive to validate (OAuth tokens requiring refresh), existence + format is acceptable.

**Example — testing actual capability:**
```bash
# BAD: only checks if variable exists
[[ -n "$CF_API_TOKEN" ]] && token_status="configured"

# GOOD: tests actual API access
if curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
   "https://api.cloudflare.com/client/v4/zones?per_page=1" | jq -e '.success' &>/dev/null; then
  token_status="valid"
fi
```

### Credential Security Checklist

| Check | Why | How to verify |
|-------|-----|--------------|
| `.gitignore` covers `.env` | Prevents credential leaks in git | Check repo root AND skill directory for `.gitignore` |
| No passwords in CLI args | `ps` and shell history expose them | Grep for `--password`, `--token` in argparse definitions |
| No secrets in committed files | Even in "local" dirs | Check git status for tracked `.env` files |
| `.env.example` has placeholders only | Template shouldn't have real values | Check `.env.example` for real-looking tokens |

### Setup Separation Patterns

**Good:** Setup is a distinct phase, triggered only when preflight fails.
```
User triggers skill → Preflight → ready: true → Business workflow
                                → ready: false → Setup flow → Re-preflight → Business workflow
```

**Bad:** Setup mixed into business workflow.
```
User triggers skill → Start research → Mid-way discover Grok needs setup
                   → Mutate ~/.claude.json → Ask user to restart → Continue with degraded mode
```

### Error Recovery: Token Expiration

Scripts that cache tokens must handle expiration gracefully:

```python
# BAD: cached token exists → use it → fail → die
if cached_token:
    client = Client(token=cached_token)
    if not client.is_valid():
        die("Login failed")  # Never tries fresh login!

# GOOD: cached token → try → fail → fallback to fresh login → update cache
if cached_token:
    client = Client(token=cached_token)
    if client.is_valid():
        return client
# Fall through to fresh login
if email and password:
    client = Client.login(email, password)
    cache_token(client.token)
    return client
die("No valid credentials")
```

### Single Canonical Configuration Path

Error messages and SKILL.md must agree on HOW to configure credentials. Having both `.env` editing and `config set` CLI commands creates confusion when they store to different locations or have different precedence.

**Pick one canonical path and make everything point to it.** If `.env` is the primary method, error hints should say "Edit ~/.claude/skill-name/.env" — not "Run: script config set --key VALUE".

### Config Safety (for Setup/Installation Skills)

L0 skills that write config files (terminal setups, editor configs) must:

1. **Check for existing files** before writing
2. **Show the user** what exists and what will change
3. **Offer choices**: backup & replace, merge, or skip
4. **Provide rollback guidance** if the new config breaks things

```markdown
Before writing, check if the config file already exists.
If it exists:
  a) Back up to <file>.backup.<timestamp>
  b) Show the user the diff between existing and proposed config
  c) Ask: (A) Replace with backup, (B) Skip this step, (C) Merge manually
If the new config breaks the shell/terminal:
  → Document how to restore: cp <file>.backup.<timestamp> <file>
  → Document how to open a fallback shell/terminal
```

## Token Awareness

- Support `--limit N` for paginated results
- Support `--format concise|detailed|json` for output verbosity
- Default to concise — Claude can request detailed when needed
- Never dump unbounded data to stdout

## UX Practices

Not every practice applies to every skill. Each has an **applicability condition** — only suggest it when the condition is met.

### Applicability Matrix

| Practice | Applies when | Does NOT apply when |
|----------|-------------|---------------------|
| Language Matching | Skill targets multilingual users, or is published publicly | Personal/internal skill with single-language audience |
| Progress Checklist | Workflow has 4+ sequential steps | Simple 1-3 step workflow, or non-linear workflow |
| Completion Report | Skill produces artifacts (files, API results, side effects) | Skill is purely informational (config wizard, research) |
| Input Adaptation | Skill accepts file/content input from user | Skill is dialogue-driven with no file input |
| Cross-skill Dependencies | SKILL.md references another skill by name | Skill is self-contained |
| User Preferences | Skill has recurring per-user config (theme, author, output dir) that stays the same across sessions | Each invocation genuinely needs fresh parameters |

When reviewing a skill, **check the applicability condition first**. A `false` profile flag with no applicable condition is not a problem — it's the expected state.

### Language Matching

**Applies when:** Skill is published publicly or targets multilingual users.

Add to the top of SKILL.md:

```
## Language
**Match user's language**: Respond in the same language the user uses.
```

### Progress Checklist

**Applies when:** Workflow has 4+ sequential steps.

Provide a copyable checklist at the start of the workflow:

```
Progress:
- [ ] Step 1: Validate input
- [ ] Step 2: Convert format
- [ ] Step 3: Check metadata
- [ ] Step 4: Publish
- [ ] Step 5: Report completion
```

Benefits: visible progress, resumability if interrupted, clear scope of what the skill does.

### Completion Report

**Applies when:** Skill produces artifacts (files, downloads, API mutations, published drafts).

Present a structured completion report after the operation:

```
[Skill Name] Complete!

Input: [type] - [path or description]
Method: [which method/backend was used]

Result:
✓ [What was accomplished]
• [Key detail 1]
• [Key detail 2]

Files created:
• [path/to/output1]
• [path/to/output2]

Next Steps:
→ [Actionable suggestion with link if applicable]
```

### Input Adaptation

**Applies when:** Skill accepts file or content input from the user.

Accept imperfect input and adapt rather than reject:

| Input State | Approach |
|-------------|----------|
| Wrong format but convertible | Auto-convert (e.g., plain text → markdown → HTML) |
| Missing optional metadata | Auto-generate with sensible defaults, inform user |
| Ambiguous input type | Detect automatically (file extension, content sniffing) |
| Partially complete | Fill in gaps, ask only for truly required fields |

### Cross-skill Dependencies

**Applies when:** SKILL.md references or invokes another skill.

1. **Check availability** at the start of the workflow
2. **If missing**, provide:
   - Installation command or link
   - An alternative path that doesn't require the dependency
   - Let the user choose (install vs. workaround vs. cancel)

```
[dependency-skill] not found.

Options:
A) Install it: npx skills add owner/repo -g -y
B) Continue without it (provide [alternative input] manually)
C) Cancel
```

### User Preferences

**Applies when:** Skill has recurring per-user configuration (theme, author, default output directory) that stays the same across sessions.

Support a layered configuration system:

**Priority chain** (highest to lowest):
1. CLI arguments (per invocation)
2. Frontmatter / inline metadata (per file)
3. User config file (persistent preferences)
4. Skill defaults (hardcoded fallback)

**First-time setup:** When config is not found, trigger a guided setup flow. Save the user's choices so they don't repeat configuration every session.

**Separate credentials from preferences:** Use `.env` for secrets (API tokens, keys) and a separate config file (e.g., `EXTEND.md`, `config.yml`) for non-secret user preferences (theme, author, default flags). This separation allows:
- Preferences can be checked into version control safely
- `.env` stays in `.gitignore`
- Different discovery paths: `.env` is loaded by scripts silently; config files are read by SKILL.md logic

**Config file discovery** (check in order, use first found):
```bash
# Project-level (this project only)
test -f <cwd>/.baoyu-skills/<skill-name>/EXTEND.md && echo "project"

# User-level (all projects)
test -f "$HOME/.baoyu-skills/<skill-name>/EXTEND.md" && echo "user"
```

If neither exists → trigger first-time setup → ask user which level to save to → write file.

## User Experience Tips

- **Long-running operations → background mode.** Download dashboards, web UIs, and server processes should be explicitly marked in SKILL.md for background execution (`run_in_background: true`). Otherwise Claude blocks the conversation.
- **Report results after operations.** After downloads, file generation, or any operation that produces artifacts, instruct Claude to tell the user: file path, file size, and any remaining quotas or limits. Use the Completion Report template above.
- **Never ask for credentials in chat.** Direct users to edit config files. Chat history may be persisted.
- **First run should be fast.** Prefer stdlib-only or uv over pip + venv. Users judge a skill by first impression.
