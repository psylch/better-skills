#!/usr/bin/env python3
"""Validate a Claude Code skill directory against best-practice conventions.

Checks structure, naming, content quality, path integrity, script conventions,
security patterns, and completeness. Outputs a graded JSON report.

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
# Individual checks
# ---------------------------------------------------------------------------

def check_result(check_id, category, severity, message, fix=None):
    r = {"id": check_id, "category": category, "severity": severity, "message": message}
    if fix:
        r["fix"] = fix
    return r


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
    actual_dirs = {d.name for d in skill_path.iterdir() if d.is_dir()}
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
                                    f"Frontmatter name matches directory name"))
    else:
        results.append(check_result("name_matches_directory", "naming", "warn",
                                    f"Frontmatter name '{name}' differs from directory '{dir_name}'",
                                    f"Rename directory to '{name}' or update frontmatter name"))
    return results


def checks_content(content, fm):
    """Content quality checks: description length, trigger phrases, sections."""
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
                                    "Add more detail about when to use this skill and trigger phrases"))

    # Check for trigger-phrase-like patterns (quoted phrases, 'when ... says')
    trigger_patterns = [r"when the user says", r"when.*says\s+'", r"trigger", r"use when",
                        r"should be used when"]
    has_trigger = any(re.search(p, desc, re.IGNORECASE) for p in trigger_patterns)
    if has_trigger:
        results.append(check_result("description_trigger_phrases", "content", "pass",
                                    "Description contains trigger phrase guidance"))
    else:
        results.append(check_result("description_trigger_phrases", "content", "warn",
                                    "Description may lack trigger phrases",
                                    "Add phrases like \"Use when...\" or \"when the user says '...'\" to help Claude know when to activate"))

    # Third-person check (no "I " or "you " at word boundaries in description)
    if re.search(r'\bI\b(?!\.)', desc) or re.search(r'\byou\b', desc, re.IGNORECASE):
        results.append(check_result("description_third_person", "content", "warn",
                                    "Description uses first/second person ('I' or 'you')",
                                    "Use third-person voice: 'This skill...' instead of 'You can...'"))
    else:
        results.append(check_result("description_third_person", "content", "pass",
                                    "Description uses appropriate voice"))

    # Check for workflow section
    workflow_patterns = [r'^##\s+(Workflow|How It Works|Process|Dialogue Flow|Steps)',]
    has_workflow = any(re.search(p, content, re.MULTILINE | re.IGNORECASE)
                       for p in workflow_patterns)
    if has_workflow:
        results.append(check_result("workflow_section", "content", "pass",
                                    "Workflow/process section found"))
    else:
        results.append(check_result("workflow_section", "content", "warn",
                                    "No Workflow or 'How It Works' section found",
                                    "Add a section describing the step-by-step process"))
    return results


def strip_code_spans(text):
    """Remove fenced code blocks and inline backtick spans from markdown."""
    # Remove fenced code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    # Remove inline code spans (backtick-wrapped)
    text = re.sub(r'`[^`]+`', '', text)
    return text


def checks_paths(skill_path, content):
    """Path integrity checks: referenced files exist, scripts executable."""
    results = []

    # Extract file paths referenced in SKILL.md prose (not code blocks or inline code).
    # Inline code and code blocks often describe paths in *generated* skills, not
    # files that must exist in the current skill directory.
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

    # Check .sh files have execute permission
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


def checks_scripts(skill_path):
    """Script convention checks: JSON output, preflight, error handling, exit codes."""
    results = []
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return results

    script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
    if not script_files:
        return results

    all_content = ""
    for sf in script_files:
        try:
            all_content += sf.read_text(encoding='utf-8', errors='replace')
        except Exception:
            pass

    # JSON output pattern
    if "json.dumps" in all_content or "json.dump" in all_content or 'echo \'{"' in all_content:
        results.append(check_result("script_json_output", "scripts", "pass",
                                    "Scripts use JSON output pattern"))
    else:
        results.append(check_result("script_json_output", "scripts", "warn",
                                    "No JSON output pattern detected in scripts",
                                    "Use json.dumps() for Python or echo '{...}' for bash to output structured JSON"))

    # Preflight subcommand
    if "preflight" in all_content:
        results.append(check_result("script_preflight", "scripts", "pass",
                                    "Scripts implement preflight subcommand"))
    else:
        results.append(check_result("script_preflight", "scripts", "warn",
                                    "No preflight subcommand found",
                                    "Add a 'preflight' subcommand that checks environment readiness"))

    # Error handling (stderr)
    if "sys.stderr" in all_content or ">&2" in all_content or "file=sys.stderr" in all_content:
        results.append(check_result("script_error_handling", "scripts", "pass",
                                    "Scripts write errors to stderr"))
    else:
        results.append(check_result("script_error_handling", "scripts", "warn",
                                    "No stderr error output pattern detected",
                                    "Write error JSON to stderr: print(..., file=sys.stderr) or echo ... >&2"))

    # Exit codes
    if re.search(r'sys\.exit\(\s*[12]\s*\)|sys\.exit\(.+\belse\b.+\)|exit\s+[12]', all_content):
        results.append(check_result("script_exit_codes", "scripts", "pass",
                                    "Scripts use proper exit codes (1=recoverable, 2=fatal)"))
    else:
        results.append(check_result("script_exit_codes", "scripts", "warn",
                                    "No exit code convention detected (exit 1/2)",
                                    "Use exit 0 for success, exit 1 for recoverable errors, exit 2 for fatal errors"))
    return results


def checks_security(skill_path, content):
    """Security checks: hardcoded paths, secrets, PII."""
    results = []

    # Collect all text from SKILL.md + scripts + references
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

    # Hardcoded user paths
    path_patterns = [r'/Users/\w+', r'/home/\w+', r'C:\\Users\\\w+', r'/mnt/c/Users/\w+']
    found_paths = []
    for pat in path_patterns:
        found_paths.extend(re.findall(pat, all_text))
    if found_paths:
        unique = list(set(found_paths))[:3]
        results.append(check_result("no_hardcoded_paths", "security", "warn",
                                    f"Hardcoded user paths found: {', '.join(unique)}",
                                    "Replace with relative paths or environment variables"))
    else:
        results.append(check_result("no_hardcoded_paths", "security", "pass",
                                    "No hardcoded user paths detected"))

    # Secret patterns
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

    # PII (email patterns)
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)
    # Filter out common non-PII emails
    non_pii = {"noreply@anthropic.com", "noreply@github.com", "example@example.com"}
    real_emails = [e for e in emails if e not in non_pii and "example" not in e.lower()]
    if real_emails:
        results.append(check_result("no_pii", "security", "warn",
                                    f"Possible PII (email addresses): {', '.join(set(real_emails)[:3])}",
                                    "Remove personal email addresses for public distribution"))
    else:
        results.append(check_result("no_pii", "security", "pass",
                                    "No PII patterns detected"))
    return results


def checks_completeness(content):
    """Completeness checks: TODO placeholders, template markers."""
    results = []

    todo_count = len(re.findall(r'\bTODO\b', content))
    if todo_count > 0:
        results.append(check_result("no_todo_placeholders", "completeness", "warn",
                                    f"Found {todo_count} TODO placeholder(s)",
                                    "Replace TODO markers with actual content"))
    else:
        results.append(check_result("no_todo_placeholders", "completeness", "pass",
                                    "No TODO placeholders"))

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
# Main validation runner
# ---------------------------------------------------------------------------

ALL_CATEGORIES = ["structure", "naming", "content", "paths", "scripts", "security", "completeness"]


def compute_grade(checks, strict):
    """Compute letter grade from check results."""
    fails = sum(1 for c in checks if c["severity"] == "fail")
    warns = sum(1 for c in checks if c["severity"] == "warn")
    if strict:
        fails += warns
        warns = 0

    # Check if SKILL.md is missing (F grade)
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

    # Run checks by category
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
    if "scripts" in cat_set:
        all_checks.extend(checks_scripts(skill_path))
    if "security" in cat_set:
        all_checks.extend(checks_security(skill_path, content))
    if "completeness" in cat_set:
        all_checks.extend(checks_completeness(content))

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
        # Only include non-pass checks
        report["checks"] = [c for c in all_checks if c["severity"] != "pass"]
    else:
        report["checks"] = all_checks

    report["hint"] = (f"{passes}/{total} checks passed, {warns} warning(s), {fails} failure(s). "
                      f"Grade: {grade}.")
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
        description="Validate a Claude Code skill directory",
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
