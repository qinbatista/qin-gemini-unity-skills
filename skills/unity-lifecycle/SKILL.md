---
name: unity-lifecycle
description: "Qin's Google Antigravity entry and template-sync adapter for the mirrored qin-unity-skills pack. Routes Unity and C# work to the six installed unity-*-skill Skills under ~/.gemini/config/skills/ and runs fast one-command template updates from qin-unity-skills."
---

# Unity Lifecycle (Antigravity / Gemini Adapter)

This Skill is the Google Antigravity entry layer for Qin's reusable Unity and C# Skills mirrored from [`qin-unity-skills`](https://github.com/qinbatista/qin-unity-skills). It keeps zero duplicate copies of Unity coding, asset, UI, animation, effects, or testing guidance — those live directly in their mirrored sibling Skills so updates never drift.

## Global Routing

For Unity or C# work, follow the receiving project's startup and source-owner rules first, then read [Unity Skill routing](references/global-skill-routing.md) and open every matching installed `SKILL.md` under `~/.gemini/config/skills/`:

- [Unity Code](../unity-code-skill/SKILL.md): C# style, gameplay ownership, Jobs, GC, serialization, SDK integration, `csharp_rule_guard.py`, and `read_topic.py`.
- [Unity Assets](../unity-assets-skill/SKILL.md): prefab placement, asset moves, serialized consumers, and texture intake/compression.
- [Unity UI](../unity-ui-skill/SKILL.md): UI Toolkit and Canvas layout, input, localization, and safe-area adaptation.
- [Unity Animation](../unity-animation-skill/SKILL.md): clips, transitions, Blend Trees, rigs, and Spine playback contracts.
- [Unity Effects](../unity-effects-skill/SKILL.md): particles, shaders, VFX Graph bindings, and visual replay checks.
- [Unity Testing](../unity-testing-skill/SKILL.md): native Edit/Play Mode tests, frame/memory profiling, and test package verification.

Use the general Antigravity Skills (`task-analyze-skill`, `workflow-skill`, `code-skill`, `verify-skill`, `project-memory-skill`, `management-skill`) from `qin-gemini-skills` for shared task scope, Cache discipline, verification boundaries, Git delivery, and Obsidian memory.

## Antigravity Runtime & Isolation

- **Global Skills root**: `~/.gemini/config/skills/` (registered via `~/.gemini/config/skills.json`). Project-local `ai-index` Skills are never installed globally.
- **Preserves core global rules**: `deploy_local.py` installs only Unity Skills and appends this repository's `skills/` entry to `~/.gemini/config/skills.json` without overwriting `~/.gemini/config/GEMINI.md` or unrelated Skills.
- **Codex isolation**: Keep `~/.codex/` and `~/.agents/skills/` completely untouched.

## Fast Template Update from `qin-unity-skills`

Whenever the user asks to update `qin-gemini-unity-skills` or sync from the `qin-unity-skills` template:

1. Check upstream drift (read-only):
   `python3 -B ~/.gemini/config/skills/unity-lifecycle/scripts/sync_check.py`
2. Pull the latest upstream `qin-unity-skills` template, mirror all `unity-*-skill` folders verbatim (adding new ones, updating changed ones, pruning retired ones), regenerate `references/global-skill-routing.md` and `references/UPSTREAM.json`, deploy to `~/.gemini/config/`, and verify:
   `python3 -B ~/.gemini/config/skills/unity-lifecycle/scripts/sync_from_template.py --apply --deploy --verify`
3. Run `verify_skills_local.py --with-tests`, update `.agents/skills/ai-index/` if module or script contracts changed, clean disposable Cache runs, and commit/push on `main` when authorized.
