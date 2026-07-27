from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = ROOT / "skills/codex-model-routing-team"
CONTRACT = Path(__file__).with_name("codex-model-routing-team-expected.json")


class SkillContractTests(unittest.TestCase):
    def test_worker_budget_fits_total_cap(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        budget = contract["deep_research_budget"]
        self.assertLessEqual(sum(budget.values()), contract["max_total_workers"])

    def test_skill_preserves_routing_and_fallback_contract(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        package = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(SKILL_ROOT.rglob("*.md"))
        )
        registry = json.loads(
            (SKILL_ROOT / "references/model-registry.json").read_text(encoding="utf-8")
        )
        for model in (item["id"] for item in registry["models"]):
            self.assertIn(model, package)
        self.assertIn("spawn_agent", package)
        for surface in contract["execution_surfaces"]:
            self.assertIn(surface, package)
        self.assertIn("禁止", package)
        self.assertIn("projectless", package)
        self.assertIn("reserved slots", package)
        for tool in contract["required_tools"]:
            self.assertIn(tool, package)
        for field in contract["required_thread_audit_fields"]:
            self.assertIn(field, package)

    def test_registry_preserves_automatic_and_manual_boundaries(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        registry = json.loads(
            (SKILL_ROOT / "references/model-registry.json").read_text(encoding="utf-8")
        )
        models = {item["id"]: item for item in registry["models"]}
        self.assertTrue(models["gpt-5.6-luna"]["automatic"])
        self.assertTrue(models["gpt-5.6-sol"]["automatic"])
        self.assertEqual(models["gpt-5.6-terra"]["status"], "opt_in")
        self.assertFalse(models["gpt-5.6-terra"]["automatic"])
        self.assertEqual(models["antigravity/gemini-3.6-flash"]["status"], "manual_only")
        self.assertFalse(models["antigravity/gemini-3.6-flash"]["automatic"])
        self.assertTrue(
            set(contract["forbidden_worker_thinking"])
            <= set(registry["policy"]["forbidden_thinking"])
        )
        audit_schema = json.loads(
            (SKILL_ROOT / "references/audit-schema.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            set(contract["required_thread_audit_fields"])
            <= set(audit_schema["required"])
        )

    def test_dual_surface_support_files_are_self_contained(self) -> None:
        required = (
            "references/native-audit-schema.json",
            "references/native-subagent-lifecycle.md",
            "references/surface-selection-policy.md",
            "scripts/route_policy.py",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((SKILL_ROOT / relative).is_file())

    def run_preflight(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts/model_preflight.py"),
                *args,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_preflight_allows_grok_high_and_rejects_ultra(self) -> None:
        incomplete = self.run_preflight("--model", "xai/grok-4.5", "--thinking", "high")
        self.assertEqual(incomplete.returncode, 3, incomplete.stderr or incomplete.stdout)
        self.assertTrue(json.loads(incomplete.stdout)["registry_eligible"])
        self.assertFalse(json.loads(incomplete.stdout)["route_eligible"])

        allowed = self.run_preflight(
            "--model",
            "xai/grok-4.5",
            "--thinking",
            "high",
            "--runtime-confirmed",
            "--host",
            "test-host",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr or allowed.stdout)
        self.assertTrue(json.loads(allowed.stdout)["route_eligible"])

        forbidden = self.run_preflight("--model", "xai/grok-4.5", "--thinking", "ultra")
        self.assertEqual(forbidden.returncode, 2, forbidden.stderr or forbidden.stdout)
        self.assertFalse(json.loads(forbidden.stdout)["route_eligible"])

    def test_preflight_keeps_blocked_gemini_closed_even_when_explicit(self) -> None:
        implicit = self.run_preflight(
            "--model", "antigravity/gemini-3.6-flash", "--thinking", "medium"
        )
        self.assertEqual(implicit.returncode, 2, implicit.stderr or implicit.stdout)

        explicit = self.run_preflight(
            "--model",
            "antigravity/gemini-3.6-flash",
            "--thinking",
            "medium",
            "--explicit-user-request",
            "--risk-acknowledged",
            "--runtime-confirmed",
            "--host",
            "test-host",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        self.assertEqual(explicit.returncode, 2, explicit.stderr or explicit.stdout)
        payload = json.loads(explicit.stdout)
        self.assertFalse(payload["route_eligible"])
        self.assertIn("cannot be overridden", " ".join(payload["errors"]))

    def test_preflight_enforces_surface_thinking_and_terra_opt_in(self) -> None:
        thread_low = self.run_preflight(
            "--surface",
            "app_thread",
            "--model",
            "gpt-5.6-sol",
            "--thinking",
            "low",
        )
        self.assertEqual(thread_low.returncode, 2, thread_low.stderr or thread_low.stdout)
        self.assertIn("not declared for this model", thread_low.stdout)

        native_low = self.run_preflight(
            "--surface",
            "native_subagent",
            "--model",
            "gpt-5.6-sol",
            "--thinking",
            "low",
            "--runtime-confirmed",
            "--host",
            "test-host",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        self.assertEqual(native_low.returncode, 0, native_low.stderr or native_low.stdout)
        self.assertEqual(json.loads(native_low.stdout)["surface"], "native_subagent")

        missing_host = self.run_preflight(
            "--surface",
            "native_subagent",
            "--model",
            "gpt-5.6-sol",
            "--thinking",
            "low",
            "--runtime-confirmed",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        self.assertEqual(missing_host.returncode, 2, missing_host.stdout)
        self.assertIn("requires --host", missing_host.stdout)

        terra_implicit = self.run_preflight(
            "--surface",
            "native_subagent",
            "--model",
            "gpt-5.6-terra",
            "--thinking",
            "low",
            "--runtime-confirmed",
            "--host",
            "test-host",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        self.assertEqual(terra_implicit.returncode, 3, terra_implicit.stderr or terra_implicit.stdout)
        self.assertFalse(json.loads(terra_implicit.stdout)["route_eligible"])

        terra_explicit = self.run_preflight(
            "--surface",
            "native_subagent",
            "--model",
            "gpt-5.6-terra",
            "--thinking",
            "low",
            "--explicit-user-request",
            "--runtime-confirmed",
            "--host",
            "test-host",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        self.assertEqual(terra_explicit.returncode, 0, terra_explicit.stderr or terra_explicit.stdout)
        self.assertTrue(json.loads(terra_explicit.stdout)["route_eligible"])

    def test_preflight_validates_runtime_catalog(self) -> None:
        catalog = {
            "models": [
                {
                    "slug": "xai/grok-4.5",
                    "supported_reasoning_levels": [{"effort": "medium"}],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            result = self.run_preflight(
                "--model",
                "xai/grok-4.5",
                "--thinking",
                "high",
                "--catalog",
                str(path),
                "--provider-status",
                "allowed",
                "--data-allowed",
            )
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        self.assertIn("runtime catalog rejects", result.stdout)

    def test_preflight_semantic_probe_matches_nonce_without_leaking_body(self) -> None:
        class ProbeHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                match = re.search(r"ROUTE-CANARY-[0-9A-F]+", payload["input"])
                response = {
                    "output": [
                        {
                            "content": [
                                {"type": "output_text", "text": match.group(0) if match else ""}
                            ]
                        }
                    ]
                }
                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = self.run_preflight(
                "--model",
                "xai/grok-4.5",
                "--thinking",
                "high",
                "--probe-url",
                f"http://127.0.0.1:{server.server_port}/v1/responses",
                "--provider-status",
                "allowed",
                "--data-allowed",
            )
            native_without_spawn_evidence = self.run_preflight(
                "--surface",
                "native_subagent",
                "--model",
                "xai/grok-4.5",
                "--thinking",
                "high",
                "--probe-url",
                f"http://127.0.0.1:{server.server_port}/v1/responses",
                "--provider-status",
                "allowed",
                "--data-allowed",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["checks"]["semantic_probe"]["semantic_match"])
        self.assertNotIn("ROUTE-CANARY-", result.stdout)
        self.assertEqual(
            native_without_spawn_evidence.returncode,
            3,
            native_without_spawn_evidence.stderr or native_without_spawn_evidence.stdout,
        )
        self.assertFalse(json.loads(native_without_spawn_evidence.stdout)["route_eligible"])

    def test_preflight_rejects_remote_probe_url_before_credential_lookup(self) -> None:
        result = self.run_preflight(
            "--model",
            "xai/grok-4.5",
            "--thinking",
            "high",
            "--provider-status",
            "allowed",
            "--data-allowed",
            "--probe-url",
            "https://example.com/v1/responses",
            "--auth-env",
            "UNSET_TEST_CREDENTIAL",
        )
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertIn("loopback", payload["checks"]["semantic_probe"]["error"])
        self.assertNotIn("UNSET_TEST_CREDENTIAL", payload["checks"]["semantic_probe"]["error"])

    def test_semantic_probe_blocks_redirects_and_oversized_responses(self) -> None:
        class UnsafeHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/oversized")
                    self.end_headers()
                    return
                body = json.dumps({"output_text": "x" * 70_000}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), UnsafeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        common = (
            "--model",
            "xai/grok-4.5",
            "--thinking",
            "high",
            "--provider-status",
            "allowed",
            "--data-allowed",
        )
        try:
            redirected = self.run_preflight(
                *common,
                "--probe-url",
                f"http://127.0.0.1:{server.server_port}/redirect",
            )
            oversized = self.run_preflight(
                *common,
                "--probe-url",
                f"http://127.0.0.1:{server.server_port}/oversized",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertEqual(redirected.returncode, 2, redirected.stderr or redirected.stdout)
        self.assertIn("redirect", redirected.stdout)
        self.assertEqual(oversized.returncode, 2, oversized.stderr or oversized.stdout)
        self.assertIn("exceeded 65536 bytes", oversized.stdout)

    def run_route_validator(self, plan: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "route-plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts/validate_route_plan.py"),
                    str(path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def live_spawn_evidence(
        self,
        model: str = "gpt-5.6-sol",
        thinking: str = "low",
        **overrides: object,
    ) -> dict[str, object]:
        evidence: dict[str, object] = {
            "kind": "live_spawn_schema",
            "surface": "native_subagent",
            "model": model,
            "thinking": thinking,
            "accepted": True,
            "host": "test-host",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        evidence.update(overrides)
        return evidence

    def native_candidate(
        self,
        model: str = "gpt-5.6-sol",
        thinking: str = "low",
        **overrides: object,
    ) -> dict[str, object]:
        candidate: dict[str, object] = {
            "surface": "native_subagent",
            "model": model,
            "thinking": thinking,
            "runtime_evidence": self.live_spawn_evidence(model, thinking),
        }
        candidate.update(overrides)
        return candidate

    def test_route_plan_validator_enforces_order_provider_and_thinking(self) -> None:
        plan = {
            "task_class": "DEEP_AGENTIC_CODE",
            "minimum_thinking": "high",
            "provider_allowlist": ["xai", "openai"],
            "provider_status": {"xai": "allowed", "openai": "allowed"},
            "data_allowed_providers": ["xai", "openai"],
            "explicit_user_request": False,
            "risk_acknowledged": False,
            "candidates": [
                {"model": "xai/grok-4.5", "thinking": "high"},
                {"model": "gpt-5.6-sol", "thinking": "high"},
            ],
            "max_worker_threads": 2,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        plan["minimum_thinking"] = "xhigh"
        invalid = self.run_route_validator(plan)
        self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
        self.assertIn("falls below minimum_thinking", invalid.stdout)

    def test_route_plan_validator_accepts_one_declared_worker(self) -> None:
        plan = {
            "task_class": "DEEP_AGENTIC_CODE",
            "minimum_thinking": "high",
            "provider_allowlist": ["xai"],
            "provider_status": {"xai": "allowed"},
            "data_allowed_providers": ["xai"],
            "explicit_user_request": True,
            "risk_acknowledged": True,
            "candidates": [{"model": "xai/grok-4.5", "thinking": "high"}],
            "max_worker_threads": 1,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        plan["max_worker_threads"] = 2
        mismatch = self.run_route_validator(plan)
        self.assertEqual(mismatch.returncode, 2, mismatch.stderr or mismatch.stdout)
        self.assertIn("must match the declared candidate count", mismatch.stdout)

    def test_route_plan_validator_accepts_explicit_sol_medium(self) -> None:
        plan = {
            "task_class": "EXPLICIT_DURABLE_GENERAL",
            "minimum_thinking": "medium",
            "provider_allowlist": ["openai"],
            "provider_status": {"openai": "allowed"},
            "data_allowed_providers": ["openai"],
            "explicit_user_request": True,
            "risk_acknowledged": True,
            "candidates": [{"model": "gpt-5.6-sol", "thinking": "medium"}],
            "max_worker_threads": 1,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

    def test_route_plan_validator_accepts_native_sol_low_with_live_evidence(self) -> None:
        plan = {
            "task_class": "NATIVE_SCOUT",
            "minimum_thinking": "low",
            "provider_allowlist": ["openai"],
            "provider_status": {"openai": "allowed"},
            "data_allowed_providers": ["openai"],
            "explicit_user_request": False,
            "risk_acknowledged": False,
            "candidates": [self.native_candidate()],
            "max_worker_threads": 1,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        plan["candidates"][0].pop("runtime_evidence")
        missing_live_evidence = self.run_route_validator(plan)
        self.assertEqual(
            missing_live_evidence.returncode,
            2,
            missing_live_evidence.stderr or missing_live_evidence.stdout,
        )
        self.assertIn("requires tuple-bound live runtime evidence", missing_live_evidence.stdout)

    def test_route_plan_validator_supports_predeclared_cross_surface_fallback(self) -> None:
        plan = {
            "task_class": "DEFAULT_GENERAL",
            "minimum_thinking": "medium",
            "provider_allowlist": ["openai"],
            "provider_status": {"openai": "allowed"},
            "data_allowed_providers": ["openai"],
            "explicit_user_request": True,
            "risk_acknowledged": False,
            "candidates": [
                self.native_candidate(thinking="medium"),
                {
                    "surface": "app_thread",
                    "model": "gpt-5.6-sol",
                    "thinking": "medium",
                },
            ],
            "max_worker_threads": 2,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        plan["candidates"][0]["surface"] = "unknown_surface"
        invalid_surface = self.run_route_validator(plan)
        self.assertEqual(invalid_surface.returncode, 2, invalid_surface.stderr or invalid_surface.stdout)
        self.assertIn("unknown execution surface", invalid_surface.stdout)

    def test_route_plan_validator_defaults_legacy_candidates_to_app_thread(self) -> None:
        plan = {
            "task_class": "DEFAULT_GENERAL",
            "minimum_thinking": "high",
            "provider_allowlist": ["openai"],
            "provider_status": {"openai": "allowed"},
            "data_allowed_providers": ["openai"],
            "explicit_user_request": False,
            "risk_acknowledged": False,
            "candidates": [{"model": "gpt-5.6-sol", "thinking": "high"}],
            "max_worker_threads": 1,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)
        self.assertIn('"surface": "app_thread"', valid.stdout)

    def test_route_plan_validator_keeps_terra_explicit_and_first(self) -> None:
        plan = {
            "task_class": "TERRA_EXPLICIT",
            "minimum_thinking": "low",
            "provider_allowlist": ["openai"],
            "provider_status": {"openai": "allowed"},
            "data_allowed_providers": ["openai"],
            "explicit_user_request": True,
            "risk_acknowledged": False,
            "candidates": [
                self.native_candidate(model="gpt-5.6-terra"),
                self.native_candidate(),
            ],
            "max_worker_threads": 2,
            "max_followups_per_thread": 1,
        }
        valid = self.run_route_validator(plan)
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        plan["explicit_user_request"] = False
        implicit = self.run_route_validator(plan)
        self.assertEqual(implicit.returncode, 2, implicit.stderr or implicit.stdout)
        self.assertIn("requires explicit_user_request", implicit.stdout)

        plan["explicit_user_request"] = True
        plan["candidates"].reverse()
        fallback = self.run_route_validator(plan)
        self.assertEqual(fallback.returncode, 2, fallback.stderr or fallback.stdout)
        self.assertIn("cannot be a fallback candidate", fallback.stdout)

    def test_route_plan_rejects_non_boolean_authorization_and_bad_runtime_evidence(self) -> None:
        plan = {
            "task_class": "TERRA_EXPLICIT",
            "minimum_thinking": "low",
            "provider_allowlist": ["openai"],
            "provider_status": {"openai": "allowed"},
            "data_allowed_providers": ["openai"],
            "explicit_user_request": "false",
            "risk_acknowledged": False,
            "candidates": [self.native_candidate(model="gpt-5.6-terra")],
            "max_worker_threads": 1,
            "max_followups_per_thread": 1,
        }
        invalid_boolean = self.run_route_validator(plan)
        self.assertEqual(invalid_boolean.returncode, 2, invalid_boolean.stdout)
        self.assertIn("explicit_user_request must be a boolean", invalid_boolean.stdout)

        plan["explicit_user_request"] = True
        plan["candidates"] = [
            self.native_candidate(
                model="gpt-5.6-terra",
                runtime_evidence=self.live_spawn_evidence(model="gpt-5.6-sol"),
            )
        ]
        mismatched = self.run_route_validator(plan)
        self.assertEqual(mismatched.returncode, 2, mismatched.stdout)
        self.assertIn("runtime evidence does not match", mismatched.stdout)

        stale_at = (datetime.now(timezone.utc) - timedelta(minutes=11)).isoformat()
        plan["candidates"] = [
            self.native_candidate(
                model="gpt-5.6-terra",
                runtime_evidence=self.live_spawn_evidence(
                    model="gpt-5.6-terra", checked_at=stale_at
                ),
            )
        ]
        stale = self.run_route_validator(plan)
        self.assertEqual(stale.returncode, 2, stale.stdout)
        self.assertIn("runtime evidence is stale", stale.stdout)

    def test_lifecycle_defines_data_ready_without_claiming_model_identity(self) -> None:
        lifecycle = (SKILL_ROOT / "references/thread-lifecycle.md").read_text(encoding="utf-8")
        self.assertIn("assistant-originated", lifecycle)
        self.assertIn("observed_runtime_model", lifecycle)
        self.assertIn("list_threads", lifecycle)

    def test_supervision_protocol_handles_pending_unknown_and_resume(self) -> None:
        protocol = (SKILL_ROOT / "references/thread-supervision-protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("pendingWorktreeId", protocol)
        self.assertIn("list_threads(query=task_id)", protocol)
        self.assertIn("两次连续官方观察", protocol)
        self.assertIn("UNKNOWN` 禁止 follow-up、归档、fallback 和重复创建", protocol)
        self.assertIn("最新成功", protocol)
        self.assertLess(protocol.index("读取上游账本"), protocol.index("才沿原 RoutePlan"))

    def run_ledger_validator(self, payload: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "team-ledger.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts/validate_team_ledger.py"),
                    str(path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def ledger_record(self, **overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "creation_attempt": 1,
            "subtask_attempt": 1,
            "task_id": "task-alpha-a1",
            "thread_id": "thread-alpha",
            "pending_worktree_id": None,
            "control_state": "COMPLETED",
            "thread_status": "idle",
            "turn_status": "completed",
            "last_observed_at": "2026-07-25T00:00:00+08:00",
            "role": "reviewer",
            "model": "gpt-5.6-sol",
            "requested_model": "gpt-5.6-sol",
            "platform_accepted_model": "gpt-5.6-sol",
            "observed_runtime_model": "unknown",
            "thinking": "xhigh",
            "route_plan": {},
            "provider_policy": {},
            "materialized": True,
            "data_ready": True,
            "status": "completed",
            "output": "reports/review.md",
            "adopted": True,
            "fallback_reason": None,
            "archived": True,
        }
        record.update(overrides)
        return record

    def native_ledger_record(self, **overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "worker_attempt": 2,
            "subtask_attempt": 1,
            "task_id": "task-native-a1",
            "surface": "native_subagent",
            "agent_id": "agent-native",
            "control_state": "CLOSED",
            "agent_status": "completed",
            "last_observed_at": "2026-07-27T00:00:00+08:00",
            "fork_mode": "fresh",
            "role": "scout",
            "model": "gpt-5.6-sol",
            "requested_model": "gpt-5.6-sol",
            "platform_accepted_model": "gpt-5.6-sol",
            "observed_runtime_model": "unknown",
            "thinking": "low",
            "route_plan": {},
            "provider_policy": {},
            "status": "completed",
            "output": "CODEX_SOL_CHILD_OK",
            "adopted": True,
            "fallback_reason": None,
            "closed": True,
        }
        record.update(overrides)
        return record

    def test_ledger_validator_accepts_completed_and_pending_records(self) -> None:
        completed = self.ledger_record()
        pending = self.ledger_record(
            creation_attempt=2,
            task_id="task-beta-a1",
            thread_id=None,
            pending_worktree_id="pending-beta",
            control_state="CREATION_PENDING",
            thread_status=None,
            turn_status=None,
            last_observed_at=None,
            materialized=False,
            data_ready=False,
            status="creation_pending",
            output=None,
            adopted=False,
            archived=False,
        )
        result = self.run_ledger_validator(
            {"creation_attempts": 2, "workers": [completed, pending]}
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ledger_valid"])
        self.assertEqual(payload["in_flight_count"], 1)

    def test_ledger_validator_rejects_unknown_archive_and_pending_as_thread(self) -> None:
        invalid = self.ledger_record(
            thread_id="pending-same",
            pending_worktree_id="pending-same",
            control_state="UNKNOWN",
        )
        result = self.run_ledger_validator([invalid])
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        self.assertIn("pending id as a formal thread id", result.stdout)
        self.assertIn("cannot archive UNKNOWN", result.stdout)

    def test_ledger_validator_uses_official_state_not_legacy_status(self) -> None:
        active = self.ledger_record(
            control_state="DATA_READY",
            thread_status="active",
            turn_status="inProgress",
            status="done",
            output=None,
            adopted=False,
            archived=False,
        )
        result = self.run_ledger_validator([active])
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_ledger_validator_rejects_inspect_source_mutation(self) -> None:
        inspect = self.ledger_record(
            task_intent="inspect",
            mutation_authority="declared-workspace",
        )
        result = self.run_ledger_validator([inspect])
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        self.assertIn("grants source mutation to inspect", result.stdout)

    def test_ledger_validator_accepts_mixed_thread_and_native_records(self) -> None:
        thread_record = self.ledger_record(archived=False)
        native_record = self.native_ledger_record()
        result = self.run_ledger_validator(
            {
                "worker_attempts": 2,
                "creation_attempts": 1,
                "workers": [thread_record, native_record],
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ledger_valid"])

    def test_thread_ledger_requires_compatible_attempt_fields_to_match(self) -> None:
        matching = self.ledger_record(worker_attempt=1)
        valid = self.run_ledger_validator([matching])
        self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        mismatched = self.ledger_record(worker_attempt=2)
        invalid = self.run_ledger_validator([mismatched])
        self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
        self.assertIn("worker_attempt must equal creation_attempt", invalid.stdout)

    def test_native_ledger_requires_close_gate_for_adopted_output(self) -> None:
        native_record = self.native_ledger_record(control_state="COMPLETED", closed=False)
        result = self.run_ledger_validator([native_record])
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        self.assertIn("adopted native output must be closed", result.stdout)

    def test_native_ledger_rejects_inherited_or_mismatched_route_identity(self) -> None:
        for override, message in (
            ({"fork_mode": "inherited"}, "must use fresh context"),
            ({"platform_accepted_model": "gpt-5.6-terra"}, "accepted model mismatch"),
            ({"observed_runtime_model": "gpt-5.6-terra"}, "observed model mismatch"),
        ):
            with self.subTest(override=override):
                result = self.run_ledger_validator(
                    [self.native_ledger_record(**override)]
                )
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(message, result.stdout)

    def test_completed_unclosed_native_agents_still_consume_concurrency(self) -> None:
        records = []
        for attempt in range(1, 8):
            records.append(
                self.native_ledger_record(
                    worker_attempt=attempt,
                    task_id=f"native-{attempt}",
                    agent_id=f"agent-{attempt}",
                    control_state="COMPLETED" if attempt < 7 else "RUNNING",
                    closed=False,
                    adopted=False,
                    output=None,
                )
            )
        result = self.run_ledger_validator(records)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("in-flight records exceed the concurrency cap", result.stdout)

    def test_native_policy_maps_v1_v2_fresh_context_without_silent_inheritance(self) -> None:
        policy = (SKILL_ROOT / "references/native-subagent-lifecycle.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("fork_context=false", policy)
        self.assertIn('fork_turns="none"', policy)
        self.assertIn("禁止静默继承父模型", policy)
        self.assertIn("observed_runtime_model", policy)

    def test_adapter_keeps_verifier_before_reviewer(self) -> None:
        adapter = (SKILL_ROOT / "references/upstream-skill-adapter.md").read_text(encoding="utf-8")
        self.assertLess(adapter.index("verifier：1 个"), adapter.index("reviewer：1 个"))
        self.assertIn("每次调用 `create_thread` 前", adapter)
        self.assertIn("返回正式 id 或 pending id 后写入对应字段", adapter)


if __name__ == "__main__":
    unittest.main()
