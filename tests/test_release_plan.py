from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/skill-open-sourcer/scripts/release_portfolio.py"


class ReleasePlanTests(unittest.TestCase):
    def command_env(self, **extra: str) -> dict[str, str]:
        return dict(os.environ, ZHIJIAN_ALLOW_TEST_REMOTE="1", **extra)

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()

    def make_repo(self, root: Path) -> None:
        (root / "skills/demo").mkdir(parents=True)
        (root / "docs/skills/demo").mkdir(parents=True)
        (root / "docs/changelogs").mkdir(parents=True)
        (root / "registry").mkdir(parents=True)
        (root / "skills/demo/SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo\n---\n", encoding="utf-8"
        )
        (root / "docs/skills/demo/README.md").write_text("# Demo\n", encoding="utf-8")
        (root / "docs/skills/demo/README.zh-CN.md").write_text("# 演示\n", encoding="utf-8")
        (root / "docs/changelogs/demo.md").write_text("# Changelog\n", encoding="utf-8")
        (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (root / "CONTRIBUTING.md").write_text("Contribute\n", encoding="utf-8")
        registry = {
            "schema_version": "1.0.0",
            "skills": [
                {
                    "name": "demo",
                    "lifecycle": "active",
                    "version": "1.0.0",
                    "path": "skills/demo",
                    "documentation": "docs/skills/demo/README.md",
                    "documentation_zh": "docs/skills/demo/README.zh-CN.md",
                    "changelog": "docs/changelogs/demo.md",
                    "canonical_tag": "demo/v1.0.0",
                    "validation": {"commands": [], "live_smoke": None},
                    "capabilities": {
                        "network": "none",
                        "subprocess": "none",
                        "filesystem": "read",
                        "credentials": "none",
                    },
                    "harnesses": ["codex"],
                }
            ],
        }
        (root / "registry/skills.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        (root / "registry/skills.schema.json").write_text("{}\n", encoding="utf-8")
        (root / "package-lock.json").write_text(
            json.dumps({"packages": {"node_modules/skills": {"version": "1.5.18"}}}),
            encoding="utf-8",
        )
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Test")
        self.git(root, "config", "user.email", "test@example.com")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "baseline")
        remote = root.parent / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            text=True,
            capture_output=True,
            check=True,
        )
        self.git(root, "remote", "add", "origin", str(remote))
        self.git(root, "push", "-u", "origin", "main")
        subprocess.run(
            ["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"],
            text=True,
            capture_output=True,
            check=True,
        )

    def plan(
        self, repo: Path, path: Path, *, source_checkout: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "plan",
                "--repo",
                str(repo),
                "--source-checkout",
                str(source_checkout or repo),
                "--all",
                "--dry-run",
                "--plan-out",
                str(path),
            ],
            text=True,
            capture_output=True,
            check=False,
            env=self.command_env(),
        )

    def test_plan_is_deterministic_and_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            first_path = Path(tmp) / "first.json"
            second_path = Path(tmp) / "second.json"
            first = self.plan(repo, first_path)
            second = self.plan(repo, second_path)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            first_data = json.loads(first_path.read_text(encoding="utf-8"))
            second_data = json.loads(second_path.read_text(encoding="utf-8"))
            self.assertEqual(first_data, second_data)
            self.assertEqual(first_data["releases"][0]["semver_reason"], "initial_baseline")
            self.assertTrue(first_data["releases"][0]["candidate_ref"].startswith("refs/zhijian-candidates/"))
            release = first_data["releases"][0]
            self.assertNotEqual(release["candidate_commit"], first_data["base_commit"])
            self.assertEqual(
                self.git(repo, "rev-parse", f"{release['candidate_commit']}^1"),
                first_data["base_commit"],
            )
            self.assertEqual(
                self.git(repo, "rev-parse", f"{release['candidate_commit']}^{{tree}}"),
                self.git(repo, "rev-parse", f"{first_data['base_commit']}^{{tree}}"),
            )
            self.assertNotIn("mirror", release)
            self.assertNotIn("mirror_tag", release)
            self.assertNotIn("mirror_export_digest", release)

            (repo / "skills/demo/SKILL.md").write_text("changed\n", encoding="utf-8")
            verify = subprocess.run(
                [sys.executable, str(SCRIPT), "verify", "--plan", str(first_path)],
                text=True,
                capture_output=True,
                check=False,
                env=self.command_env(),
            )
            self.assertEqual(verify.returncode, 2)
            self.assertIn("plan.stale", verify.stderr)

    def test_verify_rejects_remote_drift_without_local_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            self.assertEqual(self.plan(repo, plan_path).returncode, 0)

            peer = Path(tmp) / "peer"
            subprocess.run(
                ["git", "clone", str(Path(tmp) / "remote.git"), str(peer)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.git(peer, "config", "user.name", "Peer")
            self.git(peer, "config", "user.email", "peer@example.com")
            (peer / "REMOTE.md").write_text("remote drift\n", encoding="utf-8")
            self.git(peer, "add", "REMOTE.md")
            self.git(peer, "commit", "-m", "remote drift")
            self.git(peer, "push", "origin", "main")

            verify = subprocess.run(
                [sys.executable, str(SCRIPT), "verify", "--plan", str(plan_path)],
                text=True,
                capture_output=True,
                check=False,
                env=self.command_env(),
            )
            self.assertEqual(verify.returncode, 2)
            self.assertIn("plan.remote_changed", verify.stderr)

    def test_temporary_clone_plan_freezes_source_checkout_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            self.make_repo(source)
            integration = Path(tmp) / "integration"
            subprocess.run(
                ["git", "clone", str(Path(tmp) / "remote.git"), str(integration)],
                text=True,
                capture_output=True,
                check=True,
            )
            plan_path = Path(tmp) / "plan.json"
            planned = self.plan(integration, plan_path, source_checkout=source)
            self.assertEqual(planned.returncode, 0, planned.stderr)
            marker = source / ".git" / "zhijian-needs-sync.json"
            hook = source / ".git" / "hooks" / "pre-commit"
            self.assertTrue(marker.is_file())
            self.assertTrue(hook.is_file())
            self.assertTrue(os.access(hook, os.X_OK))

            (source / "blocked.txt").write_text("blocked\n", encoding="utf-8")
            self.git(source, "add", "blocked.txt")
            blocked = subprocess.run(
                ["git", "commit", "-m", "must not commit"],
                cwd=source,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("needs-sync", blocked.stderr)

    def test_each_skill_gets_a_distinct_detached_candidate_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            registry_path = repo / "registry/skills.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            second = json.loads(json.dumps(registry["skills"][0]))
            replacements = {
                "name": "demo-two",
                "path": "skills/demo-two",
                "documentation": "docs/skills/demo-two/README.md",
                "documentation_zh": "docs/skills/demo-two/README.zh-CN.md",
                "changelog": "docs/changelogs/demo-two.md",
                "canonical_tag": "demo-two/v1.0.0",
            }
            second.update(replacements)
            registry["skills"].append(second)
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            (repo / "skills/demo-two").mkdir()
            (repo / "skills/demo-two/SKILL.md").write_text(
                "---\nname: demo-two\ndescription: Demo two\n---\n", encoding="utf-8"
            )
            (repo / "docs/skills/demo-two").mkdir()
            (repo / "docs/skills/demo-two/README.md").write_text("# Demo two\n", encoding="utf-8")
            (repo / "docs/skills/demo-two/README.zh-CN.md").write_text("# 演示二\n", encoding="utf-8")
            (repo / "docs/changelogs/demo-two.md").write_text("# Changelog\n", encoding="utf-8")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-m", "add second skill")
            plan_path = Path(tmp) / "plan.json"
            self.assertEqual(self.plan(repo, plan_path).returncode, 0)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            candidates = {release["candidate_commit"] for release in plan["releases"]}
            self.assertEqual(len(candidates), 2)
            self.assertNotIn(plan["base_commit"], candidates)

    def test_ledger_updates_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            self.assertEqual(self.plan(repo, plan_path).returncode, 0)
            env = self.command_env(XDG_STATE_HOME=str(Path(tmp) / "state"))
            remote_sha = self.git(repo, "rev-parse", "origin/main")
            command = [
                sys.executable,
                str(SCRIPT),
                "record-step",
                "--plan",
                str(plan_path),
                "--skill",
                "demo",
                "--step",
                "canonical-pushed",
                "--remote-sha",
                remote_sha,
            ]
            first = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
            second = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))

    def test_post_merge_recording_accepts_a_new_head_containing_planned_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            self.assertEqual(self.plan(repo, plan_path).returncode, 0)

            (repo / "MERGED.md").write_text("merged main\n", encoding="utf-8")
            self.git(repo, "add", "MERGED.md")
            self.git(repo, "commit", "-m", "merge result")
            self.git(repo, "push", "origin", "main")
            merged_sha = self.git(repo, "rev-parse", "HEAD")
            command = [
                sys.executable,
                str(SCRIPT),
                "record-step",
                "--plan",
                str(plan_path),
                "--skill",
                "demo",
                "--step",
                "canonical-pushed",
                "--remote-sha",
                merged_sha,
            ]
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=False,
                env=self.command_env(XDG_STATE_HOME=str(Path(tmp) / "state")),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cleanup_deletes_only_the_planned_candidate_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            self.assertEqual(self.plan(repo, plan_path).returncode, 0)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            reference = plan["releases"][0]["candidate_ref"]
            cleanup = subprocess.run(
                [sys.executable, str(SCRIPT), "cleanup", "--plan", str(plan_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
            self.assertIn(reference, json.loads(cleanup.stdout)["removed"])
            self.assertNotEqual(
                subprocess.run(
                    ["git", "rev-parse", "--verify", reference],
                    cwd=repo,
                    capture_output=True,
                    check=False,
                ).returncode,
                0,
            )

    def test_cleanup_rejects_refs_outside_candidate_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            self.assertEqual(self.plan(repo, plan_path).returncode, 0)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["releases"][0]["candidate_ref"] = "refs/heads/main"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            cleanup = subprocess.run(
                [sys.executable, str(SCRIPT), "cleanup", "--plan", str(plan_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(cleanup.returncode, 2)
            self.assertIn("cleanup.ref_unsafe", cleanup.stderr)
            self.assertEqual(self.git(repo, "rev-parse", "refs/heads/main"), self.git(repo, "rev-parse", "HEAD"))


if __name__ == "__main__":
    unittest.main()
