#!/usr/bin/env python3
"""Validate a agent skill directory against best-practice conventions.

Checks structure, naming, content quality, path integrity, security patterns,
and completeness. Outputs hard-rule verdicts and soft findings for agent review.

Usage:
    validate.py preflight
    validate.py run --path <skill-dir> [--format concise|detailed|json] [--strict] [--category ...]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def output(data):
    """Write structured JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def error(code, hint, recoverable=True):
    """Write structured error JSON to stderr and exit."""
    print(json.dumps({"error": code, "hint": hint, "recoverable": recoverable},
                     ensure_ascii=False), file=sys.stderr)
    sys.exit(1 if recoverable else 2)


# ---------------------------------------------------------------------------
# Frontmatter parser (no PyYAML dependency)
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Extract YAML frontmatter from markdown text. Returns dict or None."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        colon = line.find(':')
        if colon == -1:
            continue
        key = line[:colon].strip()
        val = line[colon + 1:].strip().strip('"').strip("'")
        fm[key] = val
    return fm


# ---------------------------------------------------------------------------
# Result builders
# ---------------------------------------------------------------------------

def check_result(check_id, category, severity, message, fix=None):
    """Build a hard-rule check result (pass/warn/fail verdict)."""
    r = {"id": check_id, "category": category, "severity": severity, "message": message}
    if fix:
        r["fix"] = fix
    return r


def finding_result(finding_id, category, data, context_hint):
    """Build a soft finding (data only, no verdict — agent judges context)."""
    return {
        "id": finding_id,
        "category": category,
        "type": "finding",
        "data": data,
        "context_hint": context_hint,
    }


# ---------------------------------------------------------------------------
# Hard-rule checks (script produces verdicts)
# ---------------------------------------------------------------------------

def checks_structure(skill_path, content, fm):
    """Structure checks: SKILL.md exists, frontmatter, required fields."""
    results = []
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        results.append(check_result("skill_md_exists", "structure", "fail",
                                    "SKILL.md not found",
                                    "Create a SKILL.md file with YAML frontmatter"))
        return results  # can't continue without SKILL.md
    results.append(check_result("skill_md_exists", "structure", "pass", "SKILL.md found"))

    if fm is None:
        results.append(check_result("frontmatter_exists", "structure", "fail",
                                    "No YAML frontmatter block found",
                                    "Add --- delimited YAML frontmatter at the top of SKILL.md"))
        return results
    results.append(check_result("frontmatter_exists", "structure", "pass", "Frontmatter present"))

    if not fm.get("name"):
        results.append(check_result("frontmatter_name", "structure", "fail",
                                    "Missing 'name' field in frontmatter",
                                    "Add 'name: your-skill-name' to frontmatter"))
    else:
        results.append(check_result("frontmatter_name", "structure", "pass",
                                    f"name: {fm['name']}"))

    if not fm.get("description"):
        results.append(check_result("frontmatter_description", "structure", "fail",
                                    "Missing 'description' field in frontmatter",
                                    "Add a description explaining what the skill does and when to use it"))
    else:
        results.append(check_result("frontmatter_description", "structure", "pass",
                                    "description field present"))

    # Check for unexpected top-level directories
    expected_dirs = {"scripts", "references", "templates", "assets"}
    actual_dirs = {d.name for d in skill_path.iterdir() if d.is_dir() and not d.name.startswith(".")}
    unexpected = actual_dirs - expected_dirs
    if unexpected:
        results.append(check_result("directory_layout", "structure", "warn",
                                    f"Unexpected directories: {', '.join(sorted(unexpected))}",
                                    f"Standard directories are: {', '.join(sorted(expected_dirs))}"))
    else:
        results.append(check_result("directory_layout", "structure", "pass",
                                    "Directory layout follows convention"))
    return results


def checks_naming(skill_path, fm):
    """Naming checks: kebab-case, length, consecutive hyphens, dir match."""
    results = []
    if not fm or not fm.get("name"):
        return results

    name = fm["name"]

    if re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) or re.match(r'^[a-z]$', name):
        results.append(check_result("name_kebab_case", "naming", "pass",
                                    f"Name '{name}' is valid kebab-case"))
    else:
        results.append(check_result("name_kebab_case", "naming", "fail",
                                    f"Name '{name}' is not valid kebab-case",
                                    "Use only lowercase letters, digits, and hyphens. Must start with a letter."))

    if len(name) > 64:
        results.append(check_result("name_length", "naming", "fail",
                                    f"Name is {len(name)} chars (max 64)",
                                    "Shorten the skill name to 64 characters or fewer"))
    else:
        results.append(check_result("name_length", "naming", "pass",
                                    f"Name length: {len(name)}/64"))

    if '--' in name:
        results.append(check_result("name_no_consecutive_hyphens", "naming", "fail",
                                    "Name contains consecutive hyphens",
                                    "Replace '--' with a single '-'"))
    else:
        results.append(check_result("name_no_consecutive_hyphens", "naming", "pass",
                                    "No consecutive hyphens"))

    dir_name = skill_path.name
    if name == dir_name:
        results.append(check_result("name_matches_directory", "naming", "pass",
                                    "Frontmatter name matches directory name"))
    else:
        results.append(check_result("name_matches_directory", "naming", "warn",
                                    f"Frontmatter name '{name}' differs from directory '{dir_name}'",
                                    f"Rename directory to '{name}' or update frontmatter name"))
    return results


def checks_content(content, fm):
    """Content quality checks: quantitative metrics only."""
    results = []
    if not fm:
        return results

    desc = fm.get("description", "")
    if len(desc) >= 50:
        results.append(check_result("description_length", "content", "pass",
                                    f"Description length: {len(desc)} chars"))
    else:
        results.append(check_result("description_length", "content", "warn",
                                    f"Description is only {len(desc)} chars (recommend ≥50)",
                                    "Add more detail about what the skill does and when to use it"))

    body = re.sub(r'^---.*?---\s*', '', content, count=1, flags=re.DOTALL).strip()
    body_lines = len(body.splitlines())
    if body_lines < 10:
        results.append(check_result("body_length", "content", "warn",
                                    f"SKILL.md body is only {body_lines} lines (recommend ≥10)",
                                    "Add workflow steps, examples, or reference pointers"))
    else:
        results.append(check_result("body_length", "content", "pass",
                                    f"SKILL.md body: {body_lines} lines"))

    headings = re.findall(r'^#{1,4}\s+.+', content, re.MULTILINE)
    if len(headings) < 2:
        results.append(check_result("heading_structure", "content", "warn",
                                    f"Only {len(headings)} heading(s) found (recommend ≥2)",
                                    "Add section headings to organize the skill instructions"))
    else:
        results.append(check_result("heading_structure", "content", "pass",
                                    f"{len(headings)} headings found"))

    return results


def strip_code_spans(text):
    """Remove fenced code blocks and inline backtick spans from markdown."""
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    return text


def checks_paths(skill_path, content):
    """Path integrity checks: referenced files exist, scripts executable."""
    results = []

    prose = strip_code_spans(content)
    path_pattern = r'(?:scripts|references|assets)/[\w./-]+'
    referenced = set(re.findall(path_pattern, prose))

    missing = []
    for ref in referenced:
        full = skill_path / ref
        if not full.exists():
            missing.append(ref)

    if missing:
        results.append(check_result("referenced_files_exist", "paths", "fail",
                                    f"Missing referenced files: {', '.join(sorted(missing))}",
                                    "Create the missing files or fix the paths in SKILL.md"))
    elif referenced:
        results.append(check_result("referenced_files_exist", "paths", "pass",
                                    f"All {len(referenced)} referenced paths exist"))
    else:
        results.append(check_result("referenced_files_exist", "paths", "pass",
                                    "No file paths referenced in SKILL.md"))

    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        sh_files = list(scripts_dir.glob("*.sh"))
        non_exec = [f.name for f in sh_files if not os.access(f, os.X_OK)]
        if non_exec:
            results.append(check_result("scripts_executable", "paths", "warn",
                                        f"Shell scripts without execute permission: {', '.join(non_exec)}",
                                        f"Run: chmod +x {' '.join('scripts/' + n for n in non_exec)}"))
        elif sh_files:
            results.append(check_result("scripts_executable", "paths", "pass",
                                        "All shell scripts are executable"))
        else:
            results.append(check_result("scripts_executable", "paths", "pass",
                                        "No shell scripts found"))
    else:
        results.append(check_result("scripts_executable", "paths", "pass",
                                    "No scripts directory"))
    return results


def checks_security_hard(skill_path, content):
    """Hard security checks: secrets only (unambiguous)."""
    results = []

    # Collect all text
    all_text = content
    for subdir in ("scripts", "references"):
        d = skill_path / subdir
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.suffix in ('.py', '.sh', '.md', '.txt', '.json', '.yaml', '.yml', '.env'):
                    try:
                        all_text += "\n" + f.read_text(encoding='utf-8', errors='replace')
                    except Exception:
                        pass

    # Secret patterns — always a hard fail, no context needed
    secret_patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
        (r'ghp_[a-zA-Z0-9]{36,}', "GitHub personal access token"),
        (r'gho_[a-zA-Z0-9]{36,}', "GitHub OAuth token"),
        (r'AKIA[A-Z0-9]{16}', "AWS access key"),
        (r'xox[bpras]-[a-zA-Z0-9-]+', "Slack token"),
    ]
    found_secrets = []
    for pat, label in secret_patterns:
        if re.search(pat, all_text):
            found_secrets.append(label)
    if found_secrets:
        results.append(check_result("no_secrets", "security", "fail",
                                    f"Possible secrets detected: {', '.join(found_secrets)}",
                                    "Remove hardcoded secrets. Use environment variables instead."))
    else:
        results.append(check_result("no_secrets", "security", "pass",
                                    "No secret patterns detected"))

    # Template placeholders — always a hard fail
    template_count = len(re.findall(r'\{\{[A-Z_]+\}\}', content))
    if template_count > 0:
        results.append(check_result("no_template_placeholders", "completeness", "fail",
                                    f"Found {template_count} unresolved template placeholder(s)",
                                    "Replace {{PLACEHOLDER}} markers with actual values"))
    else:
        results.append(check_result("no_template_placeholders", "completeness", "pass",
                                    "No template placeholders"))

    return results


# ---------------------------------------------------------------------------
# Soft findings (script detects, agent judges)
# ---------------------------------------------------------------------------

def collect_findings(skill_path, content):
    """Collect contextual findings that need agent judgment."""
    findings = []

    # --- TODO markers ---
    todo_locations = []
    for fpath in _iter_skill_files(skill_path):
        try:
            lines = fpath.read_text(encoding='utf-8', errors='replace').splitlines()
        except Exception:
            continue
        rel = str(fpath.relative_to(skill_path))
        for i, line in enumerate(lines, 1):
            if re.search(r'\bTODO\b', line):
                todo_locations.append(f"{rel}:{i}")

    if todo_locations:
        findings.append(finding_result(
            "todo_markers", "completeness",
            {"count": len(todo_locations), "locations": todo_locations},
            "TODOs in .tmpl template files are intentional scaffolding — not issues. "
            "TODOs in SKILL.md body or script logic are likely unfinished work."
        ))

    # --- Hardcoded user paths ---
    path_locations = []
    path_patterns = [r'/Users/\w+', r'/home/\w+', r'C:\\Users\\\w+', r'/mnt/c/Users/\w+']
    for fpath in _iter_skill_files(skill_path):
        try:
            lines = fpath.read_text(encoding='utf-8', errors='replace').splitlines()
        except Exception:
            continue
        rel = str(fpath.relative_to(skill_path))
        for i, line in enumerate(lines, 1):
            for pat in path_patterns:
                if re.search(pat, line):
                    path_locations.append(f"{rel}:{i}")
                    break

    if path_locations:
        findings.append(finding_result(
            "hardcoded_paths", "security",
            {"count": len(path_locations), "locations": path_locations},
            "Paths in references/ docs may be illustrative examples — acceptable. "
            "Paths in scripts or SKILL.md prose are likely real issues."
        ))

    # --- PII (email addresses) ---
    all_text = _read_all_text(skill_path, content)
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)
    non_pii = {"noreply@anthropic.com", "noreply@github.com", "example@example.com"}
    real_emails = [e for e in emails if e not in non_pii and "example" not in e.lower()]
    if real_emails:
        findings.append(finding_result(
            "pii_patterns", "security",
            {"emails": list(set(real_emails))[:5]},
            "Emails in .env.example or documentation as placeholders are fine. "
            "Real personal emails in scripts or published content are PII concerns."
        ))

    # --- Credential file safety (.gitignore coverage) ---
    env_files = list(skill_path.rglob(".env")) + list(skill_path.rglob(".env.*"))
    env_example = list(skill_path.rglob(".env.example"))
    real_env = [f for f in env_files if f not in env_example and f.name != ".env.example"]
    if real_env:
        # Check if .gitignore covers .env
        gitignore_covers = False
        for gi_path in [skill_path / ".gitignore",
                        skill_path.parent / ".gitignore",
                        skill_path.parent.parent / ".gitignore"]:
            if gi_path.exists():
                try:
                    gi_content = gi_path.read_text(encoding="utf-8", errors="replace")
                    if any(pat in gi_content for pat in [".env", "*.env"]):
                        gitignore_covers = True
                        break
                except Exception:
                    pass

        if not gitignore_covers:
            findings.append(finding_result(
                "env_without_gitignore", "security",
                {"env_files": [str(f.relative_to(skill_path)) for f in real_env]},
                ".env files found but no .gitignore coverage detected. "
                "If this skill is in a git repo, credentials may be committed. "
                "Check if .gitignore at repo root covers .env files."
            ))

    # --- Script convention patterns (only meaningful for L0+/L1 with scripts) ---
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
        if script_files:
            all_script_content = ""
            for sf in script_files:
                try:
                    all_script_content += sf.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    pass

            json_patterns = ["json.dumps", "json.dump", 'echo \'{"', "| jq", "jq '.", 'jq ".',
                             '{"status":', '"status": "ok"', "json_ok", "json_error"]
            has_json = any(p in all_script_content for p in json_patterns)
            has_preflight = "preflight" in all_script_content
            has_stderr = ("sys.stderr" in all_script_content or ">&2" in all_script_content
                          or "file=sys.stderr" in all_script_content)
            has_exit_codes = bool(re.search(
                r'sys\.exit\(\s*[12]\s*\)|sys\.exit\(.+\belse\b.+\)|exit\s+[12]',
                all_script_content))

            findings.append(finding_result(
                "script_conventions", "scripts",
                {
                    "has_json_output": has_json,
                    "has_preflight": has_preflight,
                    "has_error_handling": has_stderr,
                    "has_exit_codes": has_exit_codes,
                },
                "Only applicable to skills with scripts (L0+/L1). "
                "L0 pure-prompt skills without scripts should skip this entirely."
            ))

    return findings


def _iter_skill_files(skill_path):
    """Yield all reviewable files in a skill directory."""
    for f in skill_path.rglob("*"):
        if f.is_file() and f.suffix in ('.py', '.sh', '.md', '.txt', '.json', '.yaml', '.yml', '.env', '.tmpl'):
            yield f


def _read_all_text(skill_path, content):
    """Read all text content from skill for pattern matching."""
    all_text = content
    for subdir in ("scripts", "references"):
        d = skill_path / subdir
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.suffix in ('.py', '.sh', '.md', '.txt', '.json', '.yaml', '.yml', '.env'):
                    try:
                        all_text += "\n" + f.read_text(encoding='utf-8', errors='replace')
                    except Exception:
                        pass
    return all_text


# ---------------------------------------------------------------------------
# Main validation runner
# ---------------------------------------------------------------------------

ALL_CATEGORIES = ["structure", "naming", "content", "paths", "security", "completeness"]


def compute_grade(checks, strict):
    """Compute letter grade from hard-rule check results only."""
    fails = sum(1 for c in checks if c["severity"] == "fail")
    warns = sum(1 for c in checks if c["severity"] == "warn")
    if strict:
        fails += warns
        warns = 0

    skill_md_check = next((c for c in checks if c["id"] == "skill_md_exists"), None)
    if skill_md_check and skill_md_check["severity"] == "fail":
        return "F"
    fm_check = next((c for c in checks if c["id"] == "frontmatter_exists"), None)
    if fm_check and fm_check["severity"] == "fail":
        return "F"

    if fails == 0 and warns == 0:
        return "A"
    elif fails == 0:
        return "B"
    elif fails <= 2:
        return "C"
    else:
        return "D"


def run_validation(skill_path, fmt, strict, categories):
    """Run all validation checks and output report."""
    skill_path = Path(skill_path).resolve()
    if not skill_path.is_dir():
        error("invalid_path", f"Not a directory: {skill_path}", recoverable=True)

    # Read SKILL.md
    skill_md = skill_path / "SKILL.md"
    content = ""
    fm = None
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8', errors='replace')
        fm = parse_frontmatter(content)

    # Run hard-rule checks
    all_checks = []
    cat_set = set(categories) if categories else set(ALL_CATEGORIES)

    if "structure" in cat_set:
        all_checks.extend(checks_structure(skill_path, content, fm))
    if "naming" in cat_set:
        all_checks.extend(checks_naming(skill_path, fm))
    if "content" in cat_set:
        all_checks.extend(checks_content(content, fm))
    if "paths" in cat_set:
        all_checks.extend(checks_paths(skill_path, content))
    if "security" in cat_set:
        all_checks.extend(checks_security_hard(skill_path, content))

    # Collect soft findings
    findings = collect_findings(skill_path, content)

    total = len(all_checks)
    passes = sum(1 for c in all_checks if c["severity"] == "pass")
    warns = sum(1 for c in all_checks if c["severity"] == "warn")
    fails = sum(1 for c in all_checks if c["severity"] == "fail")
    grade = compute_grade(all_checks, strict)

    # Build output
    report = {
        "status": "ok",
        "path": str(skill_path),
        "score": {"total": total, "pass": passes, "warn": warns, "fail": fails},
        "grade": grade,
    }

    if fmt == "concise":
        report["checks"] = [c for c in all_checks if c["severity"] != "pass"]
    else:
        report["checks"] = all_checks

    # Always include findings (agent needs them for contextual review)
    report["findings"] = findings

    report["hint"] = (f"{passes}/{total} checks passed, {warns} warning(s), {fails} failure(s). "
                      f"Grade: {grade}. {len(findings)} finding(s) for agent review.")
    if strict and warns > 0:
        report["hint"] += " (strict mode: warnings treated as failures)"

    output(report)


def cmd_preflight(_args):
    """Check environment readiness."""
    output({
        "ready": True,
        "dependencies": {
            "python3": {"status": "ok", "version": f"{sys.version_info.major}.{sys.version_info.minor}"}
        },
        "credentials": {},
        "services": {},
    })


def main():
    parser = argparse.ArgumentParser(
        description="Validate a agent skill directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("preflight", help="Check environment readiness")

    run_parser = sub.add_parser("run", help="Run validation checks")
    run_parser.add_argument("--path", required=True, help="Path to skill directory")
    run_parser.add_argument("--format", dest="fmt", choices=["concise", "detailed", "json"],
                            default="concise", help="Output format (default: concise)")
    run_parser.add_argument("--strict", action="store_true",
                            help="Treat warnings as failures")
    run_parser.add_argument("--category", action="append", dest="categories",
                            choices=ALL_CATEGORIES,
                            help="Run only specific category (repeatable)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(2)

    if args.command == "preflight":
        cmd_preflight(args)
    elif args.command == "run":
        run_validation(args.path, args.fmt, args.strict, args.categories)


if __name__ == "__main__":
    main()
