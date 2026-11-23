# qin-gemini-unity-skills Contract

Read the [project AI index](.agents/skills/ai-index/SKILL.md), then only the relevant route.

- This repository owns the Google Antigravity / Gemini port of Qin's reusable Unity and C# skills, using [`qin-unity-skills`](https://github.com/qinbatista/qin-unity-skills) as its canonical upstream template.
- **Fast template update**: Whenever asked to update or sync this repository from `qin-unity-skills`, run `python3 -B skills/unity-lifecycle/scripts/sync_from_template.py --apply --deploy --verify`, review the synced changes, run affected tests (`verify_skills_local.py --with-tests`), update `.agents/skills/ai-index/` if contracts changed, clean disposable Cache runs, and commit and push to `origin/main` when authorized.
- **Two-layer ownership**:
  - `skills/unity-*-skill/` mirrors all upstream Unity global Skills verbatim from `qin-unity-skills` (do not hand-patch mirrored files so repeat syncs remain clean and upstream checks pass).
  - `skills/unity-lifecycle/` owns the Antigravity Unity entry Skill, generated routing (`references/global-skill-routing.md`), upstream provenance (`references/UPSTREAM.json`), template-sync/deploy/verify scripts, and Antigravity tests.
- **Global Antigravity deployment**: `deploy_local.py` installs Unity global Skills only into `~/.gemini/config/skills/` and appends `skills/` to `~/.gemini/config/skills.json` without overwriting `~/.gemini/config/GEMINI.md` or unrelated Skills. Project-local `.agents/skills/ai-index` is never installed globally.
- **Codex isolation**: Keep Codex configuration (`~/.codex`) and Codex user Skills (`~/.agents/skills`) completely isolated and untouched.
- **English authoring & Cache**: Write all project docs, Skills, `AGENTS.md`, AI-index guidance, and durable Obsidian memory in English. Keep temporary clones, fixtures, and scratch in ignored `Cache/temp-*` and reclaim them immediately after delivery.

Done means synced Unity Skills and generated routing match upstream, `verify_skills_local.py --with-tests` and code/platform guards pass, `~/.gemini/config/` readbacks match source, `.agents/skills/ai-index/` is current, and Git/memory status are reported accurately.
