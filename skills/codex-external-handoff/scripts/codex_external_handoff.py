#!/usr/bin/env python3
"""Create and supervise persistent Codex App Server threads from external agents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {"completed", "failed", "cancelled", "timed_out"}
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Public deterministic CLI used by WorkBuddy and other local Agent hosts."
DEFAULT_MODEL = "gpt-5.6-sol"
DEFAULT_EFFORT = "high"
DEFAULT_TURN_TIMEOUT = 7200
CLIENT_INFO = {
    "name": "workbuddy_codex_external_handoff",
    "title": "WorkBuddy Codex External Handoff",
    "version": "1.0.0",
}

RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["completed", "blocked", "needs_input"],
        },
        "conclusion": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "finding": {"type": "string"},
                },
                "required": ["source", "finding"],
                "additionalProperties": False,
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}},
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["path", "description"],
                "additionalProperties": False,
            },
        },
        "recommended_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "suggested_state_delta": {"type": "string"},
    },
    "required": [
        "status",
        "conclusion",
        "evidence",
        "risks",
        "artifacts",
        "recommended_actions",
        "suggested_state_delta",
    ],
    "additionalProperties": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def state_home() -> Path:
    explicit = os.environ.get("CODEX_EXTERNAL_HANDOFF_HOME")
    if explicit:
        return Path(explicit).expanduser().resolve()
    codex_root = os.environ.get("CODEX_HOME")
    if codex_root:
        return Path(codex_root).expanduser().resolve() / "external-handoff"
    return Path.home() / ".codex" / "external-handoff"


def jobs_dir() -> Path:
    path = state_home() / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def job_path(job_id: str) -> Path:
    return jobs_dir() / f"{job_id}.json"


def request_path(job_id: str) -> Path:
    return jobs_dir() / f"{job_id}.request.json"


def log_path(job_id: str) -> Path:
    path = state_home() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{job_id}.log"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def update_job(job_id: str, **changes: Any) -> dict[str, Any]:
    path = job_path(job_id)
    state = read_json(path)
    state.update(changes)
    state["updated_at"] = now_iso()
    atomic_write_json(path, state)
    return state


def iter_jobs() -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for path in jobs_dir().glob("*.json"):
        if path.name.endswith(".request.json"):
            continue
        try:
            found.append(read_json(path))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(found, key=lambda item: item.get("updated_at", ""), reverse=True)


def resolve_job(identifier: str | None, cwd: str | None = None) -> dict[str, Any]:
    if identifier:
        direct = job_path(identifier)
        if direct.exists():
            return read_json(direct)
        matches = [item for item in iter_jobs() if item.get("thread_id") == identifier]
        if matches:
            return matches[0]
        raise SystemExit(f"找不到任务或 Thread：{identifier}")

    current = str(Path(cwd or os.getcwd()).resolve())
    matches = [item for item in iter_jobs() if item.get("cwd") == current]
    if not matches:
        raise SystemExit(f"当前目录没有 Codex 外援任务：{current}")
    return matches[0]


def is_process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def public_state(state: dict[str, Any]) -> dict[str, Any]:
    result = dict(state)
    if result.get("status") not in TERMINAL_STATUSES:
        result["worker_alive"] = is_process_alive(result.get("worker_pid"))
    result.pop("app_server_pid", None)
    return result


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def task_text(args: argparse.Namespace) -> str:
    if bool(args.task) == bool(args.task_file):
        raise SystemExit("必须且只能提供 --task 或 --task-file 之一")
    if args.task:
        text = args.task
    else:
        source = Path(args.task_file).expanduser().resolve()
        if not source.is_file():
            raise SystemExit(f"任务文件不存在：{source}")
        text = source.read_text(encoding="utf-8")
    if not text.strip():
        raise SystemExit("任务内容不能为空")
    return text.strip()


def normalize_cwd(value: str) -> str:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"工作目录不存在：{path}")
    return str(path)


class AppServerClient:
    def __init__(self, cwd: str, log_file: Any):
        self._next_id = 1
        self._messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self._pending: list[dict[str, Any]] = []
        self._log_file = log_file
        self.proc = subprocess.Popen(
            ["codex", "app-server"],
            cwd=cwd,
            env=os.environ.copy(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log_file,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            raw = line.strip()
            if not raw:
                continue
            try:
                self._messages.put(json.loads(raw))
            except json.JSONDecodeError:
                self._log_file.write(f"non-json stdout: {raw}\n")
                self._log_file.flush()

    def send(self, message: dict[str, Any]) -> None:
        if self.proc.poll() is not None:
            raise RuntimeError(f"codex app-server 已退出，exit={self.proc.returncode}")
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any], timeout: float = 60) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self.send({"method": method, "id": request_id, "params": params})
        deadline = time.monotonic() + timeout
        postponed = self._pending
        self._pending = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._pending.extend(postponed)
                raise TimeoutError(f"App Server 请求超时：{method}")
            try:
                message = self._messages.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                if self.proc.poll() is not None:
                    self._pending.extend(postponed)
                    raise RuntimeError(
                        f"codex app-server 意外退出，exit={self.proc.returncode}"
                    )
                continue
            if message.get("id") == request_id and "method" not in message:
                self._pending.extend(postponed)
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            postponed.append(message)

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self.send({"method": method, "params": params})

    def next_message(self, timeout: float = 1.0) -> dict[str, Any] | None:
        if self._pending:
            return self._pending.pop(0)
        try:
            return self._messages.get(timeout=timeout)
        except queue.Empty:
            if self.proc.poll() is not None:
                raise RuntimeError(f"codex app-server 意外退出，exit={self.proc.returncode}")
            return None

    def reject_server_request(self, message: dict[str, Any]) -> None:
        if "id" not in message or "method" not in message:
            return
        self.send(
            {
                "id": message["id"],
                "error": {
                    "code": -32601,
                    "message": "External handoff is non-interactive; return needs_input instead.",
                },
            }
        )

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)


def initialize_client(client: AppServerClient) -> dict[str, Any]:
    initialized = client.request("initialize", {"clientInfo": CLIENT_INFO})
    client.notify("initialized", {})
    return initialized


def extract_agent_text(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    if item.get("type") != "agentMessage":
        return None
    text = item.get("text")
    if isinstance(text, str):
        return text
    content = item.get("content")
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        ]
        return "".join(parts) or None
    return None


def parse_structured_result(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidate = "\n".join(lines[1:-1])
            if candidate.lstrip().startswith("json"):
                candidate = candidate.lstrip()[4:].lstrip("\n")
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def worker_main(job_id: str) -> int:
    state = read_json(job_path(job_id))
    request_file = request_path(job_id)
    request = read_json(request_file)
    try:
        request_file.unlink()
    except FileNotFoundError:
        pass

    cancelled = False

    def mark_cancelled(_signum: int, _frame: Any) -> None:
        nonlocal cancelled
        cancelled = True

    signal.signal(signal.SIGTERM, mark_cancelled)
    signal.signal(signal.SIGINT, mark_cancelled)

    client: AppServerClient | None = None
    turn_id: str | None = None
    timed_out = False
    final_text = ""
    delta_parts: list[str] = []
    log_file_path = log_path(job_id)

    update_job(job_id, status="starting", worker_pid=os.getpid(), started_at=now_iso())
    with log_file_path.open("a", encoding="utf-8") as log_file:
        try:
            client = AppServerClient(state["cwd"], log_file)
            update_job(job_id, app_server_pid=client.proc.pid)
            initialize_client(client)

            common = {
                "model": state["model"],
                "cwd": state["cwd"],
                "approvalPolicy": state["approval_policy"],
                "sandbox": state["sandbox"],
            }
            if request["action"] == "ask":
                started = client.request(
                    "thread/start",
                    {
                        **common,
                        "ephemeral": False,
                        "serviceName": CLIENT_INFO["name"],
                    },
                    timeout=90,
                )
                thread_id = started["thread"]["id"]
                client.request(
                    "thread/name/set",
                    {"threadId": thread_id, "name": state["title"]},
                    timeout=30,
                )
            else:
                thread_id = request["thread_id"]
                resumed = client.request(
                    "thread/resume",
                    {"threadId": thread_id, **common},
                    timeout=90,
                )
                thread_id = resumed["thread"]["id"]
                if state.get("title"):
                    client.request(
                        "thread/name/set",
                        {"threadId": thread_id, "name": state["title"]},
                        timeout=30,
                    )

            update_job(
                job_id,
                status="thread_created",
                thread_id=thread_id,
                codex_url=f"codex://threads/{thread_id}",
                resume_command=f"codex resume {thread_id}",
            )

            turn = client.request(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": request["task"]}],
                    "cwd": state["cwd"],
                    "model": state["model"],
                    "effort": state["effort"],
                    "approvalPolicy": state["approval_policy"],
                    "summary": "concise",
                    "outputSchema": RESULT_SCHEMA,
                },
                timeout=90,
            )
            turn_id = turn["turn"]["id"]
            update_job(job_id, status="running", turn_id=turn_id)

            started_at = time.monotonic()
            interrupt_sent = False
            last_heartbeat = 0.0
            final_turn: dict[str, Any] | None = None

            while final_turn is None:
                elapsed = time.monotonic() - started_at
                if elapsed >= state["turn_timeout_seconds"]:
                    timed_out = True
                    cancelled = True
                if cancelled and not interrupt_sent:
                    client.request(
                        "turn/interrupt",
                        {"threadId": thread_id, "turnId": turn_id},
                        timeout=30,
                    )
                    interrupt_sent = True
                    update_job(job_id, status="cancelling")

                message = client.next_message(timeout=1.0)
                if message is None:
                    if time.monotonic() - last_heartbeat >= 15:
                        update_job(job_id, heartbeat_at=now_iso())
                        last_heartbeat = time.monotonic()
                    continue

                if "id" in message and "method" in message:
                    client.reject_server_request(message)
                    continue

                method = message.get("method")
                params = message.get("params") or {}
                if method == "item/agentMessage/delta":
                    delta = params.get("delta")
                    if isinstance(delta, str):
                        delta_parts.append(delta)
                elif method == "item/completed":
                    candidate = extract_agent_text(params.get("item"))
                    if candidate:
                        final_text = candidate
                elif method == "turn/completed":
                    candidate_turn = params.get("turn") or {}
                    if candidate_turn.get("id") == turn_id:
                        final_turn = candidate_turn

            if not final_text and delta_parts:
                final_text = "".join(delta_parts)
            if not final_text:
                for item in final_turn.get("items", []):
                    candidate = extract_agent_text(item)
                    if candidate:
                        final_text = candidate

            turn_status = final_turn.get("status")
            error = final_turn.get("error")
            if timed_out:
                status = "timed_out"
            elif turn_status == "interrupted" or cancelled:
                status = "cancelled"
            elif turn_status == "completed":
                status = "completed"
            else:
                status = "failed"

            update_job(
                job_id,
                status=status,
                completed_at=now_iso(),
                final_answer=final_text,
                result=parse_structured_result(final_text),
                error=error,
                app_server_pid=None,
            )
            return 0 if status == "completed" else 1
        except Exception as exc:  # noqa: BLE001 - worker must persist all failures
            update_job(
                job_id,
                status="cancelled" if cancelled else "failed",
                completed_at=now_iso(),
                error=str(exc),
                app_server_pid=None,
            )
            log_file.write(f"worker error: {exc!r}\n")
            log_file.flush()
            return 1
        finally:
            if client is not None:
                client.close()


def launch_job(args: argparse.Namespace, action: str) -> int:
    task = task_text(args)
    cwd = normalize_cwd(args.cwd)
    source_job: dict[str, Any] | None = None
    thread_id: str | None = None
    title = args.title
    if action == "continue":
        source_job = resolve_job(args.identifier, cwd)
        thread_id = source_job.get("thread_id") or args.identifier
        if not thread_id:
            raise SystemExit("续问目标没有 threadId")
        if not title:
            title = source_job.get("title")
        if args.cwd == "." and source_job.get("cwd"):
            cwd = source_job["cwd"]

    job_id = f"ceh-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    model = args.model or os.environ.get("CODEX_EXTERNAL_HANDOFF_MODEL", DEFAULT_MODEL)
    effort = args.effort or os.environ.get("CODEX_EXTERNAL_HANDOFF_EFFORT", DEFAULT_EFFORT)
    sandbox = args.sandbox
    state = {
        "schema_version": 1,
        "job_id": job_id,
        "action": action,
        "parent_job_id": source_job.get("job_id") if source_job else None,
        "thread_id": thread_id,
        "turn_id": None,
        "title": title,
        "cwd": cwd,
        "status": "queued",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "started_at": None,
        "completed_at": None,
        "model": model,
        "effort": effort,
        "sandbox": sandbox,
        "approval_policy": "never",
        "turn_timeout_seconds": args.turn_timeout,
        "task_sha256": hashlib.sha256(task.encode("utf-8")).hexdigest(),
        "task_source": (
            str(Path(args.task_file).expanduser().resolve()) if args.task_file else None
        ),
        "worker_pid": None,
        "app_server_pid": None,
        "log_path": str(log_path(job_id)),
        "codex_url": f"codex://threads/{thread_id}" if thread_id else None,
        "resume_command": f"codex resume {thread_id}" if thread_id else None,
        "final_answer": None,
        "result": None,
        "error": None,
    }
    atomic_write_json(job_path(job_id), state)
    atomic_write_json(
        request_path(job_id),
        {"action": action, "task": task, "thread_id": thread_id},
    )

    log_handle = log_path(job_id).open("a", encoding="utf-8")
    try:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "_worker", "--job-id", job_id],
            cwd=cwd,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=log_handle,
            start_new_session=True,
        )
    finally:
        log_handle.close()

    deadline = time.monotonic() + args.startup_timeout
    while time.monotonic() < deadline:
        current = read_json(job_path(job_id))
        if current.get("thread_id") or current.get("status") in TERMINAL_STATUSES:
            break
        time.sleep(0.2)
    else:
        current = read_json(job_path(job_id))
        current = {**public_state(current), "startup_wait_timed_out": True}
        print_json(current)
        return 4

    if args.wait:
        while current.get("status") not in TERMINAL_STATUSES:
            time.sleep(0.5)
            current = read_json(job_path(job_id))

    print_json(public_state(current))
    return 0 if current.get("status") != "failed" else 1


def command_status(args: argparse.Namespace) -> int:
    state = resolve_job(args.identifier)
    print_json(public_state(state))
    return 0


def command_result(args: argparse.Namespace) -> int:
    state = resolve_job(args.identifier)
    payload = public_state(state)
    print_json(payload)
    if state.get("status") == "completed":
        return 0
    if state.get("status") in {"failed", "cancelled", "timed_out"}:
        return 1
    return 3


def command_cancel(args: argparse.Namespace) -> int:
    state = resolve_job(args.identifier)
    if state.get("status") in TERMINAL_STATUSES:
        print_json(public_state(state))
        return 0
    pid = state.get("worker_pid")
    if is_process_alive(pid):
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + args.wait_seconds
        while time.monotonic() < deadline:
            time.sleep(0.25)
            state = read_json(job_path(state["job_id"]))
            if state.get("status") in TERMINAL_STATUSES:
                break
    else:
        state = update_job(
            state["job_id"],
            status="cancelled",
            completed_at=now_iso(),
            error="worker process was not running",
        )
    print_json(public_state(state))
    return 0


def command_open(args: argparse.Namespace) -> int:
    state = resolve_job(args.identifier)
    thread_id = state.get("thread_id")
    if not thread_id:
        raise SystemExit("任务尚未创建 threadId")
    url = f"codex://threads/{thread_id}"
    opened = False
    if not args.print_only and sys.platform == "darwin" and shutil.which("open"):
        opened = subprocess.run(["open", url], check=False).returncode == 0
    print_json(
        {
            "job_id": state["job_id"],
            "thread_id": thread_id,
            "codex_url": url,
            "resume_command": f"codex resume {thread_id}",
            "opened": opened,
        }
    )
    return 0


def command_doctor(_args: argparse.Namespace) -> int:
    codex = shutil.which("codex")
    if not codex:
        print_json({"status": "error", "error": "codex 不在 PATH 中"})
        return 1
    version = subprocess.run(
        [codex, "--version"], capture_output=True, text=True, check=False
    )
    if version.returncode != 0:
        print_json({"status": "error", "error": version.stderr.strip()})
        return 1
    log_file_path = state_home() / "doctor.log"
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    client: AppServerClient | None = None
    with log_file_path.open("a", encoding="utf-8") as log_file:
        try:
            client = AppServerClient(os.getcwd(), log_file)
            initialized = initialize_client(client)
            account = client.request("account/read", {"refreshToken": False}, timeout=30)
            account_type = (account.get("account") or {}).get("type")
            print_json(
                {
                    "status": "ok",
                    "codex": version.stdout.strip(),
                    "app_server": "ready",
                    "account_type": account_type,
                    "user_agent": initialized.get("userAgent"),
                    "state_home": str(state_home()),
                }
            )
            return 0
        except Exception as exc:  # noqa: BLE001
            print_json(
                {
                    "status": "error",
                    "codex": version.stdout.strip(),
                    "error": str(exc),
                    "log_path": str(log_file_path),
                }
            )
            return 1
        finally:
            if client is not None:
                client.close()


def add_task_arguments(parser: argparse.ArgumentParser, *, title_required: bool) -> None:
    parser.add_argument("--title", required=title_required)
    parser.add_argument("--task")
    parser.add_argument("--task-file")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--model")
    parser.add_argument("--effort", default=None)
    parser.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write"],
        default="read-only",
    )
    parser.add_argument("--startup-timeout", type=int, default=45)
    parser.add_argument("--turn-timeout", type=int, default=DEFAULT_TURN_TIMEOUT)
    parser.add_argument("--wait", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从 WorkBuddy/Claude Code 创建可见、持久的 Codex App Server Thread"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="创建命名 Codex Thread 并后台执行")
    add_task_arguments(ask, title_required=True)

    follow = subparsers.add_parser("continue", help="继续指定 Thread")
    follow.add_argument("identifier")
    add_task_arguments(follow, title_required=False)

    status = subparsers.add_parser("status", help="查看任务状态")
    status.add_argument("identifier", nargs="?")

    result = subparsers.add_parser("result", help="读取结构化结果")
    result.add_argument("identifier", nargs="?")

    cancel = subparsers.add_parser("cancel", help="中断后台任务")
    cancel.add_argument("identifier", nargs="?")
    cancel.add_argument("--wait-seconds", type=int, default=15)

    open_thread = subparsers.add_parser("open", help="在 Codex App 打开 Thread")
    open_thread.add_argument("identifier", nargs="?")
    open_thread.add_argument("--print-only", action="store_true")

    subparsers.add_parser("doctor", help="检查 Codex、App Server 与登录状态")

    worker = subparsers.add_parser("_worker")
    worker.add_argument("--job-id", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "ask":
        return launch_job(args, "ask")
    if args.command == "continue":
        return launch_job(args, "continue")
    if args.command == "status":
        return command_status(args)
    if args.command == "result":
        return command_result(args)
    if args.command == "cancel":
        return command_cancel(args)
    if args.command == "open":
        return command_open(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "_worker":
        return worker_main(args.job_id)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
