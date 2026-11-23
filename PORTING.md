# Template Sync: `qin-unity-skills` → `qin-gemini-unity-skills`

This repository mirrors Qin's canonical Unity and C# global Skills from [`https://github.com/qinbatista/qin-unity-skills`](https://github.com/qinbatista/qin-unity-skills) and layers a thin, repeatable **Google Antigravity / Gemini** adapter on top so updates stay fast, deterministic, and conflict-free.

## Architecture

1. **Verbatim Upstream Mirror (`skills/unity-*-skill/`)**
   `skills/unity-lifecycle/scripts/sync_from_template.py` dynamically discovers every `<name>-skill/` directory at the root of `qin-unity-skills` (currently `unity-animation-skill`, `unity-assets-skill`, `unity-code-skill`, `unity-effects-skill`, `unity-testing-skill`, and `unity-ui-skill`), mirrors all files verbatim (including C# assets, `csharp_rule_guard.py`, `read_topic.py`, `unity_cli_daily.py`, and upstream tests), adds any new upstream Skills, and prunes retired files or Skills.

2. **Deterministic Antigravity Adapter (`skills/unity-lifecycle/`)**
   From the mirrored upstream sources, `sync_from_template.py` automatically regenerates:
   - `skills/unity-lifecycle/references/global-skill-routing.md` — adapted from `unity-code-skill/references/global-skill-routing.md` with resolved relative links, `~/.gemini/config/skills/` paths for `read_topic.py`, and Antigravity activation/update commands.
   - `skills/unity-lifecycle/references/UPSTREAM.json` — records the exact upstream repository, branch, commit SHA, commit date/subject, sync date, and mirrored Skill list.

## Fast Template Update

Run one command from this repository (or from any workspace via the installed symlink):

```bash
python3 -B skills/unity-lifecycle/scripts/sync_from_template.py --apply --deploy --verify
```

To check drift without modifying files:

```bash
python3 -B skills/unity-lifecycle/scripts/sync_check.py
python3 -B skills/unity-lifecycle/scripts/sync_from_template.py
```

## Antigravity Global Integration & Codex Isolation

- `skills/unity-lifecycle/scripts/deploy_local.py` deploys ONLY Unity global Skills (`unity-lifecycle` + mirrored `unity-*-skill` directories; never project-local `ai-index`) into `~/.gemini/config/skills/` and appends `skills/` to `~/.gemini/config/skills.json` while preserving `qin-gemini-skills`, unrelated Skills, and `~/.gemini/config/GEMINI.md`.
- `skills/unity-lifecycle/scripts/verify_skills_local.py --with-tests` verifies `UPSTREAM.json`, `skills.json`, deployed frontmatter and Python AST syntax, routing coverage and link integrity, `read_topic.py` runtime output, source portability, and unit tests.
- Codex configuration (`~/.codex`) and Codex user Skills (`~/.agents/skills`) are never modified.
