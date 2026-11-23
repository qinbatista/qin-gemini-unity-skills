# Ownership and placement

- `skills/unity-*-skill/` holds verbatim mirrors of the upstream Unity global Skills from `qin-unity-skills` (`unity-animation-skill`, `unity-assets-skill`, `unity-code-skill`, `unity-effects-skill`, `unity-testing-skill`, `unity-ui-skill`). Do not hand-patch mirrored files when a deterministic transform belongs in `sync_from_template.py`.
- [skills/unity-lifecycle/SKILL.md](../../../skills/unity-lifecycle/SKILL.md) owns the Antigravity Unity entry Skill, generated routing (`references/global-skill-routing.md`), upstream stamp (`references/UPSTREAM.json`), and adapter scripts/tests.
- `.agents/skills/ai-index/` is this project's local AI index only. Never install it globally under `~/.gemini/config/skills/`.
- Keep temporary clones, fixtures, and scratch in ignored `Cache/temp-*`.
