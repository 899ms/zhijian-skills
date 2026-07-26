from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import scan_skill_release  # noqa: E402


class SecretAssignmentTests(unittest.TestCase):
    def scan_source(self, filename: str, source: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("---\nname: fixture\ndescription: fixture\n---\n", encoding="utf-8")
            target = root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
            return scan_skill_release.scan(root)

    def test_python_runtime_credential_reads_are_allowed(self) -> None:
        result = self.scan_source(
            "runtime.py",
            """
import getpass
import os

api_key = os.environ.get("METASO_API_KEY", "")
token = token_match.group(1)
client_secret = config.get_secret()
db_password = getpass.getpass()
""",
        )
        self.assertEqual(result["status"], "clear", result["issues"])

    def test_javascript_runtime_references_are_allowed(self) -> None:
        result = self.scan_source(
            "runtime.js",
            """
const apiKey = process.env.METASO_API_KEY;
const token = session.token;
const client_secret = config.clientSecret;
""",
        )
        self.assertEqual(result["status"], "clear", result["issues"])

    def test_python_string_literals_and_mapping_values_are_blocked(self) -> None:
        first = "live_" + "A" * 24
        second = "session_" + "B" * 24
        third = "password_" + "C" * 24
        result = self.scan_source(
            "literal.py",
            f'api_key: str = "{first}"\nconfig = {{"auth_token": "{second}"}}\nsend(password="{third}")\n',
        )
        reasons = [issue["reason"] for issue in result["issues"]]
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(reasons.count("possible_secret:assignment_secret"), 3)

    def test_config_literals_are_blocked_but_placeholders_are_allowed(self) -> None:
        actual = "production_" + "C" * 24
        blocked = self.scan_source("config.yaml", f"client_secret: {actual}\n")
        allowed = self.scan_source("example.yaml", 'client_secret: "your-client-secret"\n')
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(allowed["status"], "clear", allowed["issues"])

    def test_generic_literals_in_test_fixtures_are_allowed(self) -> None:
        result = self.scan_source(
            "tests/test_fixture.py",
            'config = {"api_key": "super-secret-value"}\npassword = "fixture-password-value"\n',
        )
        self.assertEqual(result["status"], "clear", result["issues"])

    def test_provider_tokens_in_test_fixtures_are_still_blocked(self) -> None:
        actual = "ghp_" + "E" * 24
        result = self.scan_source("tests/test_fixture.py", f'github_token = "{actual}"\n')
        reasons = [issue["reason"] for issue in result["issues"]]
        self.assertEqual(result["status"], "blocked")
        self.assertIn("possible_secret:github_token", reasons)

    def test_cli_output_redacts_detected_values(self) -> None:
        actual = "ghp_" + "D" * 24
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("---\nname: fixture\ndescription: fixture\n---\n", encoding="utf-8")
            (root / "config.py").write_text(f'github_token = "{actual}"\n', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "scan_skill_release.py"), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(actual, result.stdout + result.stderr)
        self.assertIn("<redacted:", result.stdout)


if __name__ == "__main__":
    unittest.main()
