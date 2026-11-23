# Unity lifecycle and template sync

[skills/unity-lifecycle/SKILL.md](../../../skills/unity-lifecycle/SKILL.md) adapts the mirrored `qin-unity-skills` pack to Google Antigravity without duplicating domain guidance.

- `skills/unity-lifecycle/scripts/sync_from_template.py` fetches `https://github.com/qinbatista/qin-unity-skills` (`master`) inside a managed `Cache/temp-*` scope, mirrors all upstream `*-skill/` folders verbatim, regenerates `references/global-skill-routing.md` and `references/UPSTREAM.json`, and optionally deploys and verifies.
- `skills/unity-lifecycle/scripts/deploy_local.py` deploys Unity global Skills into `~/.gemini/config/skills/` and appends `skills/` to `~/.gemini/config/skills.json` while preserving `qin-gemini-skills`, `~/.gemini/config/GEMINI.md`, and Codex isolation.
