from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class LightPlanContractTests(unittest.TestCase):
    def test_manual_activation_is_consistent(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        openai = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        interface = (ROOT / "agents" / "interface.yaml").read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation: true", skill)
        self.assertIn("allow_implicit_invocation: false", openai)
        self.assertIn('mode: "manual"', interface)

    def test_workflow_keeps_light_and_heavy_routes(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "3–7",
            "Direct execution",
            "Light plan and work",
            "Specialist Skill",
            "Discovery or brainstorming",
            "Heavy workflow",
            "Do not create a durable plan file by default",
        ):
            self.assertIn(marker, skill)

    def test_trigger_suite_has_all_buckets(self):
        cases = json.loads((ROOT / "evals" / "trigger_cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases["should_trigger"]), 4)
        self.assertGreaterEqual(len(cases["should_not_trigger"]), 5)
        self.assertGreaterEqual(len(cases["near_neighbor"]), 3)

    def test_output_eval_is_valid_jsonl(self):
        lines = (ROOT / "evals" / "output" / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        cases = [json.loads(line) for line in lines if line.strip()]
        self.assertGreaterEqual(len(cases), 4)
        for case in cases:
            self.assertTrue(case["assertions"])
            self.assertEqual(case["human_review"]["expected_winner"], "with_skill")

    def test_unrelated_global_verification_protocol_is_explicit(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (ROOT / "references" / "routing-and-verification.md").read_text(encoding="utf-8")
        output_cases = (ROOT / "evals" / "output" / "cases.jsonl").read_text(encoding="utf-8")

        for marker in (
            "pre-existing, unrelated work",
            "strongest safe task-scoped checks",
            "without claiming the repository is fully green",
            "Never revert, stash, edit, or stage unrelated work",
        ):
            self.assertIn(marker, skill)

        for marker in (
            "Blocked verification protocol",
            "exact command, exit status",
            "Do not describe the repository or release as fully green",
            "mandatory for a release",
        ):
            self.assertIn(marker, reference)

        self.assertIn('"id":"records-unrelated-global-gate"', output_cases)


if __name__ == "__main__":
    unittest.main()
