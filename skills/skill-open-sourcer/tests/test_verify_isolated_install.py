from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "verify_isolated_install.py"


class IsolatedInstallVerifierTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        skill = repo / "skills" / "demo-skill"
        (skill / "agents").mkdir(parents=True)
        (skill / "scripts").mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Demo.\n---\n",
            encoding="utf-8",
        )
        (skill / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
        (skill / "scripts" / "demo.py").write_text("print('demo')\n", encoding="utf-8")
        return repo

    def make_cli(self, root: Path, mode: str) -> Path:
        cli = root / "fake_cli.py"
        cli.write_text(
            textwrap.dedent(
                f"""
                from pathlib import Path
                import shutil
                import sys

                mode = {mode!r}
                if mode == "install-fail":
                    print("synthetic install failure", file=sys.stderr)
                    raise SystemExit(7)

                source = Path(sys.argv[2])
                skill = sys.argv[sys.argv.index("--skill") + 1]
                destination = Path.cwd() / ".agents" / "skills" / skill
                shutil.copytree(source / "skills" / skill, destination)

                if mode == "missing":
                    (destination / "scripts" / "demo.py").unlink()
                elif mode == "extra":
                    (destination / "unexpected.txt").write_text("extra", encoding="utf-8")
                elif mode == "changed":
                    (destination / "SKILL.md").write_text("changed", encoding="utf-8")
                """
            ).lstrip(),
            encoding="utf-8",
        )
        return cli

    def run_verifier(
        self,
        repo: Path,
        cli: Path,
        *,
        node_override: str | None = sys.executable,
        path: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(repo),
            "--skill",
            "demo-skill",
            "--cli",
            str(cli),
            "--json",
        ]
        if node_override:
            command.extend(("--node", node_override))
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            env={"PATH": path or os.environ.get("PATH", "")},
        )

    def test_complete_copy_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_verifier(self.make_repo(root), self.make_cli(root, "pass"))
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["phase"], "compare")
        self.assertEqual(payload["file_count"], 3)

    def test_generated_directories_are_excluded_from_the_payload_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self.make_repo(root)
            generated = repo / "skills" / "demo-skill" / "dist" / "qa"
            generated.mkdir(parents=True)
            (generated / "report.md").write_text("generated\n", encoding="utf-8")
            result = self.run_verifier(repo, self.make_cli(root, "pass"))
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["file_count"], 3)

    def test_install_failure_cannot_be_masked_by_later_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_verifier(
                self.make_repo(root), self.make_cli(root, "install-fail")
            )
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["phase"], "install")
        self.assertEqual(payload["install_returncode"], 7)

    def test_node_version_manager_shim_resolves_real_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary_dir = root / "bin"
            binary_dir.mkdir()
            shim = binary_dir / "node"
            shim.write_text(
                f"#!{sys.executable}\n"
                "import sys\n"
                f"print({sys.executable!r}) if sys.argv[1:] == ['-p', 'process.execPath'] else sys.exit(9)\n",
                encoding="utf-8",
            )
            shim.chmod(0o755)
            result = self.run_verifier(
                self.make_repo(root),
                self.make_cli(root, "pass"),
                node_override=None,
                path=str(binary_dir),
            )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_missing_extra_and_changed_files_fail(self) -> None:
        for mode, field in (("missing", "missing"), ("extra", "extra"), ("changed", "changed")):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result = self.run_verifier(self.make_repo(root), self.make_cli(root, mode))
                self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["phase"], "compare")
                self.assertTrue(payload[field])


if __name__ == "__main__":
    unittest.main()
