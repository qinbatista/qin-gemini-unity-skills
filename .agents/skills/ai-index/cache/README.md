# Cache ownership and current state

Read this folder at task start/resume and finish. The project owns its Cache policy here; `current.json` is an ignored, replaceable current operational view refreshed with `project_ai_index.py cache --project-root ROOT --apply`.

- Task support, temporary upstream template clones, and test fixtures belong to a fresh `Cache/temp-*` run and are reclaimed immediately after verified delivery.
- `Cache/temp-task-cache-registry` is the local operational control registry; preserve it.
- Do not commit `current.json` or any `Cache/` files to Git. Antigravity and Codex sessions remain user-managed and excluded.
