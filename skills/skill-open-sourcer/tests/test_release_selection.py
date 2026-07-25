from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_portfolio.py"


class ReleaseSelectionTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()

    def make_repo(self, repo: Path) -> None:
        records = []
        for name in ("demo-one", "demo-two"):
            (repo / "skills" / name).mkdir(parents=True)
            (repo / "docs" / "skills" / name).mkdir(parents=True)
            (repo / "docs" / "changelogs").mkdir(parents=True, exist_ok=True)
            (repo / "skills" / name / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Demo\n---\n", encoding="utf-8"
            )
            (repo / "docs" / "skills" / name / "README.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )
            (repo / "docs" / "skills" / name / "README.zh-CN.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )
            (repo / "docs" / "changelogs" / f"{name}.md").write_text(
                "# Changelog\n", encoding="utf-8"
            )
            records.append(
                {
                    "name": name,
                    "lifecycle": "active",
                    "version": "1.0.0",
                    "path": f"skills/{name}",
                    "documentation": f"docs/skills/{name}/README.md",
                    "documentation_zh": f"docs/skills/{name}/README.zh-CN.md",
                    "changelog": f"docs/changelogs/{name}.md",
                    "canonical_tag": f"{name}/v1.0.0",
                    "validation": {"commands": [], "live_smoke": None},
                }
            )
        (repo / "registry").mkdir()
        (repo / "registry" / "skills.json").write_text(
            json.dumps({"schema_version": "1.0.0", "skills": records}),
            encoding="utf-8",
        )
        (repo / "registry" / "skills.schema.json").write_text("{}\n", encoding="utf-8")
        (repo / "package-lock.json").write_text(
            json.dumps({"packages": {"node_modules/skills": {"version": "1.5.18"}}}),
            encoding="utf-8",
        )
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Test")
        self.git(repo, "config", "user.email", "test@example.com")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "baseline")

    def run_plan(self, repo: Path, plan_path: Path, *selector: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "plan",
                "--repo",
                str(repo),
                *selector,
                "--dry-run",
                "--plan-out",
                str(plan_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_skill_selector_plans_only_the_named_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            result = self.run_plan(repo, plan_path, "--skill", "demo-two")
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual([release["skill"] for release in plan["releases"]], ["demo-two"])

    def test_unknown_skill_fails_before_candidate_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            result = self.run_plan(repo, plan_path, "--skill", "missing")
            self.assertEqual(result.returncode, 2)
            self.assertIn("plan.skill_unknown: missing", result.stderr)
            self.assertFalse(plan_path.exists())
            refs = self.git(repo, "for-each-ref", "--format=%(refname)", "refs/zhijian-candidates")
            self.assertEqual(refs, "")

    def test_all_and_skill_are_mutually_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            result = self.run_plan(repo, plan_path, "--all", "--skill", "demo-one")
            self.assertEqual(result.returncode, 2)
            self.assertIn("not allowed with argument", result.stderr)

    def test_skill_rejects_exclude(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            plan_path = Path(tmp) / "plan.json"
            result = self.run_plan(
                repo,
                plan_path,
                "--skill",
                "demo-one",
                "--exclude",
                "demo-two",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("plan.selector_conflict", result.stderr)


if __name__ == "__main__":
    unittest.main()
