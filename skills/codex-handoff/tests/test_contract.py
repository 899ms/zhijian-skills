from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class CodexHandoffContractTests(unittest.TestCase):
    def test_manual_activation_is_consistent(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        openai = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        interface = (ROOT / "agents" / "interface.yaml").read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation: true", skill)
        self.assertIn("allow_implicit_invocation: false", openai)
        self.assertIn('mode: "manual"', interface)

    def test_fresh_task_route_and_exclusions_are_explicit(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "list_projects",
            "create_thread",
            "set_thread_title",
            "wait_threads",
            "Do not use `fork_thread`",
            "Do not spawn a subagent",
            "Do not use `handoff_thread`",
            "Do not create or resume a handoff document",
            "Do not trigger on ordinary requests",
        ):
            self.assertIn(marker, skill)

    def test_compact_prompt_contract_is_complete(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "2,000–4,000 Chinese characters",
            "objective and first action",
            "completed work and current state",
            "decisions, constraints",
            "verification performed",
            "remaining work, blockers",
            "relevant installed Skills",
            "Point to authoritative artifacts",
            "secrets, credentials",
        ):
            self.assertIn(marker, skill)

    def test_trigger_suite_covers_route_confusion(self) -> None:
        cases = json.loads((ROOT / "evals" / "trigger_cases.json").read_text(encoding="utf-8"))
        semantic = json.loads((ROOT / "evals" / "semantic_config.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases["should_trigger"]), 5)
        self.assertGreaterEqual(len(cases["should_not_trigger"]), 5)
        self.assertGreaterEqual(len(cases["near_neighbor"]), 4)
        self.assertIn("explicit_handoff", semantic["positive_concepts"])
        self.assertIn("full_history_fork", semantic["negative_concepts"])

    def test_output_cases_are_valid_and_prefer_skill(self) -> None:
        lines = (ROOT / "evals" / "output" / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        cases = [json.loads(line) for line in lines if line.strip()]
        self.assertGreaterEqual(len(cases), 3)
        for case in cases:
            self.assertTrue(case["assertions"])
            self.assertEqual(case["human_review"]["expected_winner"], "with_skill")


if __name__ == "__main__":
    unittest.main()
