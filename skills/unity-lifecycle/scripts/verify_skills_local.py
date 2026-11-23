#!/usr/bin/env python3
"""Verify that Google Antigravity Unity skills, routing links, and scripts are valid and effective."""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILLS_ROOT.parent
MACHINE_PATH_PATTERN = re.compile(r"(?:/Users/[A-Za-z0-9._-]+|[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._-]+)")

UNITY_CODE_SCRIPTS = SKILLS_ROOT / "unity-code-skill" / "scripts"
if UNITY_CODE_SCRIPTS.is_dir():
    sys.path.insert(0, str(UNITY_CODE_SCRIPTS))

try:
    from hidden_process import hidden_process_options
except ImportError:
    def hidden_process_options():
        if os.name != "nt":
            return {}
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0), "startupinfo": startupinfo}


def read_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as err:
        return None, str(err)


def parse_frontmatter(content):
    if not content.startswith("---"):
        return None
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip().strip('"').strip("'")
    return data


def check_python_syntax(scripts_dir):
    errors = []
    if not scripts_dir.is_dir():
        return errors, 0
    scripts = sorted(scripts_dir.glob("*.py"))
    for py_file in scripts:
        try:
            ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as err:
            errors.append(f"{py_file.name}: {err}")
    return errors, len(scripts)


def check_markdown_links(markdown_path):
    broken = []
    text = markdown_path.read_text(encoding="utf-8")
    for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if raw_target.startswith(("http://", "https://", "#")):
            continue
        rel = raw_target.split("#", 1)[0]
        if not (markdown_path.parent / rel).exists():
            broken.append(raw_target)
    return broken


def check_repo_portability(adapter_root):
    hits = []
    for path in sorted(adapter_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        if MACHINE_PATH_PATTERN.search(path.read_text(encoding="utf-8", errors="replace")):
            hits.append(path.relative_to(adapter_root).as_posix())
    return hits


def run_test_suites(repo_root):
    suites = [
        ("unity-lifecycle tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(repo_root / "skills" / "unity-lifecycle" / "tests"), "-p", "test_*.py"]),
        ("unity-code-skill tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(repo_root / "skills" / "unity-code-skill" / "tests"), "-p", "test_*.py"]),
    ]
    results = []
    for label, cmd in suites:
        proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False, shell=False, timeout=180, **hidden_process_options())
        detail = "ok" if proc.returncode == 0 else (proc.stderr or proc.stdout).strip().splitlines()[-1]
        results.append((label, proc.returncode == 0, detail))
    return results


def verify_all(*, repo_root=None, config_dir=None, with_tests=False):
    resolved_repo = (Path(repo_root) if repo_root else REPO_ROOT).expanduser().resolve()
    repo_skills_dir = resolved_repo / "skills"
    adapter_root = repo_skills_dir / "unity-lifecycle"
    resolved_config = (Path(config_dir) if config_dir else Path.home() / ".gemini" / "config").expanduser().resolve()
    gemini_skills_dir = resolved_config / "skills"
    skills_json_path = resolved_config / "skills.json"
    stamp_path = adapter_root / "references" / "UPSTREAM.json"
    routing_path = adapter_root / "references" / "global-skill-routing.md"

    results = []
    stamp = {}
    if not stamp_path.is_file():
        results.append(("UPSTREAM.json", False, "Missing references/UPSTREAM.json"))
    else:
        loaded_stamp, stamp_err = read_json_file(stamp_path)
        if stamp_err is not None or not isinstance(loaded_stamp, dict):
            results.append(("UPSTREAM.json", False, stamp_err or "Invalid JSON object"))
        else:
            stamp = loaded_stamp
            mirrored = stamp.get("mirrored_skills", [])
            ok = bool(stamp.get("repo") and stamp.get("commit") and isinstance(mirrored, list) and mirrored)
            results.append(("UPSTREAM.json", ok, f"{stamp.get('commit', '')[:12]} ({len(mirrored)} mirrored skills)"))

    if not skills_json_path.is_file():
        results.append(("skills.json", False, f"Missing {skills_json_path}"))
    else:
        s_data, s_err = read_json_file(skills_json_path)
        if s_err is not None or not isinstance(s_data, dict):
            results.append(("skills.json", False, s_err or "Invalid JSON object"))
        else:
            paths = [entry.get("path") for entry in s_data.get("entries", []) if isinstance(entry, dict)]
            ok = str(repo_skills_dir.resolve()) in paths
            results.append(("skills.json registration", ok, f"Registered: {repo_skills_dir}" if ok else f"Not found in {paths}"))

    expected_skills = ["unity-lifecycle", *stamp.get("mirrored_skills", [])]
    for skill_name in expected_skills:
        skill_dir = gemini_skills_dir / skill_name
        skill_md = skill_dir / "SKILL.md"
        if not skill_dir.exists() or not skill_md.is_file():
            results.append((skill_name, False, f"Missing deployed SKILL.md under {skill_dir}"))
            continue
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        if not fm or "name" not in fm or "description" not in fm:
            results.append((skill_name, False, f"Invalid frontmatter in {skill_md}"))
            continue
        script_errors, scripts_count = check_python_syntax(skill_dir / "scripts")
        if script_errors:
            results.append((skill_name, False, f"Python syntax errors: {script_errors}"))
        else:
            results.append((skill_name, True, f"name='{fm['name']}', desc_len={len(fm['description'])}, scripts={scripts_count}"))

    if not routing_path.is_file():
        results.append(("global-skill-routing.md", False, "Missing generated routing guide"))
    else:
        routing_text = routing_path.read_text(encoding="utf-8")
        missing_routes = [name for name in stamp.get("mirrored_skills", []) if f"../../{name}/SKILL.md" not in routing_text]
        broken_links = check_markdown_links(routing_path)
        ok = not missing_routes and not broken_links
        detail = "All Unity skills routed & links valid" if ok else f"missing={missing_routes}, broken={broken_links}"
        results.append(("global-skill-routing.md", ok, detail))

    read_topic_script = gemini_skills_dir / "unity-code-skill" / "scripts" / "read_topic.py"
    if read_topic_script.is_file():
        topic_proc = subprocess.run([sys.executable, "-B", str(read_topic_script)], capture_output=True, text=True, check=False, shell=False, timeout=30, **hidden_process_options())
        ok = topic_proc.returncode == 0 and "Choose by task" in topic_proc.stdout
        results.append(("read_topic.py runtime", ok, "Task menu readback OK" if ok else (topic_proc.stderr or topic_proc.stdout).strip()[:160]))

    portable_hits = check_repo_portability(adapter_root)
    results.append(("source portability", not portable_hits, "No machine-local home paths" if not portable_hits else f"Hardcoded paths in: {portable_hits}"))

    if with_tests:
        results.extend(run_test_suites(resolved_repo))

    overall_pass = all(item[1] for item in results)
    print("\n" + "=" * 68)
    print("GOOGLE ANTIGRAVITY UNITY SKILL VERIFICATION REPORT")
    print("=" * 68)
    for name, ok, details in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name:<28} -> {details}")
    print("=" * 68)
    print(f"OVERALL STATUS: {'ALL PASS' if overall_pass else 'FAILURES DETECTED'}")
    print("=" * 68 + "\n")
    return 0 if overall_pass else 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="Repository root (default: derived from script location)")
    parser.add_argument("--config-dir", type=Path, help="Antigravity config directory (default: ~/.gemini/config)")
    parser.add_argument("--with-tests", action="store_true", help="Also run unity-lifecycle and unity-code-skill unit tests")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    return verify_all(repo_root=args.repo_root, config_dir=args.config_dir, with_tests=args.with_tests)


if __name__ == "__main__":
    raise SystemExit(main())
