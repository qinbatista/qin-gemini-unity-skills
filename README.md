# qin-gemini-unity-skills

Qin's reusable Unity and C# global Skills adapted for **Google Antigravity** and **Gemini**, continuously synced from [`qin-unity-skills`](https://github.com/qinbatista/qin-unity-skills) as its canonical template.

Pair with `qin-gemini-skills` for general task scope, Cache discipline, verification boundaries, Git delivery, and Obsidian project memory.

## Included Global Skills

| Skill | Role | Source |
| --- | --- | --- |
| [`unity-lifecycle`](skills/unity-lifecycle/SKILL.md) | Antigravity Unity entry adapter, task routing, and template-sync runner | Antigravity adapter |
| [`unity-code-skill`](skills/unity-code-skill/SKILL.md) | C# style, gameplay ownership, Jobs, GC, serialization, SDK integration, `csharp_rule_guard.py`, `read_topic.py` | Mirrored from `qin-unity-skills` |
| [`unity-assets-skill`](skills/unity-assets-skill/SKILL.md) | Prefab placement, asset moves, serialized consumers, and texture intake/compression | Mirrored from `qin-unity-skills` |
| [`unity-ui-skill`](skills/unity-ui-skill/SKILL.md) | UI Toolkit and Canvas layout, input, localization, and safe-area screen adaptation | Mirrored from `qin-unity-skills` |
| [`unity-animation-skill`](skills/unity-animation-skill/SKILL.md) | Clips, transitions, Blend Trees, 2D/3D rigs, and Spine playback contracts | Mirrored from `qin-unity-skills` |
| [`unity-effects-skill`](skills/unity-effects-skill/SKILL.md) | Particles, shaders, VFX Graph bindings, material ownership, and replay checks | Mirrored from `qin-unity-skills` |
| [`unity-testing-skill`](skills/unity-testing-skill/SKILL.md) | Native Edit/Play Mode tests, frame/memory profiling, and test package verification | Mirrored from `qin-unity-skills` |

Full Unity sample projects and casebooks live in upstream [`qin-unity-skills/examples`](https://github.com/qinbatista/qin-unity-skills/tree/master/examples).

## Fast Update from `qin-unity-skills`

Whenever upstream `qin-unity-skills` changes, update everything (mirror Unity Skills, regenerate Antigravity routing, deploy globally, and verify) in one command:

```bash
python3 -B skills/unity-lifecycle/scripts/sync_from_template.py --apply --deploy --verify
```

To check drift without modifying files:

```bash
python3 -B skills/unity-lifecycle/scripts/sync_check.py
```

## Global Deployment to Antigravity

```bash
python3 -B skills/unity-lifecycle/scripts/deploy_local.py
```

This symlinks all 7 Unity global Skills into `~/.gemini/config/skills/` and appends `skills/` to `~/.gemini/config/skills.json` (preserving `qin-gemini-skills`, unrelated Skills, and `~/.gemini/config/GEMINI.md`). Codex paths (`~/.codex` and `~/.agents/skills`) remain completely untouched.

## Local Verification

```bash
python3 -B skills/unity-lifecycle/scripts/verify_skills_local.py --with-tests
```
