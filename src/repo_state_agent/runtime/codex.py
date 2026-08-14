from __future__ import annotations

import os
import shutil
import subprocess
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
    ) -> None:
        self.binary = binary
        self.model = model
        self.profile = profile
        self.sandbox = sandbox
        self.approve_for_me = approve_for_me
        self.quiet = quiet

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
                warnings.append("codex --version returned non-zero")
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"Could not execute Codex: {exc}")

        capabilities: list[str] = []
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
        error = ""
        interrupted = False
        process: subprocess.Popen[str] | None = None

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
            )
            assert process.stdin is not None
            assert process.stdout is not None
            process.stdin.write(prompt)
            process.stdin.close()
            with events_path.open("w", encoding="utf-8") as events_file:
                for line in process.stdout:
                    events_file.write(line)
                    events_file.flush()
                    event = accumulator.feed(line)
                    if not self.quiet and event is not None:
                        _print_compact_event(event)
            exit_code = process.wait()
        except KeyboardInterrupt:
            interrupted = True
            error = "Codex turn interrupted by operator"
            if process is not None:
                try:
                    process.terminate()
                    exit_code = process.wait(timeout=10)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
                    exit_code = 130
            else:
                exit_code = 130
        except OSError as exc:
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            exit_code = 127
            error = str(exc)

        if accumulator.errors and not error:
            error = "; ".join(accumulator.errors)
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


def _print_compact_event(event: dict[str, object]) -> None:
    event_type = event.get("type")
    if event_type == "thread.started":
        print(f"[codex] thread {event.get('thread_id')}")
    elif event_type == "turn.completed":
        usage = event.get("usage")
        print(f"[codex] turn complete usage={usage}")
    elif event_type in {"turn.failed", "error"}:
        print(f"[codex] {event_type}: {event.get('error') or event.get('message')}")
