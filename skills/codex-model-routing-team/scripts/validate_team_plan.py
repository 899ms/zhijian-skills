#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


CURRENT_SCHEMA_VERSION = "1.0"
SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = SKILL_ROOT / "references" / "model-registry.json"
FALLBACK_LIMIT_PROFILE = {
    "max_planned_workers": 6,
    "max_worker_attempts": 8,
    "max_new_workers_per_wave": 3,
    "min_reserved_slots": 0,
}
PLANNING_SOURCES = {"ad_hoc", "codex_plan", "ce_plan", "upstream_skill"}
ROLES = {"researcher", "implementer", "verifier", "reviewer", "custom"}
UNIT_ID_PATTERN = re.compile(r"^U[1-9][0-9]*$")
GLOB_CHARS = set("*?[]{}")


def load_input(source: str) -> Any:
    if source == "-":
        return json.load(sys.stdin)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def load_registry(path: Path = DEFAULT_REGISTRY) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def parse_timestamp(value: Any) -> datetime | None:
    if not nonempty_string(value):
        return None
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def normalize_scope_path(value: Any) -> tuple[str | None, str | None]:
    if not nonempty_string(value):
        return None, "must be a non-empty string"
    candidate = value.strip()
    if "\\" in candidate:
        return None, "must use forward slashes"
    if any(char in candidate for char in GLOB_CHARS):
        return None, "must not contain glob syntax"
    path = PurePosixPath(candidate)
    if path.is_absolute() or candidate == "." or ".." in path.parts:
        return None, "must be a safe relative path"
    normalized = path.as_posix().rstrip("/")
    if not normalized:
        return None, "must be a safe relative path"
    return normalized, None


def paths_overlap(left: str, right: str) -> bool:
    left_parts = PurePosixPath(left).parts
    right_parts = PurePosixPath(right).parts
    shorter = min(len(left_parts), len(right_parts))
    return left_parts[:shorter] == right_parts[:shorter]


def validate_team_plan_payload(
    payload: Any, registry: dict[str, Any] | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "fail",
        "team_plan_valid": False,
        "schema_version": None,
        "revision": None,
        "worker_count": 0,
        "scale_profile": None,
        "limits": {},
        "dispatch_waves": [],
        "errors": [],
        "warnings": [],
    }
    errors: list[str] = result["errors"]

    if not isinstance(payload, dict):
        errors.append("TeamPlan must be a JSON object")
        return result

    if registry is None:
        try:
            loaded_registry = load_registry()
        except (OSError, json.JSONDecodeError):
            loaded_registry = {}
        registry = loaded_registry if isinstance(loaded_registry, dict) else {}
    policy = registry.get("policy", {}) if isinstance(registry, dict) else {}
    profiles = policy.get("team_limit_profiles", {})
    default_profile = policy.get("default_team_limit_profile", "standard")
    scale_profile = payload.get("scale_profile", default_profile)
    result["scale_profile"] = scale_profile
    limits = profiles.get(scale_profile) if isinstance(profiles, dict) else None
    if not isinstance(limits, dict):
        if scale_profile == "standard":
            limits = dict(FALLBACK_LIMIT_PROFILE)
        else:
            errors.append("scale_profile is not declared in registry policy")
            limits = dict(FALLBACK_LIMIT_PROFILE)
    required_limits = (
        "max_planned_workers",
        "max_worker_attempts",
        "max_new_workers_per_wave",
        "min_reserved_slots",
    )
    if not (
        all(valid_int(limits.get(field), minimum=1) for field in required_limits[:3])
        and valid_int(limits.get("min_reserved_slots"))
    ):
        errors.append("scale_profile limits are invalid")
        limits = dict(FALLBACK_LIMIT_PROFILE)
    result["limits"] = {field: limits[field] for field in required_limits}
    if scale_profile != default_profile and not nonempty_string(
        payload.get("scale_reason")
    ):
        errors.append("non-default scale_profile requires scale_reason")
    runtime_worker_capacity = payload.get("runtime_worker_capacity")
    if runtime_worker_capacity is not None and not valid_int(
        runtime_worker_capacity, minimum=1
    ):
        errors.append("runtime_worker_capacity must be a positive integer")
        runtime_worker_capacity = None
    if scale_profile != default_profile and runtime_worker_capacity is None:
        errors.append("non-default scale_profile requires runtime_worker_capacity")
    capacity_policy = policy.get("native_capacity_policy", {})
    capacity_evidence = payload.get("runtime_capacity_evidence")
    if runtime_worker_capacity is not None and not isinstance(capacity_evidence, dict):
        errors.append("runtime_worker_capacity requires runtime_capacity_evidence")
    if isinstance(capacity_evidence, dict):
        evidence_kind = capacity_evidence.get("kind")
        if evidence_kind not in {"live_tool_contract", "live_collaboration_status"}:
            errors.append("runtime_capacity_evidence has unsupported kind")
        if not nonempty_string(capacity_evidence.get("host")):
            errors.append("runtime_capacity_evidence requires host")
        captured_at = parse_timestamp(capacity_evidence.get("captured_at"))
        if captured_at is None:
            errors.append("runtime_capacity_evidence requires a timezone-aware captured_at")
        else:
            ttl_seconds = (
                capacity_policy.get("capacity_evidence_ttl_seconds", 600)
                if isinstance(capacity_policy, dict)
                else 600
            )
            if not valid_int(ttl_seconds, minimum=1):
                ttl_seconds = 600
            age_seconds = (datetime.now(timezone.utc) - captured_at).total_seconds()
            if age_seconds < -60 or age_seconds > ttl_seconds:
                errors.append("runtime_capacity_evidence is stale or from the future")
        total_slots = capacity_evidence.get("total_concurrency_slots")
        coordinator_slots = capacity_evidence.get("coordinator_slots")
        active_worker_slots = capacity_evidence.get("active_worker_slots")
        available_child_slots = capacity_evidence.get("available_child_slots")
        if not valid_int(total_slots, minimum=1):
            errors.append("runtime_capacity_evidence has invalid total_concurrency_slots")
        if not valid_int(coordinator_slots):
            errors.append("runtime_capacity_evidence has invalid coordinator_slots")
        if not valid_int(active_worker_slots):
            errors.append("runtime_capacity_evidence has invalid active_worker_slots")
        if not valid_int(available_child_slots, minimum=1):
            errors.append("runtime_capacity_evidence has invalid available_child_slots")
        if all(
            valid_int(value)
            for value in (total_slots, coordinator_slots, active_worker_slots)
        ):
            computed_available = total_slots - coordinator_slots - active_worker_slots
            if computed_available < 1 or available_child_slots != computed_available:
                errors.append("runtime_capacity_evidence slot arithmetic does not balance")
        if runtime_worker_capacity is not None and available_child_slots != runtime_worker_capacity:
            errors.append("runtime_worker_capacity does not match live capacity evidence")
        reserve_coordinator = (
            capacity_policy.get("reserve_coordinator_slot", True)
            if isinstance(capacity_policy, dict)
            else True
        )
        if reserve_coordinator and not valid_int(coordinator_slots, minimum=1):
            errors.append("runtime_capacity_evidence must reserve a coordinator slot")
    unknown_capacity = (
        capacity_policy.get("default_child_capacity_when_unknown", 3)
        if isinstance(capacity_policy, dict)
        else 3
    )
    if not valid_int(unknown_capacity, minimum=1):
        unknown_capacity = 3
    conservative_capacity = min(
        limits["max_new_workers_per_wave"],
        runtime_worker_capacity
        if isinstance(runtime_worker_capacity, int)
        else unknown_capacity,
    )
    result["runtime_worker_capacity"] = runtime_worker_capacity
    result["runtime_capacity_evidence"] = capacity_evidence
    result["effective_worker_capacity"] = conservative_capacity

    schema_version = payload.get("schema_version")
    revision = payload.get("revision")
    result["schema_version"] = schema_version
    result["revision"] = revision
    if schema_version != CURRENT_SCHEMA_VERSION:
        errors.append("unsupported TeamPlan schema_version")
    if not valid_int(revision, minimum=1):
        errors.append("revision must be a positive integer")
    else:
        supersedes = payload.get("supersedes_revision")
        if revision == 1 and supersedes is not None:
            errors.append("revision 1 must not supersede another revision")
        if revision > 1 and supersedes != revision - 1:
            errors.append("supersedes_revision must name the direct previous revision")

    source = payload.get("planning_source")
    source_refs = payload.get("source_refs")
    if source not in PLANNING_SOURCES:
        errors.append("planning_source is not supported")
    if not isinstance(source_refs, list) or not all(
        nonempty_string(item) for item in source_refs
    ):
        errors.append("source_refs must be an array of non-empty strings")
    elif source != "ad_hoc" and not source_refs:
        errors.append("non-ad_hoc TeamPlan requires source_refs")

    if not nonempty_string(payload.get("root_goal")):
        errors.append("root_goal must be a non-empty string")
    if not nonempty_string(payload.get("revision_reason")):
        errors.append("revision_reason must be a non-empty string")
    if payload.get("integration_owner") != "lead":
        errors.append("integration_owner must remain lead")
    if not nonempty_string(payload.get("final_verification")):
        errors.append("final_verification must be a non-empty string")

    units = payload.get("units")
    if not isinstance(units, list):
        errors.append("units must be an array")
        return result
    result["worker_count"] = len(units)
    max_planned_workers = limits["max_planned_workers"]
    max_worker_attempts = limits["max_worker_attempts"]
    max_new_workers_per_wave = limits["max_new_workers_per_wave"]
    min_reserved_slots = limits["min_reserved_slots"]
    if not 2 <= len(units) <= max_planned_workers:
        errors.append(
            f"TeamPlan must contain between 2 and {max_planned_workers} Worker units"
        )

    reserved_slots = payload.get("reserved_slots")
    if not valid_int(reserved_slots):
        errors.append("reserved_slots must be a non-negative integer")
    else:
        if reserved_slots < min_reserved_slots:
            errors.append(
                f"scale_profile requires at least {min_reserved_slots} reserved_slots"
            )
        if len(units) + reserved_slots > max_worker_attempts:
            errors.append("planned Workers plus reserved_slots exceed the attempt cap")

    unit_order: list[str] = []
    units_by_id: dict[str, dict[str, Any]] = {}
    dependencies: dict[str, list[str]] = {}
    write_scopes: dict[str, list[str]] = {}

    for index, unit in enumerate(units):
        prefix = f"unit {index}"
        if not isinstance(unit, dict):
            errors.append(f"{prefix} must be an object")
            continue
        unit_id = unit.get("unit_id")
        if not nonempty_string(unit_id) or UNIT_ID_PATTERN.fullmatch(unit_id) is None:
            errors.append(f"{prefix} has invalid unit_id")
            continue
        if unit_id in units_by_id:
            errors.append(f"{prefix} duplicates unit_id {unit_id}")
            continue
        unit_order.append(unit_id)
        units_by_id[unit_id] = unit

        if unit.get("role") not in ROLES:
            errors.append(f"{unit_id} has unsupported role")
        for field in ("goal", "output", "done_when"):
            if not nonempty_string(unit.get(field)):
                errors.append(f"{unit_id} has invalid {field}")

        depends_on = unit.get("depends_on")
        if not isinstance(depends_on, list) or not all(
            nonempty_string(item) for item in depends_on
        ):
            errors.append(f"{unit_id} depends_on must contain unit IDs")
            dependencies[unit_id] = []
        else:
            if len(depends_on) != len(set(depends_on)):
                errors.append(f"{unit_id} duplicates dependencies")
            if unit_id in depends_on:
                errors.append(f"{unit_id} cannot depend on itself")
            dependencies[unit_id] = list(depends_on)

        ownership = unit.get("ownership")
        if not isinstance(ownership, dict):
            errors.append(f"{unit_id} ownership must be an object")
            write_scopes[unit_id] = []
            continue
        normalized_scopes: dict[str, list[str]] = {"write": [], "forbidden": []}
        for field in ("write", "forbidden"):
            values = ownership.get(field)
            if not isinstance(values, list):
                errors.append(f"{unit_id} ownership.{field} must be an array")
                continue
            for value in values:
                normalized, error = normalize_scope_path(value)
                if error is not None:
                    errors.append(f"{unit_id} ownership.{field} {error}")
                elif normalized is not None:
                    normalized_scopes[field].append(normalized)
            if len(normalized_scopes[field]) != len(set(normalized_scopes[field])):
                errors.append(f"{unit_id} ownership.{field} contains duplicates")
        write_scopes[unit_id] = normalized_scopes["write"]
        for write_path in normalized_scopes["write"]:
            for forbidden_path in normalized_scopes["forbidden"]:
                if paths_overlap(write_path, forbidden_path):
                    errors.append(
                        f"{unit_id} write scope overlaps its forbidden scope"
                    )

    if len(units_by_id) == len(units):
        for unit_id, deps in dependencies.items():
            for dependency in deps:
                if dependency not in units_by_id:
                    errors.append(f"{unit_id} depends on unknown unit {dependency}")

        remaining = set(unit_order)
        completed: set[str] = set()
        layers: list[list[str]] = []
        while remaining:
            ready = [
                unit_id
                for unit_id in unit_order
                if unit_id in remaining
                and set(dependencies.get(unit_id, [])) <= completed
            ]
            if not ready:
                errors.append("TeamPlan dependency graph contains a cycle")
                break
            layers.append(ready)
            completed.update(ready)
            remaining.difference_update(ready)

        for layer in layers:
            for left_index, left_id in enumerate(layer):
                for right_id in layer[left_index + 1 :]:
                    for left_path in write_scopes.get(left_id, []):
                        for right_path in write_scopes.get(right_id, []):
                            if paths_overlap(left_path, right_path):
                                errors.append(
                                    f"ready units {left_id} and {right_id} have overlapping write scope"
                                )
            for start in range(0, len(layer), conservative_capacity):
                result["dispatch_waves"].append(
                    layer[start : start + conservative_capacity]
                )

        integration_order = payload.get("integration_order")
        if not isinstance(integration_order, list) or not all(
            nonempty_string(item) for item in integration_order
        ):
            errors.append("integration_order must contain unit IDs")
        elif len(integration_order) != len(set(integration_order)):
            errors.append("integration_order contains duplicates")
        elif set(integration_order) != set(unit_order):
            errors.append("integration_order must cover every Worker unit exactly once")
        else:
            positions = {unit_id: index for index, unit_id in enumerate(integration_order)}
            for unit_id, deps in dependencies.items():
                for dependency in deps:
                    if dependency in positions and positions[dependency] > positions[unit_id]:
                        errors.append("integration_order violates dependency order")

    if not errors:
        result["status"] = "pass"
        result["team_plan_valid"] = True
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a lightweight TeamPlan before multi-Worker dispatch."
    )
    parser.add_argument("plan", help="TeamPlan JSON path, or - to read JSON from stdin")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_input(args.plan)
        registry = load_registry(args.registry)
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "status": "fail",
            "team_plan_valid": False,
            "errors": [f"JSON load failed: {exc}"],
            "warnings": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    result = validate_team_plan_payload(payload, registry)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["team_plan_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
