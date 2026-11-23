"""Tests for template-driven syncing from qin-unity-skills and Antigravity global deployment."""

import json
import sys
import unittest
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILLS_ROOT.parent

sys.path.insert(0, str(SKILLS_ROOT / "unity-lifecycle" / "scripts"))
import deploy_local
import sync_from_template
import verify_skills_local


SAMPLE_UNITY_ROUTING = """# Unity Skill routing

Apply project rules first. When the shared guidance falls short, [improve it](contributing.md#submit-a-skill-change).

## Choose by task

| Requested result | Start here |
| --- | --- |
| Implement or review C# | [Code](../SKILL.md) |
| Place or move assets | [Assets](../../unity-assets-skill/SKILL.md) |

## Read one section

The [reader](../scripts/read_topic.py) returns headings. Resolve `<pack>` to the installed group or the plugin's `skills` directory.

```text
macOS/Linux: python3 -B "<pack>/unity-code-skill/scripts/read_topic.py" assets
```

## Require routing across projects

Append this paragraph to Codex `developer_instructions`.
"""


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_mock_upstream(root):
    write_text(root / "unity-code-skill" / "SKILL.md", '---\nname: unity-code-skill\ndescription: "Unity C# code rules"\n---\n# Code\n')
    write_text(root / "unity-code-skill" / "references" / "global-skill-routing.md", SAMPLE_UNITY_ROUTING)
    write_text(root / "unity-code-skill" / "references" / "contributing.md", "# Contributing\n")
    write_text(root / "unity-code-skill" / "scripts" / "read_topic.py", 'print("## Choose by task")\n')
    write_text(root / "unity-assets-skill" / "SKILL.md", '---\nname: unity-assets-skill\ndescription: "Unity asset placement"\n---\n# Assets\n')
    write_text(root / "unity-audio-skill" / "SKILL.md", '---\nname: unity-audio-skill\ndescription: "Unity audio mixers and playback"\n---\n# Audio\n')


def build_mock_target_repo(root):
    write_text(root / "skills" / "unity-lifecycle" / "SKILL.md", '---\nname: unity-lifecycle\ndescription: "Antigravity Unity adapter"\n---\n# Unity Lifecycle\n')
    write_text(root / "skills" / "unity-lifecycle" / "references" / "UPSTREAM.json", json.dumps({"repo": "https://example.invalid/unity", "commit": "oldsha", "mirrored_skills": ["unity-code-skill", "unity-retired-skill"]}))
    write_text(root / "skills" / "unity-code-skill" / "references" / "obsolete.md", "# Old\n")
    write_text(root / "skills" / "unity-retired-skill" / "SKILL.md", '---\nname: unity-retired-skill\ndescription: "Retired"\n---\n')


class UnityTemplateSyncTests(unittest.TestCase):
    def test_sync_mirrors_adds_prunes_deploys_and_preserves_sibling_packs(self):
        with sync_from_template.managed_cache_scope(REPO_ROOT, "test-unity-sync") as work_root:
            upstream = work_root / "upstream"
            target_repo = work_root / "repo"
            fake_config = work_root / "gemini-config"
            core_skill = work_root / "core-code-skill"
            build_mock_upstream(upstream)
            build_mock_target_repo(target_repo)
            write_text(core_skill / "SKILL.md", '---\nname: code-skill\ndescription: "Core code skill"\n---\n')
            write_text(fake_config / "GEMINI.md", "# Core global rules untouched\n")
            write_text(fake_config / "skills.json", json.dumps({"entries": [{"path": "/existing/qin-gemini-skills/skills", "exclude": ["ai-index"]}]}))
            (fake_config / "skills").mkdir(parents=True, exist_ok=True)
            (fake_config / "skills" / "code-skill").symlink_to(core_skill, target_is_directory=True)
            (fake_config / "skills" / "unity-retired-skill").symlink_to(target_repo / "skills" / "unity-retired-skill", target_is_directory=True)

            summary = sync_from_template.sync_from_template(repo_root=target_repo, upstream_dir=upstream, apply_changes=True, deploy_local_flag=True, verify_flag=True, config_dir=fake_config)
            self.assertEqual(summary["status"], "synced")
            self.assertEqual(summary["verify_exit_code"], 0)
            self.assertEqual(summary["mirrored_skills"], ["unity-assets-skill", "unity-audio-skill", "unity-code-skill"])
            self.assertFalse((target_repo / "skills" / "unity-code-skill" / "references" / "obsolete.md").exists())
            self.assertFalse((target_repo / "skills" / "unity-retired-skill").exists())

            routing = (target_repo / "skills" / "unity-lifecycle" / "references" / "global-skill-routing.md").read_text(encoding="utf-8")
            self.assertIn("../../unity-code-skill/SKILL.md", routing)
            self.assertIn("../../unity-audio-skill/SKILL.md", routing)
            self.assertIn("~/.gemini/config/skills/unity-code-skill/scripts/read_topic.py", routing)
            self.assertIn("sync_from_template.py --apply --deploy --verify", routing)

            self.assertEqual((fake_config / "GEMINI.md").read_text(encoding="utf-8"), "# Core global rules untouched\n")
            self.assertTrue((fake_config / "skills" / "code-skill").is_symlink())
            self.assertFalse((fake_config / "skills" / "unity-retired-skill").exists() or (fake_config / "skills" / "unity-retired-skill").is_symlink())

            saved = json.loads((fake_config / "skills.json").read_text(encoding="utf-8"))
            paths = [entry["path"] for entry in saved["entries"]]
            self.assertIn("/existing/qin-gemini-skills/skills", paths)
            self.assertIn(str((target_repo / "skills").resolve()), paths)
            self.assertEqual(verify_skills_local.verify_all(repo_root=target_repo, config_dir=fake_config), 0)

    def test_check_mode_detects_drift_without_writes_and_clears_after_apply(self):
        with sync_from_template.managed_cache_scope(REPO_ROOT, "test-unity-check") as work_root:
            upstream = work_root / "upstream"
            target_repo = work_root / "repo"
            build_mock_upstream(upstream)
            build_mock_target_repo(target_repo)

            before = sync_from_template.sync_from_template(repo_root=target_repo, upstream_dir=upstream, apply_changes=False)
            self.assertEqual(before["status"], "drifted")
            self.assertFalse((target_repo / "skills" / "unity-audio-skill").exists())

            applied = sync_from_template.sync_from_template(repo_root=target_repo, upstream_dir=upstream, apply_changes=True)
            self.assertEqual(applied["status"], "synced")

            after = sync_from_template.sync_from_template(repo_root=target_repo, upstream_dir=upstream, apply_changes=False)
            self.assertEqual(after["status"], "up_to_date")


if __name__ == "__main__":
    unittest.main()
