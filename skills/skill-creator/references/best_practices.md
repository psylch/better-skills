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

- **API tokens** → Environment variables (`$SKILL_NAME_API_KEY`), don't persist to files
- **Persistent credentials** → `~/.claude/<skill-name>/.env`, provide `.env.example` template
- **Browser login state** → Status cache JSON with optimistic assumption + passive expiry
- **Never ask for passwords in chat** — direct users to edit config files

## Degradation Patterns

| Pattern | When to use | Example |
|---------|-------------|---------|
| **Skip & report** | Optional data source unavailable | Grok offline → research with WebSearch only |
| **Auto-fallback** | Alternative backend available | Z-Library down → try Anna's Archive |
| **Disable service** | User explicitly opts out | No TIDAL membership → disable TIDAL source |
| **Halt & guide** | Hard dependency, no alternative | Quark APP not running → tell user to launch it |

## Token Awareness

- Support `--limit N` for paginated results
- Support `--format concise|detailed|json` for output verbosity
- Default to concise — Claude can request detailed when needed
- Never dump unbounded data to stdout
