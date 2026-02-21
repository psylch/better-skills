#!/usr/bin/env python3
"""Package an agent skill into a distributable GitHub repository.

Generates README, LICENSE, plugin.json, marketplace.json, .gitignore,
and copies the skill directory into the proper structure.

Usage:
    publish.py preflight
    publish.py generate --skill-path <path> --owner <owner> --repo <name> --version <ver> [--license mit|apache2|gpl3] [--output <dir>] [--force]
"""

import argparse
import datetime
import json
import os
import re
import shutil
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
# Frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Extract YAML frontmatter from markdown text."""
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


def name_to_title(name):
    """Convert kebab-case to Title Case."""
    return ' '.join(word.capitalize() for word in name.split('-'))


def render(template, replacements):
    """Replace {{PLACEHOLDER}} tokens in template string."""
    result = template
    for key, value in replacements.items():
        result = result.replace(f'{{{{{key}}}}}', value)
    return result


def detect_level(skill_path):
    """Detect skill level: l0, l0plus, or l1."""
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return "l0"
    py_files = list(scripts_dir.glob("*.py"))
    if py_files:
        return "l1"
    sh_files = list(scripts_dir.glob("*.sh"))
    if sh_files:
        return "l0plus"
    return "l0"


def extract_prerequisites(level):
    """Generate prerequisites text based on skill level."""
    if level == "l0":
        return "- Any AI coding agent that supports [skills.sh](https://skills.sh/) (Claude Code, Cursor, Windsurf, etc.)"
    elif level == "l0plus":
        return ("- Any AI coding agent that supports [skills.sh](https://skills.sh/) (Claude Code, Cursor, Windsurf, etc.)\n"
                "- **Bash** (for helper scripts)")
    else:
        return ("- Any AI coding agent that supports [skills.sh](https://skills.sh/) (Claude Code, Cursor, Windsurf, etc.)\n"
                "- **Python 3.11+** (for skill scripts)")


# ---------------------------------------------------------------------------
# Generate command
# ---------------------------------------------------------------------------

def cmd_generate(args):
    """Generate repository files from a skill directory."""
    skill_path = Path(args.skill_path).resolve()
    if not skill_path.is_dir():
        error("invalid_path", f"Not a directory: {skill_path}", recoverable=True)

    skill_md_path = skill_path / "SKILL.md"
    if not skill_md_path.exists():
        error("no_skill_md", f"SKILL.md not found in {skill_path}", recoverable=True)

    content = skill_md_path.read_text(encoding='utf-8')
    fm = parse_frontmatter(content)
    if not fm or not fm.get("name"):
        error("bad_frontmatter", "SKILL.md must have frontmatter with a 'name' field", recoverable=True)

    skill_name = fm["name"]
    skill_desc = fm.get("description", f"{name_to_title(skill_name)} skill")
    level = detect_level(skill_path)

    output_dir = Path(args.output).resolve() if args.output else skill_path.parent.parent
    repo_dir = output_dir / args.repo

    if repo_dir.exists() and not args.force:
        error("already_exists",
              f"Directory '{repo_dir}' already exists. Use --force to overwrite.",
              recoverable=True)

    # Load templates
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / "templates"
    if not templates_dir.exists():
        error("templates_missing", f"Templates directory not found at {templates_dir}", recoverable=False)

    replacements = {
        "SKILL_NAME": skill_name,
        "SKILL_NAME_TITLE": name_to_title(skill_name),
        "SKILL_DESCRIPTION": skill_desc,
        "OWNER": args.owner,
        "REPO": args.repo,
        "VERSION": args.version,
        "YEAR": str(datetime.date.today().year),
        "LICENSE_TYPE": {"mit": "MIT", "apache2": "Apache-2.0", "gpl3": "GPL-3.0"}[args.license],
        "INSTALL_COMMAND": f"npx skills add {args.owner}/{args.repo} -g -y",
        "PREREQUISITES": extract_prerequisites(level),
        "SKILL_LEVEL": level.upper(),
    }

    created = []

    # Create repo directory
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Copy skill directory
    dest_skill_dir = repo_dir / "skills" / skill_name
    if dest_skill_dir.exists():
        shutil.rmtree(dest_skill_dir)
    shutil.copytree(skill_path, dest_skill_dir)
    created.append(f"skills/{skill_name}/")

    # Generate files from templates
    template_files = {
        "README.md.tmpl": "README.md",
        "README.zh.md.tmpl": "README.zh.md",
        "plugin.json.tmpl": ".claude-plugin/plugin.json",
        "marketplace.json.tmpl": ".claude-plugin/marketplace.json",
        f"LICENSE_{args.license}.tmpl": "LICENSE",
        "gitignore.tmpl": ".gitignore",
    }

    for tmpl_name, dest_name in template_files.items():
        tmpl_path = templates_dir / tmpl_name
        if not tmpl_path.exists():
            error("template_missing", f"Template not found: {tmpl_path}", recoverable=False)
        tmpl_content = tmpl_path.read_text(encoding='utf-8')
        rendered = render(tmpl_content, replacements)

        dest_path = repo_dir / dest_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(rendered, encoding='utf-8')
        created.append(dest_name)

    output({
        "status": "ok",
        "output_dir": str(repo_dir),
        "repo": f"{args.owner}/{args.repo}",
        "created": created,
        "hint": (f"Repository files generated at {repo_dir}.\n"
                 f"Next steps:\n"
                 f"  1. Review and polish README.md / README.zh.md\n"
                 f"  2. Run: cd {repo_dir} && git init && git add . && git commit -m 'Initial commit'\n"
                 f"  3. Optional: gh repo create {args.owner}/{args.repo} --public --source . --push"),
    })


def cmd_preflight(_args):
    """Check environment readiness."""
    deps = {
        "python3": {"status": "ok", "version": f"{sys.version_info.major}.{sys.version_info.minor}"},
    }

    # Check git
    if shutil.which("git"):
        deps["git"] = {"status": "ok"}
    else:
        deps["git"] = {"status": "missing", "hint": "Install git for repository initialization"}

    # Check gh (optional)
    if shutil.which("gh"):
        deps["gh"] = {"status": "ok", "hint": "Available for GitHub repo creation"}
    else:
        deps["gh"] = {"status": "missing", "hint": "Optional: install gh CLI for GitHub repo creation (brew install gh)"}

    output({
        "ready": True,
        "dependencies": deps,
        "credentials": {},
        "services": {},
    })


def main():
    parser = argparse.ArgumentParser(
        description="Package a skill into a distributable GitHub repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("preflight", help="Check environment readiness")

    gen = sub.add_parser("generate", help="Generate repository files")
    gen.add_argument("--skill-path", required=True, help="Path to skill directory")
    gen.add_argument("--owner", required=True, help="GitHub owner/org name")
    gen.add_argument("--repo", required=True, help="Repository name")
    gen.add_argument("--version", default="1.0.0", help="Skill version (default: 1.0.0)")
    gen.add_argument("--license", choices=["mit", "apache2", "gpl3"], default="mit",
                     help="License type (default: mit)")
    gen.add_argument("--output", help="Output parent directory (default: skill's grandparent)")
    gen.add_argument("--force", action="store_true", help="Overwrite existing repo directory")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(2)

    if args.command == "preflight":
        cmd_preflight(args)
    elif args.command == "generate":
        cmd_generate(args)


if __name__ == "__main__":
    main()
