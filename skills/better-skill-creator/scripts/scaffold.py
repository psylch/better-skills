#!/usr/bin/env python3
"""Scaffold generator for agent skills.

Non-interactive script that generates skill project files from templates.
All user interaction happens through Claude's dialogue — this script only
accepts CLI arguments and outputs JSON.

Usage:
    scaffold.py preflight
    scaffold.py scaffold --name <name> --level l0|l0plus|l1 [--env stdlib|uv|venv] [--output <dir>] [--force]
"""

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path


def output(data):
    """Write structured JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def error(code, hint, recoverable=True):
    """Write structured error JSON to stderr and exit."""
    print(json.dumps({"error": code, "hint": hint, "recoverable": recoverable}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1 if recoverable else 2)


def validate_name(name):
    """Validate skill name: lowercase letters, digits, hyphens, max 64 chars."""
    if not name:
        error("invalid_name", "Skill name cannot be empty", recoverable=False)
    if len(name) > 64:
        error("invalid_name", f"Skill name must be ≤64 characters, got {len(name)}", recoverable=False)
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and not re.match(r'^[a-z]$', name):
        error("invalid_name",
              "Skill name must start with a letter, end with a letter/digit, "
              "and contain only lowercase letters, digits, and hyphens",
              recoverable=False)
    if '--' in name:
        error("invalid_name", "Skill name cannot contain consecutive hyphens", recoverable=False)


def name_to_title(name):
    """Convert kebab-case to Title Case: 'my-skill' -> 'My Skill'."""
    return ' '.join(word.capitalize() for word in name.split('-'))


def load_template(templates_dir, level, filename):
    """Load a template file from the templates directory."""
    path = templates_dir / level / filename
    if not path.exists():
        error("template_missing", f"Template file not found: {path}", recoverable=False)
    return path.read_text(encoding='utf-8')


def render(template, replacements):
    """Replace {{PLACEHOLDER}} tokens in template string."""
    result = template
    for key, value in replacements.items():
        result = result.replace(f'{{{{{key}}}}}', value)
    return result


def make_executable(path):
    """Add execute permission to a file."""
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def scaffold(name, level, env, output_dir, force, templates_dir):
    """Generate skill files from templates."""
    skill_dir = Path(output_dir) / 'skills' / name
    scripts_dir = skill_dir / 'scripts'
    references_dir = skill_dir / 'references'

    # Check if target already exists
    if skill_dir.exists() and not force:
        error("already_exists",
              f"Directory '{skill_dir}' already exists. Use --force to overwrite.",
              recoverable=True)

    replacements = {
        'SKILL_NAME': name,
        'SKILL_NAME_TITLE': name_to_title(name),
    }

    created = []

    # Always create SKILL.md
    tmpl = load_template(templates_dir, level, 'SKILL.md.tmpl')
    skill_md_path = skill_dir / 'SKILL.md'
    skill_md_path.parent.mkdir(parents=True, exist_ok=True)
    skill_md_path.write_text(render(tmpl, replacements), encoding='utf-8')
    created.append(str(skill_md_path.relative_to(output_dir)))

    # Always create references/.gitkeep
    references_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = references_dir / '.gitkeep'
    gitkeep.touch()
    created.append(str(gitkeep.relative_to(output_dir)))

    # L0+ and L1: create assets/.gitkeep (non-context files: templates, images, fonts)
    if level in ('l0plus', 'l1'):
        assets_dir = skill_dir / 'assets'
        assets_dir.mkdir(parents=True, exist_ok=True)
        assets_gitkeep = assets_dir / '.gitkeep'
        assets_gitkeep.touch()
        created.append(str(assets_gitkeep.relative_to(output_dir)))

    # L0+ and L1: create scripts
    if level == 'l0plus':
        scripts_dir.mkdir(parents=True, exist_ok=True)
        tmpl = load_template(templates_dir, 'l0plus', 'helper.sh.tmpl')
        helper_path = scripts_dir / 'helper.sh'
        helper_path.write_text(render(tmpl, replacements), encoding='utf-8')
        make_executable(helper_path)
        created.append(str(helper_path.relative_to(output_dir)))

    elif level == 'l1':
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Select main.py template based on env strategy
        env_template_map = {
            'stdlib': 'main_stdlib.py.tmpl',
            'uv': 'main_uv.py.tmpl',
            'venv': 'main_venv.py.tmpl',
        }
        tmpl_file = env_template_map.get(env, 'main_stdlib.py.tmpl')
        tmpl = load_template(templates_dir, 'l1', tmpl_file)
        main_path = scripts_dir / 'main.py'
        main_path.write_text(render(tmpl, replacements), encoding='utf-8')
        make_executable(main_path)
        created.append(str(main_path.relative_to(output_dir)))

        # venv: also generate run.sh and .env.example
        if env == 'venv':
            tmpl = load_template(templates_dir, 'l1', 'run.sh.tmpl')
            run_path = scripts_dir / 'run.sh'
            run_path.write_text(render(tmpl, replacements), encoding='utf-8')
            make_executable(run_path)
            created.append(str(run_path.relative_to(output_dir)))

            tmpl = load_template(templates_dir, 'l1', 'env.example.tmpl')
            env_path = skill_dir / '.env.example'
            env_path.write_text(render(tmpl, replacements), encoding='utf-8')
            created.append(str(env_path.relative_to(output_dir)))

    # Build hint message
    hints = [f"Skill '{name}' created at {skill_dir}"]
    hints.append("Next steps:")
    hints.append("  1. Edit SKILL.md — replace TODO placeholders with your skill's content")
    if level in ('l0plus', 'l1'):
        hints.append("  2. Customize scripts/ for your use case")
    if level == 'l1':
        hints.append("  3. Test: python3 scripts/main.py preflight")
    hints.append(f"  {'3' if level != 'l1' else '4'}. Add reference docs to references/ as needed")

    output({
        "status": "ok",
        "level": level,
        "env": env if level == 'l1' else None,
        "created": created,
        "hint": '\n'.join(hints),
    })


def cmd_validate(args):
    """Validate a generated skill's structural integrity."""
    skill_path = Path(args.path).resolve()
    if not skill_path.exists():
        error("not_found", f"Path does not exist: {skill_path}", recoverable=False)

    warnings = []

    # Check SKILL.md exists and has frontmatter
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        error("missing_skill_md", "SKILL.md not found", recoverable=False)

    content = skill_md.read_text(encoding='utf-8')

    # Check frontmatter
    if not content.startswith('---'):
        warnings.append("SKILL.md missing frontmatter (should start with ---)")
    else:
        fm_end = content.find('---', 3)
        if fm_end == -1:
            warnings.append("SKILL.md frontmatter not closed (missing closing ---)")
        else:
            fm = content[3:fm_end]
            if 'name:' not in fm:
                warnings.append("Frontmatter missing 'name' field")
            if 'description:' not in fm:
                warnings.append("Frontmatter missing 'description' field")
            if 'TODO' in fm:
                warnings.append("Frontmatter still contains TODO placeholders — replace before publishing")

    # Check unreplaced template tokens
    import re as _re
    tokens = _re.findall(r'\{\{[A-Z_]+\}\}', content)
    if tokens:
        warnings.append(f"Unreplaced template tokens found: {', '.join(set(tokens))}")

    # Check line count (context budget)
    line_count = len(content.splitlines())
    if line_count > 200:
        warnings.append(f"SKILL.md is {line_count} lines (recommended: ≤200). Move details to references/.")

    # Check referenced directories exist
    scripts_dir = skill_path / 'scripts'
    if 'scripts/' in content and not scripts_dir.exists():
        warnings.append("SKILL.md references scripts/ but the directory does not exist")

    references_dir = skill_path / 'references'
    if 'references/' in content and not references_dir.exists():
        warnings.append("SKILL.md references references/ but the directory does not exist")

    output({
        "status": "ok" if not warnings else "warnings",
        "path": str(skill_path),
        "line_count": line_count,
        "warnings": warnings,
        "hint": "All structural checks passed." if not warnings else f"{len(warnings)} issue(s) found — review before publishing.",
    })


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


def cmd_scaffold(args):
    """Run the scaffold command."""
    validate_name(args.name)

    if args.level != 'l1' and args.env != 'stdlib':
        error("invalid_args", "--env is only applicable for --level l1", recoverable=False)

    # Resolve templates directory (sibling of scripts/)
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / 'templates'
    if not templates_dir.exists():
        error("templates_missing", f"Templates directory not found at {templates_dir}", recoverable=False)

    scaffold(args.name, args.level, args.env, args.output, args.force, templates_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Generate agent skill from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("preflight", help="Check environment readiness")

    validate_parser = sub.add_parser("validate", help="Validate a generated skill's structure")
    validate_parser.add_argument('--path', required=True, help='Path to the skill directory to validate')

    scaffold_parser = sub.add_parser("scaffold", help="Generate skill from templates")
    scaffold_parser.add_argument('--name', required=True, help='Skill name (kebab-case, e.g. my-awesome-skill)')
    scaffold_parser.add_argument('--level', required=True, choices=['l0', 'l0plus', 'l1'],
                        help='Skill level: l0 (pure prompt), l0plus (prompt + helper), l1 (prompt + business scripts)')
    scaffold_parser.add_argument('--env', choices=['stdlib', 'uv', 'venv'], default='stdlib',
                        help='Environment strategy for L1 skills (default: stdlib)')
    scaffold_parser.add_argument('--output', default='.', help='Output directory (default: current directory)')
    scaffold_parser.add_argument('--force', action='store_true', help='Overwrite existing skill directory')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(2)

    if args.command == "preflight":
        cmd_preflight(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "scaffold":
        cmd_scaffold(args)


if __name__ == '__main__':
    main()
