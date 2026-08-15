from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from .events import CodexEventAccumulator
from .model import AdapterDoctorResult, AgentTurnResult

CodexEventSink = Callable[[dict[str, Any]], None]
CodexEventGuard = Callable[[dict[str, Any]], str | None]
_SANDBOXES = {"read-only", "workspace-write", "danger-full-access"}


class CodexAdapter:
    name = "codex"

    def __init__(
        self,
        *,
        binary: str = "codex",
        model: str | None = None,
        profile: str | None = None,
        sandbox: str = "workspace-write",
        task_sandbox_overrides: dict[str, str] | None = None,
        forced_sandbox: str | None = None,
        forced_sandbox_task: str | None = None,
        approve_for_me: bool = False,
        quiet: bool = False,
        event_sink: CodexEventSink | None = None,
        event_guard: CodexEventGuard | None = None,
        turn_timeout_seconds: float = 7_200.0,
        stdout_eof_grace_seconds: float = 10.0,
    ) -> None:
        if turn_timeout_seconds <= 0:
            raise ValueError("turn_timeout_seconds must be positive")
        if stdout_eof_grace_seconds <= 0:
            raise ValueError("stdout_eof_grace_seconds must be positive")
        self.binary = binary
        self.model = model
        self.profile = profile
        self.sandbox = sandbox
        self.task_sandbox_overrides = {
            str(task): str(mode) for task, mode in (task_sandbox_overrides or {}).items()
        }
        self.forced_sandbox = forced_sandbox
        self.forced_sandbox_task = str(forced_sandbox_task or "")
        for label, mode in {
            "default": self.sandbox,
            "forced": self.forced_sandbox,
            **{f"task:{task}": value for task, value in self.task_sandbox_overrides.items()},
        }.items():
            if mode is not None and mode not in _SANDBOXES:
                raise ValueError(f"unsupported Codex sandbox for {label}: {mode}")
        self.approve_for_me = approve_for_me
        self.quiet = quiet
        self.event_sink = event_sink
        self.event_guard = event_guard
        self.turn_timeout_seconds = turn_timeout_seconds
        self.stdout_eof_grace_seconds = stdout_eof_grace_seconds

    def resolve_turn_settings(self, environment: dict[str, str]) -> dict[str, str]:
        task_id = str(environment.get("RSAW_TASK_ID") or "")
        pre_resolved = str(environment.get("RSAW_RESOLVED_SANDBOX") or "")
        if pre_resolved:
            sandbox = pre_resolved
            source = str(environment.get("RSAW_SANDBOX_SOURCE") or "supervisor")
        elif self.forced_sandbox and task_id == self.forced_sandbox_task:
            sandbox = self.forced_sandbox
            source = "CLI task override"
        elif task_id and task_id in self.task_sandbox_overrides:
            sandbox = self.task_sandbox_overrides[task_id]
            source = "task override"
        else:
            sandbox = self.sandbox
            source = "default"
        if sandbox not in _SANDBOXES:
            raise ValueError(f"unsupported Codex sandbox mode: {sandbox}")
        return {"task": task_id, "sandbox": sandbox, "source": source}

    def doctor(self) -> AdapterDoctorResult:
        resolved = shutil.which(self.binary)
        if resolved is None:
            return AdapterDoctorResult(
                ok=False,
                adapter=self.name,
                binary=self.binary,
                errors=(f"Codex binary not found: {self.binary}",),
            )
        errors: list[str] = []
        warnings: list[str] = []
        capabilities: list[str] = []
        version = ""

        try:
            version_result = subprocess.run(
                [resolved, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            version = (version_result.stdout or version_result.stderr).strip()
            if version_result.returncode != 0:
                errors.append("codex --version returned non-zero")
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"Could not execute Codex: {exc}")

        if not errors:
            try:
                help_result = subprocess.run(
                    [resolved, "exec", "--help"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                help_text = f"{help_result.stdout}\n{help_result.stderr}"
                required = {
                    "exec-json": "--json",
                    "exec-resume": "resume",
                    "last-message": "--output-last-message",
                }
                for capability, marker in required.items():
                    if marker in help_text:
                        capabilities.append(capability)
                    else:
                        errors.append(f"Codex exec is missing required capability: {marker}")
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"Could not inspect Codex exec: {exc}")

        if not errors:
            try:
                auth_result = subprocess.run(
                    [resolved, "login", "status"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if auth_result.returncode == 0:
                    capabilities.append("authenticated")
                else:
                    errors.append("Codex is not authenticated; run `codex login`")
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"Could not verify Codex authentication: {exc}")

        return AdapterDoctorResult(
            ok=not errors,
            adapter=self.name,
            binary=resolved,
            version=version,
            capabilities=tuple(capabilities),
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def build_command(
        self,
        *,
        root: Path,
        last_message_path: Path,
        thread_id: str | None,
        sandbox: str | None = None,
    ) -> list[str]:
        command = [
            self.binary,
            "exec",
            "--json",
            "--color",
            "never",
            "--output-last-message",
            str(last_message_path),
            "--cd",
            str(root),
        ]
        if self.model:
            command.extend(["--model", self.model])
        if self.profile:
            command.extend(["--profile", self.profile])
        if self.approve_for_me:
            command.append("--approve-for-me")
        else:
            command.extend(["--sandbox", sandbox or self.sandbox])
        if thread_id:
            command.extend(["resume", thread_id, "-"])
        else:
            command.append("-")
        return command

    def run_turn(
        self,
        *,
        prompt: str,
        root: Path,
        run_dir: Path,
        turn_index: int,
        thread_id: str | None,
        environment: dict[str, str],
    ) -> AgentTurnResult:
        run_dir.mkdir(parents=True, exist_ok=True)
        _reset_bound_guard(self.event_guard)
        events_path = run_dir / f"turn-{turn_index:04d}.jsonl"
        last_message_path = run_dir / f"turn-{turn_index:04d}-last-message.txt"
        turn_settings = self.resolve_turn_settings(environment)
        command = self.build_command(
            root=root,
            last_message_path=last_message_path,
            thread_id=thread_id,
            sandbox=turn_settings["sandbox"],
        )
        env = os.environ.copy()
        env.update(environment)
        env["RSAW_RESOLVED_SANDBOX"] = turn_settings["sandbox"]
        env["RSAW_SANDBOX_SOURCE"] = turn_settings["source"]
        accumulator = CodexEventAccumulator()
        reader_errors: list[str] = []
        guard_errors: list[str] = []
        error = ""
        interrupted = False
        exit_code = 127
        process: subprocess.Popen[str] | None = None
        reader: threading.Thread | None = None

        try:
            process = subprocess.Popen(
                command,
                cwd=root,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=(os.name == "posix"),
                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
            )
            assert process.stdin is not None
            assert process.stdout is not None

            def drain_output() -> None:
                try:
                    with events_path.open("w", encoding="utf-8") as events_file:
                        for line in process.stdout:
                            events_file.write(line)
                            events_file.flush()
                            event = accumulator.feed(line)
                            if event is not None:
                                _notify_event(self.event_sink, event)
                                if self.event_guard is not None and not guard_errors:
                                    reason = self.event_guard(event)
                                    if reason:
                                        guard_errors.append(reason)
                                        _request_process_stop(process)
                                if not self.quiet:
                                    _print_compact_event(event)
                            else:
                                diagnostic = line.strip()
                                if diagnostic:
                                    _notify_event(
                                        self.event_sink,
                                        {
                                            "type": "codex.diagnostic",
                                            "message": _truncate(diagnostic, 240),
                                        },
                                    )
                except (OSError, ValueError) as exc:
                    reader_errors.append(str(exc))

            reader = threading.Thread(
                target=drain_output,
                name=f"rsaw-codex-output-{turn_index}",
                daemon=True,
            )
            reader.start()
            process.stdin.write(prompt)
            process.stdin.close()
            exit_code = process.wait(timeout=self.turn_timeout_seconds)
            reader.join(timeout=self.stdout_eof_grace_seconds)
            if reader.is_alive():
                error = "Codex stdout remained open after the parent process exited"
                _terminate_process_tree(process)
                process.stdout.close()
                reader.join(timeout=1)
                exit_code = 124
        except subprocess.TimeoutExpired:
            error = f"Codex turn exceeded {self.turn_timeout_seconds:g} seconds"
            if process is not None:
                _terminate_process_tree(process)
                if process.stdout is not None:
                    process.stdout.close()
            if reader is not None:
                reader.join(timeout=1)
            exit_code = 124
        except KeyboardInterrupt:
            interrupted = True
            error = "Codex turn interrupted by operator"
            if process is not None:
                _terminate_process_tree(process)
                if process.stdout is not None:
                    process.stdout.close()
            if reader is not None:
                reader.join(timeout=1)
            exit_code = 130
        except OSError as exc:
            error = str(exc)
            if process is not None:
                _terminate_process_tree(process)
            exit_code = 127

        if reader_errors and not error:
            error = "; ".join(reader_errors)
        if guard_errors and not error:
            error = f"TOOL_BUDGET_EXCEEDED:{guard_errors[0]}"
        if accumulator.errors and not error:
            error = "; ".join(accumulator.errors)
        if exit_code == 0 and accumulator.thread_id is None and not error:
            error = "Codex JSON stream did not emit thread.started"
        if exit_code == 0 and not accumulator.turn_completed and not error:
            error = "Codex JSON stream did not emit turn.completed"

        last_message = (
            last_message_path.read_text(encoding="utf-8") if last_message_path.is_file() else ""
        )
        return AgentTurnResult(
            exit_code=exit_code,
            thread_id=accumulator.thread_id or thread_id,
            usage=accumulator.total_usage,
            latest_turn_usage=accumulator.latest_turn_usage,
            last_message=last_message,
            event_count=accumulator.event_count,
            events_path=events_path,
            last_message_path=last_message_path,
            error=error,
            interrupted=interrupted,
        )


def _reset_bound_guard(guard: CodexEventGuard | None) -> None:
    if guard is None:
        return
    owner = getattr(guard, "__self__", None)
    reset = getattr(owner, "reset", None)
    if callable(reset):
        reset()


def _notify_event(sink: CodexEventSink | None, event: dict[str, Any]) -> None:
    if sink is None:
        return
    try:
        sink(event)
    except Exception:
        # Observability is downstream from execution and must never break a turn.
        return


def _request_process_stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        return
    with suppress(OSError):
        process.terminate()


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "posix":
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _print_compact_event(event: dict[str, object]) -> None:
    event_type = event.get("type")
    if event_type == "thread.started":
        print(f"[codex] thread {event.get('thread_id')}")
    elif event_type == "turn.completed":
        usage = event.get("usage")
        print(f"[codex] turn complete usage={usage}")
    elif event_type in {"turn.failed", "error"}:
        print(f"[codex] {event_type}: {event.get('error') or event.get('message')}")


def _truncate(value: str, limit: int) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
