#!/usr/bin/env python3
"""Sync qin-gemini-unity-skills from its upstream qin-unity-skills template and regenerate Antigravity routing."""

import argparse
from contextlib import contextmanager
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILLS_ROOT.parent

DEFAULT_UPSTREAM_REPO = "https://github.com/qinbatista/qin-unity-skills"
DEFAULT_UPSTREAM_BRANCH = "master"
SKILL_DIR_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-skill$")
OMITTED_NAMES = {"__pycache__", ".DS_Store"}
OMITTED_SUFFIXES = {".pyc", ".pyo"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy_local
import verify_skills_local

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

ANTIGRAVITY_UNITY_ROUTING_ACTIVATION = """## Require routing across projects

Deploy the Unity Skills into Google Antigravity (`~/.gemini/config/skills/` and `~/.gemini/config/skills.json`) using `deploy_local.py` (or `sync_from_template.py --apply --deploy --verify`). Keep Codex configuration (`~/.codex`) and Codex user Skills (`~/.agents/skills`) completely isolated and untouched.

To refresh all Unity Skills and this routing guide from the canonical `qin-unity-skills` template at any time, run:

```bash
python3 -B ~/.gemini/config/skills/unity-lifecycle/scripts/sync_from_template.py --apply --deploy --verify
```

When `qin-gemini-skills` is also installed, its global `~/.gemini/config/GEMINI.md` and `task-lifecycle/references/global-skill-routing.md` automatically discover and load this Unity routing guide for Unity and C# work.
"""


def run_quiet(command, *, cwd=None, env=None, timeout=120):
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False, shell=False, timeout=timeout, **hidden_process_options())


@contextmanager
def managed_cache_scope(repo_root, task_key):
    workflow_scripts = Path.home() / ".gemini" / "config" / "skills" / "workflow-skill" / "scripts"
    if workflow_scripts.is_dir() and str(workflow_scripts) not in sys.path:
        sys.path.insert(0, str(workflow_scripts))
    try:
        from task_artifact_paths import task_artifact_scope
    except ImportError:
        task_artifact_scope = None
    if task_artifact_scope is not None:
        with task_artifact_scope(repo_root, task_key) as work_root:
            yield work_root
        return
    cache_dir = repo_root / "Cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    run_dir = cache_dir / f"temp-{task_key}-{uuid.uuid4().hex[:12]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield run_dir
    finally:
        if run_dir.exists():
            shutil.rmtree(run_dir)


def discover_upstream_skills(upstream_root):
    skills = []
    for child in sorted(upstream_root.iterdir()):
        if child.is_dir() and not child.is_symlink() and SKILL_DIR_PATTERN.fullmatch(child.name) and (child / "SKILL.md").is_file():
            skills.append(child.name)
    return skills


def collect_tree_hashes(directory):
    hashes = {}
    if not directory.is_dir():
        return hashes
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel_parts = path.relative_to(directory).parts
        if any(part in OMITTED_NAMES for part in rel_parts) or path.suffix.lower() in OMITTED_SUFFIXES:
            continue
        hashes[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def inspect_git_metadata(directory, repo_url, branch):
    git_dir = directory / ".git"
    if not git_dir.exists():
        return {"repo": repo_url, "branch": branch, "commit": "local-snapshot", "commit_date": datetime.date.today().isoformat(), "commit_subject": "Local upstream snapshot"}
    result = run_quiet(["git", "-C", str(directory), "log", "-1", "--format=%H%n%cI%n%s"])
    if result.returncode != 0:
        raise RuntimeError(f"Failed to read upstream git metadata: {(result.stderr or result.stdout).strip()}")
    lines = result.stdout.splitlines()
    commit = lines[0].strip() if len(lines) > 0 else "unknown"
    commit_date = lines[1].strip() if len(lines) > 1 else datetime.date.today().isoformat()
    commit_subject = lines[2].strip() if len(lines) > 2 else ""
    return {"repo": repo_url, "branch": branch, "commit": commit, "commit_date": commit_date, "commit_subject": commit_subject}


def remove_git_metadata_dir(git_dir):
    if not git_dir.exists():
        return
    for item in git_dir.rglob("*"):
        if item.is_file() and not item.is_symlink():
            item.chmod(0o644)
    shutil.rmtree(git_dir)


def clone_upstream_snapshot(repo_url, branch, work_root):
    git_bin = shutil.which("git")
    if git_bin is None:
        raise RuntimeError("git executable is required to fetch the upstream template repository")
    clone_dir = work_root / "upstream-template"
    git_env = os.environ.copy()
    git_env["GIT_TERMINAL_PROMPT"] = "0"
    result = run_quiet([git_bin, "clone", "--depth", "1", "--branch", branch, "--", repo_url, str(clone_dir)], env=git_env, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone {repo_url} ({branch}): {(result.stderr or result.stdout).strip()}")
    metadata = inspect_git_metadata(clone_dir, repo_url, branch)
    remove_git_metadata_dir(clone_dir / ".git")
    return clone_dir, metadata


def read_previous_stamp(stamp_path):
    if not stamp_path.is_file():
        return {}
    try:
        data = json.loads(stamp_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def mirror_upstream_skills(upstream_root, skills_root, previous_skills, *, apply_changes):
    discovered = discover_upstream_skills(upstream_root)
    if not discovered:
        raise ValueError(f"No global *-skill directories found in upstream template: {upstream_root}")
    changes = {"added": [], "updated": [], "removed": [], "retired_skills": []}
    for skill_name in discovered:
        src_dir = upstream_root / skill_name
        dst_dir = skills_root / skill_name
        src_hashes = collect_tree_hashes(src_dir)
        dst_hashes = collect_tree_hashes(dst_dir)
        for rel_path, src_hash in src_hashes.items():
            full_rel = f"{skill_name}/{rel_path}"
            if rel_path not in dst_hashes:
                changes["added"].append(full_rel)
            elif dst_hashes[rel_path] != src_hash:
                changes["updated"].append(full_rel)
            if apply_changes and dst_hashes.get(rel_path) != src_hash:
                target_file = dst_dir / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_dir / rel_path, target_file)
        for rel_path in sorted(set(dst_hashes) - set(src_hashes)):
            changes["removed"].append(f"{skill_name}/{rel_path}")
            if apply_changes:
                stale_file = dst_dir / rel_path
                if stale_file.exists() or stale_file.is_symlink():
                    stale_file.unlink()
        if apply_changes and dst_dir.is_dir():
            for subdir in sorted((p for p in dst_dir.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                if subdir.name == "__pycache__":
                    shutil.rmtree(subdir)
                elif not any(subdir.iterdir()):
                    subdir.rmdir()
    for old_skill in sorted(set(previous_skills) - set(discovered)):
        old_dir = skills_root / old_skill
        if old_dir.is_dir() and SKILL_DIR_PATTERN.fullmatch(old_skill):
            changes["retired_skills"].append(old_skill)
            if apply_changes:
                shutil.rmtree(old_dir)
    return discovered, changes


def extract_skill_description(skill_md_path):
    text = skill_md_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', text, re.MULTILINE)
    return match.group(1).strip() if match else "Matched upstream Unity Skill."


def build_global_unity_routing(upstream_root, mirrored_skills):
    source_path = upstream_root / "unity-code-skill" / "references" / "global-skill-routing.md"
    if not source_path.is_file():
        raise FileNotFoundError(f"Upstream Unity routing guide missing: {source_path}")
    text = source_path.read_text(encoding="utf-8")
    body = text.split("## Require routing across projects", 1)[0].rstrip()
    body = body.replace("# Unity Skill routing", "# Unity Skill routing (Antigravity / Gemini)")
    body = body.replace("(contributing.md", "(../../unity-code-skill/references/contributing.md")
    body = body.replace("(../SKILL.md", "(../../unity-code-skill/SKILL.md")
    body = body.replace("(../scripts/read_topic.py)", "(../../unity-code-skill/scripts/read_topic.py)")
    body = body.replace("<pack>/unity-code-skill/scripts/read_topic.py", "~/.gemini/config/skills/unity-code-skill/scripts/read_topic.py")
    body = body.replace("Resolve `<pack>` to the installed group or the plugin's `skills` directory.", "Antigravity installs all Unity Skills directly under `~/.gemini/config/skills/`.")
    lines = body.splitlines()
    for skill_name in mirrored_skills:
        token = f"../../{skill_name}/SKILL.md"
        if token not in body:
            desc = extract_skill_description(upstream_root / skill_name / "SKILL.md")
            table_idx = next((idx for idx, line in enumerate(lines) if line.startswith("| Requested result |")), None)
            if table_idx is not None:
                end_idx = table_idx + 1
                while end_idx + 1 < len(lines) and lines[end_idx + 1].startswith("|"):
                    end_idx += 1
                lines.insert(end_idx + 1, f"| {desc} | [{skill_name}]({token}) |")
    return "\n".join(lines).rstrip() + "\n\n" + ANTIGRAVITY_UNITY_ROUTING_ACTIVATION.strip() + "\n"


def sync_from_template(*, repo_root=REPO_ROOT, repo_url=DEFAULT_UPSTREAM_REPO, branch=DEFAULT_UPSTREAM_BRANCH, upstream_dir=None, apply_changes=False, deploy_local_flag=False, verify_flag=False, config_dir=None):
    skills_root = repo_root / "skills"
    adapter_root = skills_root / "unity-lifecycle"
    stamp_path = adapter_root / "references" / "UPSTREAM.json"
    routing_out = adapter_root / "references" / "global-skill-routing.md"
    previous_stamp = read_previous_stamp(stamp_path)
    previous_skills = previous_stamp.get("mirrored_skills", [])

    def execute_with_upstream(upstream_root, metadata):
        mirrored_skills, skill_changes = mirror_upstream_skills(upstream_root, skills_root, previous_skills, apply_changes=apply_changes)
        routing_text = build_global_unity_routing(upstream_root, mirrored_skills)
        generated_updates = []
        old_routing = routing_out.read_text(encoding="utf-8") if routing_out.is_file() else None
        if old_routing != routing_text:
            generated_updates.append(routing_out.relative_to(repo_root).as_posix())
            if apply_changes:
                routing_out.parent.mkdir(parents=True, exist_ok=True)
                routing_out.write_text(routing_text, encoding="utf-8")
        stamp_payload = {
            "repo": metadata["repo"],
            "branch": metadata["branch"],
            "commit": metadata["commit"],
            "commit_date": metadata["commit_date"],
            "commit_subject": metadata["commit_subject"],
            "synced_at": datetime.date.today().isoformat(),
            "mirrored_skills": mirrored_skills,
            "generated_files": [routing_out.relative_to(repo_root).as_posix()],
        }
        drifted = bool(skill_changes["added"] or skill_changes["updated"] or skill_changes["removed"] or skill_changes["retired_skills"] or generated_updates or previous_stamp.get("commit") != metadata["commit"])
        if apply_changes:
            stamp_path.parent.mkdir(parents=True, exist_ok=True)
            stamp_path.write_text(json.dumps(stamp_payload, indent=2) + "\n", encoding="utf-8")
        summary = {
            "status": "synced" if apply_changes else ("drifted" if drifted else "up_to_date"),
            "upstream": metadata,
            "previous_commit": previous_stamp.get("commit"),
            "mirrored_skills": mirrored_skills,
            "changes": skill_changes,
            "generated_updates": generated_updates,
        }
        if deploy_local_flag:
            summary["deploy"] = deploy_local.deploy(repo_root=repo_root, config_dir=config_dir)
        if verify_flag:
            verify_code = verify_skills_local.verify_all(repo_root=repo_root, config_dir=config_dir)
            summary["verify_exit_code"] = verify_code
            if verify_code != 0:
                summary["status"] = "verify_failed"
        return summary

    if upstream_dir is not None:
        upstream_path = Path(upstream_dir).expanduser().resolve()
        metadata = inspect_git_metadata(upstream_path, repo_url, branch)
        return execute_with_upstream(upstream_path, metadata)

    with managed_cache_scope(repo_root, "unity-template-sync") as work_root:
        clone_dir, metadata = clone_upstream_snapshot(repo_url, branch, work_root)
        return execute_with_upstream(clone_dir, metadata)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_UPSTREAM_REPO, help="Upstream template repository URL")
    parser.add_argument("--branch", default=DEFAULT_UPSTREAM_BRANCH, help="Upstream template branch")
    parser.add_argument("--upstream-dir", type=Path, help="Local upstream template checkout or fixture directory")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Target qin-gemini-unity-skills repository root")
    parser.add_argument("--config-dir", type=Path, help="Antigravity global config directory (default: ~/.gemini/config)")
    parser.add_argument("--apply", action="store_true", help="Write mirrored skills, routing adapter, and UPSTREAM.json")
    parser.add_argument("--deploy", action="store_true", help="Deploy synced Unity skills to Antigravity global config")
    parser.add_argument("--verify", action="store_true", help="Run verify_skills_local after sync/deploy")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary only")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    summary = sync_from_template(
        repo_root=args.repo_root.expanduser().resolve(),
        repo_url=args.repo,
        branch=args.branch,
        upstream_dir=args.upstream_dir,
        apply_changes=args.apply,
        deploy_local_flag=args.deploy,
        verify_flag=args.verify,
        config_dir=args.config_dir,
    )
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        ch = summary["changes"]
        print(f"Unity Template Sync [{summary['status']}]: {summary['upstream']['repo']} @ {summary['upstream']['commit'][:12]} ({summary['upstream']['commit_subject']})")
        print(f"Mirrored skills ({len(summary['mirrored_skills'])}): {', '.join(summary['mirrored_skills'])}")
        print(f"Files: +{len(ch['added'])} added, ~{len(ch['updated'])} updated, -{len(ch['removed'])} removed, retired_skills={len(ch['retired_skills'])}")
        print(f"Generated adapters updated: {summary['generated_updates'] or 'none'}")
    if summary["status"] == "verify_failed":
        return 1
    if not args.apply and summary["status"] == "drifted":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
