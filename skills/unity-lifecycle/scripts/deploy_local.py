#!/usr/bin/env python3
"""Deploy qin-gemini-unity-skills into Google Antigravity (~/.gemini/config) without touching Codex or GEMINI.md."""

import argparse
import json
import shutil
from pathlib import Path

EXCLUDED_GLOBAL_SKILLS = {"ai-index"}


def default_repo_root():
    return Path(__file__).resolve().parents[3]


def default_config_dir():
    return Path.home() / ".gemini" / "config"


def target_points_into_repo(link_path, repo_root):
    if not link_path.is_symlink():
        return False
    try:
        resolved = link_path.resolve(strict=False)
        return resolved == repo_root or resolved.is_relative_to(repo_root)
    except OSError:
        return False


def discover_global_skills(skills_root):
    found = []
    for skill_path in sorted(skills_root.iterdir()):
        if not skill_path.is_dir() or skill_path.name.startswith(".") or skill_path.name in EXCLUDED_GLOBAL_SKILLS:
            continue
        if (skill_path / "SKILL.md").is_file():
            found.append(skill_path)
    return found


def update_skills_json(skills_json_path, skills_root):
    resolved_skills = str(skills_root.resolve())
    data = {"entries": []}
    if skills_json_path.is_file():
        try:
            loaded = json.loads(skills_json_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("entries"), list):
                data = loaded
        except (OSError, ValueError):
            data = {"entries": []}
    entries = data["entries"]
    existing = next((entry for entry in entries if isinstance(entry, dict) and entry.get("path") == resolved_skills), None)
    if existing is None:
        entries.append({"path": resolved_skills, "exclude": sorted(EXCLUDED_GLOBAL_SKILLS)})
    else:
        existing["exclude"] = sorted(EXCLUDED_GLOBAL_SKILLS)
    skills_json_path.parent.mkdir(parents=True, exist_ok=True)
    skills_json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def deploy(*, repo_root=None, config_dir=None):
    resolved_repo = (Path(repo_root) if repo_root else default_repo_root()).expanduser().resolve()
    skills_root = resolved_repo / "skills"
    resolved_config = (Path(config_dir) if config_dir else default_config_dir()).expanduser().resolve()
    config_skills_dir = resolved_config / "skills"
    skills_json_path = resolved_config / "skills.json"
    config_skills_dir.mkdir(parents=True, exist_ok=True)

    discovered = discover_global_skills(skills_root)
    discovered_names = {skill_path.name for skill_path in discovered}
    removed_stale = []
    for existing in sorted(config_skills_dir.iterdir()):
        if target_points_into_repo(existing, resolved_repo) and (existing.name in EXCLUDED_GLOBAL_SKILLS or existing.name not in discovered_names):
            existing.unlink()
            removed_stale.append(existing.name)

    deployed = []
    for skill_path in discovered:
        target = config_skills_dir / skill_path.name
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        try:
            target.symlink_to(skill_path.resolve(), target_is_directory=True)
        except OSError:
            shutil.copytree(skill_path.resolve(), target)
        deployed.append(skill_path.name)

    update_skills_json(skills_json_path, skills_root)
    return {
        "config_dir": str(resolved_config),
        "skills_json": str(skills_json_path),
        "deployed_skills": deployed,
        "removed_stale_links": removed_stale,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="Source qin-gemini-unity-skills repository root")
    parser.add_argument("--config-dir", type=Path, help="Target Antigravity config root (default: ~/.gemini/config)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = deploy(repo_root=args.repo_root, config_dir=args.config_dir)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Deployed {len(result['deployed_skills'])} Antigravity Unity skills -> {result['config_dir']}/skills: {', '.join(result['deployed_skills'])}")
        if result["removed_stale_links"]:
            print(f"Removed stale global links: {', '.join(result['removed_stale_links'])}")
        print(f"Updated {result['skills_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
