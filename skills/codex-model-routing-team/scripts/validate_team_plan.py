#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


CURRENT_SCHEMA_VERSION = "1.0"
MAX_PLANNED_WORKERS = 6
MAX_WORKER_ATTEMPTS = 8
MAX_NEW_WORKERS_PER_WAVE = 3
PLANNING_SOURCES = {"ad_hoc", "codex_plan", "ce_plan", "upstream_skill"}
ROLES = {"researcher", "implementer", "verifier", "reviewer", "custom"}
UNIT_ID_PATTERN = re.compile(r"^U[1-9][0-9]*$")
GLOB_CHARS = set("*?[]{}")


def load_input(source: str) -> Any:
    if source == "-":
        return json.load(sys.stdin)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


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


def validate_team_plan_payload(payload: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "fail",
        "team_plan_valid": False,
        "schema_version": None,
        "revision": None,
        "worker_count": 0,
        "dispatch_waves": [],
        "errors": [],
        "warnings": [],
    }
    errors: list[str] = result["errors"]

    if not isinstance(payload, dict):
        errors.append("TeamPlan must be a JSON object")
        return result

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
    if not 2 <= len(units) <= MAX_PLANNED_WORKERS:
        errors.append("TeamPlan must contain between 2 and 6 Worker units")

    reserved_slots = payload.get("reserved_slots")
    if not valid_int(reserved_slots):
        errors.append("reserved_slots must be a non-negative integer")
    elif len(units) + reserved_slots > MAX_WORKER_ATTEMPTS:
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
            for start in range(0, len(layer), MAX_NEW_WORKERS_PER_WAVE):
                result["dispatch_waves"].append(
                    layer[start : start + MAX_NEW_WORKERS_PER_WAVE]
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_input(args.plan)
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "status": "fail",
            "team_plan_valid": False,
            "errors": [f"JSON load failed: {exc}"],
            "warnings": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    result = validate_team_plan_payload(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["team_plan_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
