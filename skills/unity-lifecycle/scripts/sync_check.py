#!/usr/bin/env python3
"""Check whether qin-gemini-unity-skills has drifted from its upstream qin-unity-skills template."""

import json
import os
import subprocess
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
STAMP_PATH = SKILLS_ROOT / "unity-lifecycle" / "references" / "UPSTREAM.json"

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


def remote_head(repo_url, branch="master"):
    try:
        listing = subprocess.run(["git", "ls-remote", repo_url, f"refs/heads/{branch}"], capture_output=True, text=True, check=False, shell=False, timeout=15, **hidden_process_options())
    except (OSError, subprocess.SubprocessError):
        return None
    if listing.returncode != 0 or not listing.stdout.strip():
        return None
    return listing.stdout.split()[0]


def main():
    try:
        stamp = json.loads(STAMP_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"SKIPPED: references/UPSTREAM.json is unreadable ({error}); cannot compare against upstream")
        return 0
    repo_url = stamp.get("repo")
    synced_commit = stamp.get("commit")
    branch = stamp.get("branch", "master")
    if not repo_url or not synced_commit:
        print("SKIPPED: references/UPSTREAM.json has no repo/commit stamp; cannot compare against upstream")
        return 0
    head = remote_head(repo_url, branch)
    if head is None:
        print("SKIPPED: upstream unreachable, using local mirrored Unity skills")
        return 0
    if head == synced_commit:
        print(f"SAME: local mirrored Unity skills match upstream {head[:12]}")
        return 0
    print(f"DRIFTED: upstream {head[:12]} != synced {synced_commit[:12]} — run: python3 -B skills/unity-lifecycle/scripts/sync_from_template.py --apply --deploy --verify")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
