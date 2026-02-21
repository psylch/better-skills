#!/usr/bin/env python3
"""Scaffold generator for Claude Code skills.

Non-interactive script that generates skill project files from templates.
All user interaction happens through Claude's dialogue — this script only
accepts CLI arguments and outputs JSON.

Usage:
    scaffold.py --name <name> --level l0|l0plus|l1 [--env stdlib|uv|venv] [--output <dir>] [--force]
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate Claude Code skill from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--name', required=True, help='Skill name (kebab-case, e.g. my-awesome-skill)')
    parser.add_argument('--level', required=True, choices=['l0', 'l0plus', 'l1'],
                        help='Skill level: l0 (pure prompt), l0plus (prompt + helper), l1 (prompt + business scripts)')
    parser.add_argument('--env', choices=['stdlib', 'uv', 'venv'], default='stdlib',
                        help='Environment strategy for L1 skills (default: stdlib)')
    parser.add_argument('--output', default='.', help='Output directory (default: current directory)')
    parser.add_argument('--force', action='store_true', help='Overwrite existing skill directory')
    args = parser.parse_args()

    validate_name(args.name)

    if args.level != 'l1' and args.env != 'stdlib':
        error("invalid_args", "--env is only applicable for --level l1", recoverable=False)

    # Resolve templates directory (sibling of scripts/)
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / 'templates'
    if not templates_dir.exists():
        error("templates_missing", f"Templates directory not found at {templates_dir}", recoverable=False)

    scaffold(args.name, args.level, args.env, args.output, args.force, templates_dir)


if __name__ == '__main__':
    main()
