# Verification owner

- Run `python3 -B skills/unity-lifecycle/scripts/verify_skills_local.py --with-tests` to verify `UPSTREAM.json`, `~/.gemini/config/skills.json`, deployed Unity skill frontmatter and AST, routing link validity, `read_topic.py` runtime execution, source portability, and unit tests (`unity-lifecycle`, `unity-code-skill`).
- Run `python3 -B skills/unity-lifecycle/scripts/sync_check.py` to check upstream drift read-only. Never invoke `deploy_local.py` merely to inspect an installation. Keep all test fixtures inside project `Cache/temp-*`.
