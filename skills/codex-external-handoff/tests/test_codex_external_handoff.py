from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_external_handoff.py"


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import sys

if "--version" in sys.argv:
    print("codex-cli test")
    raise SystemExit(0)

if len(sys.argv) < 2 or sys.argv[1] != "app-server":
    raise SystemExit(2)

thread_id = "019fake0-0000-7000-8000-000000000001"
turn_id = "turn_fake_1"
final = {
    "status": "completed",
    "conclusion": "fake result",
    "evidence": [{"source": "/tmp/source.md", "finding": "verified"}],
    "risks": [],
    "artifacts": [],
    "recommended_actions": ["review"],
    "suggested_state_delta": ""
}

def send(message):
    print(json.dumps(message, ensure_ascii=False), flush=True)

for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        send({"id": request_id, "result": {"userAgent": "fake"}})
    elif method == "initialized":
        pass
    elif method == "account/read":
        send({"id": request_id, "result": {"account": {"type": "chatgpt"}}})
    elif method == "thread/start":
        send({"id": request_id, "result": {"thread": {"id": thread_id, "ephemeral": False}}})
    elif method == "thread/resume":
        send({"id": request_id, "result": {"thread": {"id": message["params"]["threadId"], "ephemeral": False}}})
    elif method == "thread/name/set":
        send({"id": request_id, "result": {}})
    elif method == "turn/start":
        send({"id": request_id, "result": {"turn": {"id": turn_id, "status": "inProgress", "items": []}}})
        text = json.dumps(final, ensure_ascii=False)
        send({"method": "item/completed", "params": {"item": {"type": "agentMessage", "text": text}}})
        send({"method": "turn/completed", "params": {"turn": {"id": turn_id, "status": "completed", "items": []}}})
    elif method == "turn/interrupt":
        send({"id": request_id, "result": {}})
        send({"method": "turn/completed", "params": {"turn": {"id": turn_id, "status": "interrupted", "items": []}}})
'''


class ExternalHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        fake = self.bin_dir / "codex"
        fake.write_text(textwrap.dedent(FAKE_CODEX), encoding="utf-8")
        fake.chmod(0o755)
        self.project = self.root / "project"
        self.project.mkdir()
        self.state = self.root / "state"
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.bin_dir}{os.pathsep}{self.env.get('PATH', '')}"
        self.env["CODEX_EXTERNAL_HANDOFF_HOME"] = str(self.state)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, expected: int = 0) -> dict:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.project,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            completed.returncode,
            expected,
            msg=f"stdout={completed.stdout}\nstderr={completed.stderr}",
        )
        return json.loads(completed.stdout)

    def test_doctor_checks_app_server_and_account(self) -> None:
        result = self.run_cli("doctor")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["account_type"], "chatgpt")

    def test_ask_result_continue_and_open_contract(self) -> None:
        asked = self.run_cli(
            "ask",
            "--title",
            "测试 Thread",
            "--task",
            "只返回测试结果",
            "--cwd",
            str(self.project),
            "--wait",
        )
        self.assertEqual(asked["status"], "completed")
        self.assertEqual(asked["thread_id"], "019fake0-0000-7000-8000-000000000001")
        self.assertEqual(asked["result"]["conclusion"], "fake result")
        self.assertFalse((self.state / "jobs" / f"{asked['job_id']}.request.json").exists())

        result = self.run_cli("result", asked["job_id"])
        self.assertEqual(result["result"]["evidence"][0]["finding"], "verified")

        followed = self.run_cli(
            "continue",
            asked["thread_id"],
            "--task",
            "继续测试",
            "--cwd",
            str(self.project),
            "--wait",
        )
        self.assertEqual(followed["thread_id"], asked["thread_id"])
        self.assertEqual(followed["parent_job_id"], asked["job_id"])

        opened = self.run_cli("open", asked["job_id"], "--print-only")
        self.assertEqual(opened["codex_url"], f"codex://threads/{asked['thread_id']}")
        self.assertFalse(opened["opened"])

    def test_task_and_task_file_are_mutually_exclusive(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "ask",
                "--title",
                "invalid",
                "--task",
                "one",
                "--task-file",
                "two.md",
            ],
            cwd=self.project,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("必须且只能提供", completed.stderr)


if __name__ == "__main__":
    unittest.main()
