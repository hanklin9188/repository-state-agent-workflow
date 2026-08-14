from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
from contextlib import suppress
from pathlib import Path

from .events import CodexEventAccumulator
from .model import AdapterDoctorResult, AgentTurnResult


class CodexAdapter:
    name = "codex"

    def __init__(
        self,
        *,
        binary: str = "codex",
        model: str | None = None,
        profile: str | None = None,
        sandbox: str = "workspace-write",
        approve_for_me: bool = False,
        quiet: bool = False,
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
        self.approve_for_me = approve_for_me
        self.quiet = quiet
        self.turn_timeout_seconds = turn_timeout_seconds
        self.stdout_eof_grace_seconds = stdout_eof_grace_seconds

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
            command.extend(["--sandbox", self.sandbox])
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
        events_path = run_dir / f"turn-{turn_index:04d}.jsonl"
        last_message_path = run_dir / f"turn-{turn_index:04d}-last-message.txt"
        command = self.build_command(
            root=root,
            last_message_path=last_message_path,
            thread_id=thread_id,
        )
        env = os.environ.copy()
        env.update(environment)
        accumulator = CodexEventAccumulator()
        reader_errors: list[str] = []
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
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
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
                            if not self.quiet and event is not None:
                                _print_compact_event(event)
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
        if accumulator.errors and not error:
            error = "; ".join(accumulator.errors)
        if exit_code == 0 and accumulator.thread_id is None and not error:
            error = "Codex JSON stream did not emit thread.started"
        if exit_code == 0 and not accumulator.turn_completed and not error:
            error = "Codex JSON stream did not emit turn.completed"

        last_message = (
            last_message_path.read_text(encoding="utf-8")
            if last_message_path.is_file()
            else ""
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
