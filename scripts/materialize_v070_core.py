from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing anchor for {label}: {path}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def regex_once(path: str, pattern: str, replacement: str, label: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    updated, count = re.subn(
        pattern,
        lambda _match: replacement,
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    if count != 1:
        raise SystemExit(f"regex anchor count={count} for {label}: {path}")
    target.write_text(updated, encoding="utf-8")


# ---------------------------------------------------------------------------
# Codex adapter: enforce tool budgets while a turn is still running.
# ---------------------------------------------------------------------------
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "CodexEventSink = Callable[[dict[str, Any]], None]\n",
    "CodexEventSink = Callable[[dict[str, Any]], None]\n"
    "CodexEventGuard = Callable[[dict[str, Any]], str | None]\n",
    "Codex event guard alias",
)
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "        event_sink: CodexEventSink | None = None,\n"
    "        turn_timeout_seconds: float = 7_200.0,\n",
    "        event_sink: CodexEventSink | None = None,\n"
    "        event_guard: CodexEventGuard | None = None,\n"
    "        turn_timeout_seconds: float = 7_200.0,\n",
    "Codex event guard parameter",
)
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "        self.event_sink = event_sink\n"
    "        self.turn_timeout_seconds = turn_timeout_seconds\n",
    "        self.event_sink = event_sink\n"
    "        self.event_guard = event_guard\n"
    "        self.turn_timeout_seconds = turn_timeout_seconds\n",
    "Codex event guard assignment",
)
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "        reader_errors: list[str] = []\n"
    "        error = \"\"\n",
    "        reader_errors: list[str] = []\n"
    "        guard_errors: list[str] = []\n"
    "        error = \"\"\n",
    "Codex guard error state",
)
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "                            if event is not None:\n"
    "                                _notify_event(self.event_sink, event)\n"
    "                                if not self.quiet:\n"
    "                                    _print_compact_event(event)\n"
    "                            else:\n",
    "                            if event is not None:\n"
    "                                _notify_event(self.event_sink, event)\n"
    "                                if self.event_guard is not None and not guard_errors:\n"
    "                                    reason = self.event_guard(event)\n"
    "                                    if reason:\n"
    "                                        guard_errors.append(reason)\n"
    "                                        _request_process_stop(process)\n"
    "                                if not self.quiet:\n"
    "                                    _print_compact_event(event)\n"
    "                            else:\n",
    "Codex live guard observation",
)
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "        if reader_errors and not error:\n"
    "            error = \"; \".join(reader_errors)\n"
    "        if accumulator.errors and not error:\n",
    "        if reader_errors and not error:\n"
    "            error = \"; \".join(reader_errors)\n"
    "        if guard_errors and not error:\n"
    "            error = f\"TOOL_BUDGET_EXCEEDED:{guard_errors[0]}\"\n"
    "        if accumulator.errors and not error:\n",
    "Codex guard terminal error",
)
replace_once(
    "src/repo_state_agent/runtime/codex.py",
    "\ndef _terminate_process_tree(process: subprocess.Popen[str]) -> None:\n",
    "\ndef _request_process_stop(process: subprocess.Popen[str]) -> None:\n"
    "    if process.poll() is not None:\n"
    "        return\n"
    "    if os.name == \"posix\":\n"
    "        with suppress(ProcessLookupError):\n"
    "            os.killpg(process.pid, signal.SIGTERM)\n"
    "        return\n"
    "    with suppress(OSError):\n"
    "        process.terminate()\n"
    "\n\n"
    "def _terminate_process_tree(process: subprocess.Popen[str]) -> None:\n",
    "non-blocking Codex process stop",
)

# ---------------------------------------------------------------------------
# v0.7 runtime hardening.
# ---------------------------------------------------------------------------
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "from ..model import ActiveState\n"
    "from ..parsing import parse_active\n"
    "from ..verify import verify_repository\n",
    "from ..active_format import (\n"
    "    active_budget_errors,\n"
    "    canonicalize_active_text,\n"
    "    replace_section as replace_active_section,\n"
    ")\n"
    "from ..model import ActiveState\n"
    "from ..parsing import parse_active\n"
    "from ..verify import verify_repository\n"
    "from .tool_budget import is_broad_discovery\n",
    "v0.7 runtime imports",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "    max_total_input_tokens: int = 5_000_000\n"
    "    quiet: bool = False\n",
    "    max_total_input_tokens: int = 5_000_000\n"
    "    max_tool_calls_per_turn: int = 32\n"
    "    max_tool_output_tokens: int = 50_000\n"
    "    max_single_tool_output_tokens: int = 20_000\n"
    "    max_broad_discovery_commands: int = 2\n"
    "    enforce_tool_budget: bool = True\n"
    "    quiet: bool = False\n",
    "v0.7 tool budget options",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "        governor = v6.get(\"governor\", {}) if isinstance(v6.get(\"governor\", {}), dict) else {}\n"
    "        return cls(\n",
    "        governor = v6.get(\"governor\", {}) if isinstance(v6.get(\"governor\", {}), dict) else {}\n"
    "        tool_budget = runtime.get(\"toolBudget\", {}) if isinstance(runtime.get(\"toolBudget\", {}), dict) else {}\n"
    "        return cls(\n",
    "read tool budget config",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "            max_total_input_tokens=_nonneg(runtime.get(\"max_total_input_tokens\"), 5_000_000),\n"
    "            quiet=quiet,\n",
    "            max_total_input_tokens=_nonneg(runtime.get(\"max_total_input_tokens\"), 5_000_000),\n"
    "            max_tool_calls_per_turn=_pos(tool_budget.get(\"maxToolCallsPerTurn\"), 32),\n"
    "            max_tool_output_tokens=_pos(tool_budget.get(\"maxToolOutputTokens\"), 50_000),\n"
    "            max_single_tool_output_tokens=_pos(tool_budget.get(\"maxSingleToolOutputTokens\"), 20_000),\n"
    "            max_broad_discovery_commands=_nonneg(tool_budget.get(\"maxBroadDiscoveryCommands\"), 2),\n"
    "            enforce_tool_budget=bool(tool_budget.get(\"enforce\", True)),\n"
    "            quiet=quiet,\n",
    "materialize tool budget options",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "        task_id = _s(value.get(\"id\") or value.get(\"taskId\"))\n"
    "        spec = _s(value.get(\"spec\") or value.get(\"taskSpec\"))\n",
    "        task_id = _s(\n"
    "            value.get(\"id\")\n"
    "            or value.get(\"taskId\")\n"
    "            or value.get(\"task_id\")\n"
    "        )\n"
    "        spec = _s(\n"
    "            value.get(\"spec\")\n"
    "            or value.get(\"taskSpec\")\n"
    "            or value.get(\"task_spec\")\n"
    "        )\n",
    "TaskRef snake_case compatibility",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "        incoming_refs = _str_list(delta.get(\"evidenceRefs\")) + evidence_refs\n"
    "        self.evidence_refs = list(dict.fromkeys([*self.evidence_refs, *incoming_refs]))[-64:]\n",
    "        # Authoritative evidence is bound by the supervisor after the turn.\n"
    "        # Model-provided source labels are non-authoritative hints and are not persisted.\n"
    "        incoming_refs = evidence_refs\n"
    "        self.evidence_refs = list(dict.fromkeys([*self.evidence_refs, *incoming_refs]))[-64:]\n",
    "supervisor-owned evidence binding",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "    recovery_rediscovery_commands: int = 0\n"
    "    occupancy_samples: list[float] = field(default_factory=list)\n",
    "    recovery_rediscovery_commands: int = 0\n"
    "    tool_output_tokens: int = 0\n"
    "    peak_tool_output_tokens: int = 0\n"
    "    tool_budget_aborts: int = 0\n"
    "    occupancy_samples: list[float] = field(default_factory=list)\n",
    "v0.7 summary metrics",
)

# Insert the v0.7 migration beside the compatible v0.6 migration.
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "    plan[\"status\"] = \"MIGRATED\"\n"
    "    return plan\n\n\n"
    "def compile_context(",
    "    plan[\"status\"] = \"MIGRATED\"\n"
    "    return plan\n\n\n"
    "def migrate_v7(root: Path, *, apply: bool = False) -> dict[str, Any]:\n"
    "    root = root.resolve()\n"
    "    config_path = root / \".rsaw/config.json\"\n"
    "    active_path = root / \"ACTIVE.md\"\n"
    "    before_active = _sha_file(active_path) if active_path.is_file() else \"\"\n"
    "    raw: dict[str, Any] = {}\n"
    "    if config_path.is_file():\n"
    "        value = json.loads(config_path.read_text(encoding=\"utf-8\"))\n"
    "        if not isinstance(value, dict):\n"
    "            raise ValueError(\".rsaw/config.json must be an object\")\n"
    "        raw = value\n"
    "    runtime = raw.setdefault(\"runtime\", {})\n"
    "    if not isinstance(runtime, dict):\n"
    "        raise ValueError(\"runtime must be an object\")\n"
    "    raw[\"schema_version\"] = 4\n"
    "    runtime.setdefault(\"max_transitions\", 100)\n"
    "    runtime.setdefault(\"max_total_input_tokens\", 5_000_000)\n"
    "    v6 = runtime.setdefault(\"v6\", {})\n"
    "    if not isinstance(v6, dict):\n"
    "        raise ValueError(\"runtime.v6 must be an object\")\n"
    "    v6.setdefault(\"enabled\", True)\n"
    "    v6.setdefault(\"contextWindowTokens\", 128_000)\n"
    "    v6.setdefault(\"contextCompiler\", {\n"
    "        \"targetEnvelopeTokens\": 6_000,\n"
    "        \"hardEnvelopeTokens\": 12_000,\n"
    "        \"maxExactEvidenceTokens\": 7_000,\n"
    "        \"maxSemanticCapsuleTokens\": 2_500,\n"
    "        \"maxValidationSummaryTokens\": 1_000,\n"
    "        \"useReadIfChanged\": True,\n"
    "        \"useEvidenceHandles\": True,\n"
    "        \"useDeltaContext\": True,\n"
    "    })\n"
    "    v6.setdefault(\"governor\", {\n"
    "        \"compactCandidateRatio\": 0.75,\n"
    "        \"compactRequiredRatio\": 0.85,\n"
    "        \"hardTurnCeiling\": 8,\n"
    "        \"useAggregateProviderInputAsOccupancy\": False,\n"
    "    })\n"
    "    v6.setdefault(\"bookkeeping\", {\n"
    "        \"agentMayMutateActive\": False,\n"
    "        \"agentMayRunAdvance\": False,\n"
    "        \"supervisorOwnsTransition\": True,\n"
    "    })\n"
    "    runtime.setdefault(\"codex\", {\n"
    "        \"binary\": runtime.get(\"codex_binary\", \"codex\"),\n"
    "        \"defaultSandbox\": runtime.get(\"sandbox\", \"workspace-write\"),\n"
    "        \"taskSandboxOverrides\": {},\n"
    "    })\n"
    "    runtime.setdefault(\"toolBudget\", {\n"
    "        \"maxToolCallsPerTurn\": 32,\n"
    "        \"maxToolOutputTokens\": 50_000,\n"
    "        \"maxSingleToolOutputTokens\": 20_000,\n"
    "        \"maxBroadDiscoveryCommands\": 2,\n"
    "        \"enforce\": True,\n"
    "    })\n"
    "    plan = {\n"
    "        \"target\": \"0.7\",\n"
    "        \"apply\": apply,\n"
    "        \"config\": str(config_path.relative_to(root)),\n"
    "        \"backup\": \".rsaw/config.v06.backup.json\",\n"
    "        \"activeSha256Before\": before_active,\n"
    "        \"preservesActive\": True,\n"
    "        \"v7Enabled\": True,\n"
    "    }\n"
    "    if not apply:\n"
    "        return plan\n"
    "    config_path.parent.mkdir(parents=True, exist_ok=True)\n"
    "    if config_path.is_file():\n"
    "        backup = root / \".rsaw/config.v06.backup.json\"\n"
    "        if not backup.exists():\n"
    "            backup.write_bytes(config_path.read_bytes())\n"
    "    atomic_write_json(config_path, raw)\n"
    "    after_active = _sha_file(active_path) if active_path.is_file() else \"\"\n"
    "    if before_active != after_active:\n"
    "        raise RuntimeError(\"migration changed ACTIVE.md; refusing migration\")\n"
    "    plan[\"activeSha256After\"] = after_active\n"
    "    plan[\"status\"] = \"MIGRATED\"\n"
    "    return plan\n\n\n"
    "def compile_context(",
    "insert v0.7 migration",
)

regex_once(
    "src/repo_state_agent/runtime/v6.py",
    r"def inspect_turn_events\(result: AgentTurnResult, root: Path\) -> dict\[str, Any\]:.*?\n\ndef deterministic_gate",
    '''def inspect_turn_events(result: AgentTurnResult, root: Path) -> dict[str, Any]:
    tool_calls = 0
    command_records: dict[str, dict[str, Any]] = {}
    command_order: list[str] = []
    started: set[str] = set()
    completed_output: set[str] = set()
    broad_discovery: set[str] = set()
    retained_output_tokens = 0
    peak_tool_output_tokens = 0

    if result.events_path and result.events_path.is_file():
        for line in result.events_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            item = event.get("item")
            payload = item if isinstance(item, dict) else event
            item_type = _s(payload.get("type")).lower()
            event_type = _s(event.get("type"))
            cmd = payload.get("command") or payload.get("cmd")
            if isinstance(cmd, list):
                cmd = " ".join(str(x) for x in cmd)
            command = _one_line(cmd) if isinstance(cmd, str) else ""
            identity = _s(payload.get("id") or event.get("id")) or command or item_type

            is_tool = item_type in {
                "command_execution",
                "command",
                "shell",
                "shell_command",
                "tool_call",
                "mcp_tool_call",
                "function_call",
            }
            if is_tool and event_type.endswith(".started") and identity not in started:
                started.add(identity)
                tool_calls += 1
                if command and is_broad_discovery(command):
                    broad_discovery.add(identity)

            if command and item_type in {
                "command_execution",
                "command",
                "shell",
                "shell_command",
            }:
                if identity not in command_records:
                    command_order.append(identity)
                record = command_records.get(identity, {"command": command})
                record["command"] = command
                record["eventType"] = event_type
                exit_code = _maybe_int(
                    payload.get("exit_code")
                    if payload.get("exit_code") is not None
                    else payload.get("exitCode")
                )
                if exit_code is not None or event_type.endswith(".completed"):
                    record["exitCode"] = exit_code
                command_records[identity] = record

            if is_tool and event_type.endswith(".completed") and identity not in completed_output:
                completed_output.add(identity)
                output = (
                    payload.get("aggregated_output")
                    or payload.get("output")
                    or payload.get("stdout")
                )
                if isinstance(output, str):
                    output_tokens = _tokens(output)
                    retained_output_tokens += output_tokens
                    peak_tool_output_tokens = max(
                        peak_tool_output_tokens, output_tokens
                    )

    commands = [command_records[key] for key in command_order]
    return {
        "tool_calls": tool_calls,
        "commands": commands,
        "retained_tool_output_tokens": retained_output_tokens,
        "peak_tool_output_tokens": peak_tool_output_tokens,
        "broad_discovery_commands": len(broad_discovery),
    }


def deterministic_gate''',
    "deduplicated turn event inspection",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "    refs = set(_str_list(result.capsule_delta.get(\"evidenceRefs\")))\n"
    "    unknown = refs - evidence_ids\n"
    "    if unknown:\n"
    "        errors.append(\"UNKNOWN_EVIDENCE_REFS:\" + \",\".join(sorted(unknown)))\n",
    "    refs = set(_str_list(result.capsule_delta.get(\"evidenceRefs\")))\n"
    "    claimed_handles = {ref for ref in refs if ref.startswith(\"EV-\")}\n"
    "    unknown_handles = claimed_handles - evidence_ids\n"
    "    if unknown_handles:\n"
    "        errors.append(\"UNKNOWN_EVIDENCE_REFS:\" + \",\".join(sorted(unknown_handles)))\n"
    "    if refs - claimed_handles:\n"
    "        warnings.append(\"MODEL_SOURCE_REFS_IGNORED:SUPERVISOR_OWNS_EVIDENCE_BINDING\")\n",
    "evidence handle gate semantics",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "                summary.total_usage = summary.total_usage + turn.usage\n"
    "                if not turn.ok:\n"
    "                    return finish(\"FAILED\", f\"AGENT_TURN_FAILED:{turn.error or turn.exit_code}\", 22)\n"
    "                event_info = inspect_turn_events(turn, root)\n"
    "                summary.tool_calls += int(event_info[\"tool_calls\"])\n"
    "                epoch_tokens_estimate += turn.latest_turn_usage.output_tokens + int(event_info[\"retained_tool_output_tokens\"])\n",
    "                summary.total_usage = summary.total_usage + turn.usage\n"
    "                event_info = inspect_turn_events(turn, root)\n"
    "                summary.tool_calls += int(event_info[\"tool_calls\"])\n"
    "                summary.tool_output_tokens += int(event_info[\"retained_tool_output_tokens\"])\n"
    "                summary.peak_tool_output_tokens = max(\n"
    "                    summary.peak_tool_output_tokens,\n"
    "                    int(event_info[\"peak_tool_output_tokens\"]),\n"
    "                )\n"
    "                summary.recovery_rediscovery_commands += int(\n"
    "                    event_info[\"broad_discovery_commands\"]\n"
    "                )\n"
    "                epoch_tokens_estimate += (\n"
    "                    turn.latest_turn_usage.output_tokens\n"
    "                    + int(event_info[\"retained_tool_output_tokens\"])\n"
    "                )\n"
    "                if not turn.ok:\n"
    "                    if turn.error.startswith(\"TOOL_BUDGET_EXCEEDED:\"):\n"
    "                        summary.tool_budget_aborts += 1\n"
    "                        return finish(\"PAUSED\", turn.error, 26)\n"
    "                    return finish(\"FAILED\", f\"AGENT_TURN_FAILED:{turn.error or turn.exit_code}\", 22)\n",
    "turn telemetry before failure handling",
)

# Transactional checkpoint advancement: validate proposed ACTIVE, then roll back every
# authority file if post-advance verification fails.
regex_once(
    "src/repo_state_agent/runtime/v6.py",
    r"                checkpoint_index \+= 1\n.*?                summary\.checkpoints_observed \+= 1",
    '''                candidate_index = checkpoint_index + 1
                checkpoint_id = f"CP-{candidate_index:04d}"
                revision = _git_revision(root)
                capsule = SemanticCapsule.load(root, state.workstream_id)
                capsule.merge(
                    result.capsule_delta,
                    checkpoint_id=checkpoint_id,
                    revision=revision,
                    role=state.current_role or state.next_role,
                    objective=result.summary or state.next_action,
                    evidence_refs=[h.evidence_id for h in evidence_handles],
                    max_tokens=options.max_capsule_tokens,
                )
                complete = result.requested_action == "COMPLETE"
                next_role = (
                    result.next_task.role
                    if result.next_task
                    else (state.next_role or state.current_role)
                )
                decision = governor_decision(
                    current_role=state.current_role or state.next_role,
                    next_role=next_role,
                    requested_action=result.requested_action,
                    human_gate=result.human_gate,
                    complete=complete,
                    estimated_occupancy_tokens=epoch_tokens_estimate,
                    context_window_tokens=options.context_window_tokens,
                    compact_candidate_ratio=options.compact_candidate_ratio,
                    compact_required_ratio=options.compact_required_ratio,
                    thread_turns=thread_turns,
                    hard_turn_ceiling=options.hard_turn_ceiling,
                )
                summary.occupancy_samples.append(decision.occupancy_ratio)
                if decision.action == "COMPACT":
                    summary.context_compactions += 1
                elif decision.action == "ROTATE":
                    summary.role_rotations += 1
                _emit(store, event_sink, {"type": "v6.governor", **decision.to_dict()})

                proposed_active = _render_active_markdown(
                    root, state, result, decision, checkpoint_id
                )
                budget_errors = active_budget_errors(proposed_active)
                if budget_errors:
                    return finish(
                        "FAILED",
                        "PROPOSED_ACTIVE_INVALID:" + ";".join(budget_errors),
                        29,
                    )

                capsule_path = (
                    root
                    / ".rsaw/state/capsules"
                    / f"{_safe_name(capsule.workstream_id)}.json"
                )
                review_manifest_path = None
                if decision.action == "ROTATE" and _role(next_role) == "reviewer":
                    review_manifest_path = (
                        root / ".rsaw/state/reviews" / f"{checkpoint_id}.json"
                    )
                checkpoint_path = (
                    root / ".rsaw/state/checkpoints" / f"{checkpoint_id}.json"
                )
                sidecar_path = checkpoint_path.with_suffix(
                    checkpoint_path.suffix + ".sha256"
                )
                if checkpoint_path.exists() or sidecar_path.exists():
                    return finish(
                        "FAILED", f"CHECKPOINT_ALREADY_EXISTS:{checkpoint_id}", 29
                    )

                authority_paths = [
                    root / "ACTIVE.md",
                    root / ".rsaw/state/active.json",
                    capsule_path,
                ]
                if review_manifest_path is not None:
                    authority_paths.append(review_manifest_path)
                snapshots = {path: _snapshot_file(path) for path in authority_paths}

                try:
                    capsule_path = capsule.save(root)
                    summary.semantic_capsule_tokens += _tokens(
                        json.dumps(capsule.to_dict(), sort_keys=True)
                    )
                    if review_manifest_path is not None:
                        review_manifest_path = _write_review_manifest(
                            root,
                            checkpoint_id,
                            state,
                            result,
                            evidence_handles,
                            revision,
                        )
                    checkpoint = {
                        "schemaVersion": SCHEMA_CHECKPOINT,
                        "checkpointId": checkpoint_id,
                        "runId": run_id,
                        "workstreamId": state.workstream_id,
                        "taskId": state.task_id,
                        "sourceRevision": revision,
                        "acceptedAt": utc_now(),
                        "result": _checkpoint_result_dict(result),
                        "gate": gate.to_dict(),
                        "governor": decision.to_dict(),
                        "contextEnvelopeRef": envelope_path.relative_to(root).as_posix(),
                        "contextEnvelopeSha256": envelope.sha256,
                        "semanticCapsuleRef": capsule_path.relative_to(root).as_posix(),
                        "semanticCapsuleSha256": _sha_file(capsule_path),
                        "evidence": [h.to_dict() for h in evidence_handles],
                        "reviewManifestRef": (
                            review_manifest_path.relative_to(root).as_posix()
                            if review_manifest_path
                            else None
                        ),
                    }
                    atomic_write_json(checkpoint_path, checkpoint)
                    _write_sha_sidecar(checkpoint_path)
                    _write_active_pointer(
                        root,
                        state,
                        result,
                        decision,
                        checkpoint_id,
                        capsule_path,
                        revision,
                    )
                    (root / "ACTIVE.md").write_text(
                        proposed_active, encoding="utf-8"
                    )
                    post = verify_repository(root)
                    if not post.ok:
                        raise RuntimeError(
                            "POST_ADVANCE_REPOSITORY_INVALID:"
                            + ";".join(post.errors)
                        )
                except Exception as exc:
                    checkpoint_path.unlink(missing_ok=True)
                    sidecar_path.unlink(missing_ok=True)
                    for authority_path, snapshot in snapshots.items():
                        _restore_file(authority_path, snapshot)
                    return finish("FAILED", str(exc), 23)

                checkpoint_index = candidate_index
                summary.deterministic_operations += 5
                summary.checkpoints_observed += 1''',
    "transactional checkpoint advancement",
)

regex_once(
    "src/repo_state_agent/runtime/v6.py",
    r"def _v6_prompt\(state: ActiveState, envelope: ContextEnvelope\) -> str:.*?\n\ndef _write_review_manifest",
    '''def _v6_prompt(state: ActiveState, envelope: ContextEnvelope) -> str:
    return f"""RSAW v0.7 SUPERVISED CHECKPOINT

Repository state is authoritative. The supervisor owns ACTIVE.md, checkpoint numbering,
state advancement, evidence binding, checksums, and lifecycle decisions.

HARD RULES
- Do NOT edit ACTIVE.md.
- Do NOT run advance.py or any RSAW state-advancement command.
- Do semantic engineering work for exactly the active task.
- Treat the compiled context below as the default working set.
- Do NOT run broad repository discovery (`rg --files`, `find .`, `tree`, or equivalent)
  unless a specific unresolved question cannot be answered from the envelope.
- Do NOT concatenate multiple long files into one command.
- Keep each tool result bounded. Prefer exact paths, line ranges, counts, hashes, and concise
  summaries; redirect verbose output to an artifact rather than returning it into context.
- Do not re-read unchanged files or ACTIVE.md unless resolving a concrete contradiction.
- Run task-relevant validation.
- Do not expose hidden chain-of-thought.
- semanticCapsuleDelta.evidenceRefs MUST be [] because the supervisor binds authoritative
  evidence handles after the turn.
- Use canonical nextTask keys: id, spec, role.
- Your FINAL MESSAGE must be exactly one JSON object matching rsaw.checkpoint-result.v1.

ACTIVE TASK: {state.task_id}
ROLE: {state.current_role or state.next_role}
CONTEXT MODE: {envelope.mode}
ENVELOPE SHA256: {envelope.sha256}

{envelope.prompt_text()}

FINAL JSON CONTRACT
{{
  "schemaVersion": "rsaw.checkpoint-result.v1",
  "outcome": "PASS|BLOCKED|COMPLETE",
  "summary": "concise factual checkpoint result",
  "changedFiles": ["path"],
  "validations": [{{"command": "...", "status": "PASS|FAIL"}}],
  "artifacts": [{{"path": "...", "sha256": "optional"}}],
  "semanticCapsuleDelta": {{"observedFacts": [], "decisions": [], "excludedHypotheses": [], "evidenceRefs": [], "unresolvedRisks": [], "codeRelations": [], "validationStatus": [], "nextAction": "..."}},
  "nextTask": {{"id": "T-next", "spec": "docs/tasks/T-next.md", "role": "Builder"}},
  "followingTask": null,
  "nextAction": "...",
  "stopCondition": "...",
  "requestedAction": "CONTINUE|COMPACT|ROTATE|PAUSE|COMPLETE",
  "transitionReason": "...",
  "humanGate": ""
}}
"""


def _write_review_manifest''',
    "bounded v0.7 agent prompt",
)

regex_once(
    "src/repo_state_agent/runtime/v6.py",
    r"def _update_active_markdown\(root: Path, state: ActiveState, result: CheckpointResult, decision: GovernorDecision, checkpoint_id: str\) -> None:.*?\n\ndef _checkpoint_result_dict",
    '''def _render_active_markdown(
    root: Path,
    state: ActiveState,
    result: CheckpointResult,
    decision: GovernorDecision,
    checkpoint_id: str,
) -> str:
    text = (root / "ACTIVE.md").read_text(encoding="utf-8")
    next_task = result.next_task
    if decision.action == "COMPLETE":
        continuation = "COMPLETE"
        active_id = state.task_id
        active_spec = state.task_spec.relative_to(root).as_posix()
        role = state.current_role or state.next_role
    else:
        assert next_task is not None
        active_id, active_spec, role = next_task.task_id, next_task.spec, next_task.role
        continuation = (
            "ROTATE_REQUIRED"
            if decision.action == "ROTATE"
            else (
                "STOP_REQUIRED"
                if decision.action == "PAUSE"
                else "CONTINUE_ALLOWED"
            )
        )
    following = result.following_task
    text = _replace_section(
        text, "Context Epoch", f"ID: {state.epoch_id or 'E-v7'}\nRole: {role}"
    )
    text = _replace_section(text, "Active Task", f"ID: {active_id}\nSpec: {active_spec}")
    text = _replace_section(
        text,
        "Required Reads",
        f"- AGENTS.md\n- ACTIVE.md\n- {active_spec}",
    )
    text = _replace_section(text, "Human Gate", result.human_gate or "None.")
    text = _replace_section(
        text,
        "Next Exact Action",
        result.next_action or "Continue from the sealed checkpoint.",
    )
    text = _replace_section(
        text,
        "Stop Condition",
        result.stop_condition or "Task acceptance criteria are satisfied.",
    )
    text = _replace_section(
        text,
        "Continuation Gate",
        f"Decision: {continuation}\nReason: {decision.action}:{decision.reason}; checkpoint={checkpoint_id}",
    )
    if following:
        text = _replace_section(
            text, "Next Task", f"ID: {following.task_id}\nSpec: {following.spec}"
        )
        text = _replace_section(text, "Next Session Role", following.role)
    elif next_task and decision.action != "COMPLETE":
        text = _replace_section(
            text, "Next Task", f"ID: {next_task.task_id}\nSpec: {next_task.spec}"
        )
        text = _replace_section(text, "Next Session Role", next_task.role)
    return canonicalize_active_text(text)


def _update_active_markdown(
    root: Path,
    state: ActiveState,
    result: CheckpointResult,
    decision: GovernorDecision,
    checkpoint_id: str,
) -> None:
    (root / "ACTIVE.md").write_text(
        _render_active_markdown(root, state, result, decision, checkpoint_id),
        encoding="utf-8",
    )


def _checkpoint_result_dict''',
    "canonical ACTIVE renderer",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "def _replace_section(text: str, heading: str, body: str) -> str:\n"
    "    pattern = re.compile(rf\"(^##\\s+{re.escape(heading)}\\s*$\\n)(.*?)(?=^##\\s+|\\Z)\", re.MULTILINE | re.DOTALL | re.IGNORECASE)\n"
    "    replacement = rf\"\\1\\n{body.strip()}\\n\\n\"\n"
    "    if pattern.search(text):\n"
    "        return pattern.sub(replacement, text, count=1)\n"
    "    return text.rstrip() + f\"\\n\\n## {heading}\\n\\n{body.strip()}\\n\"\n",
    "def _replace_section(text: str, heading: str, body: str) -> str:\n"
    "    return replace_active_section(text, heading, body)\n",
    "canonical section replacement",
)
replace_once(
    "src/repo_state_agent/runtime/v6.py",
    "\ndef _extract_json(text: str) -> dict[str, Any]:\n",
    "\ndef _snapshot_file(path: Path) -> bytes | None:\n"
    "    return path.read_bytes() if path.is_file() else None\n"
    "\n\n"
    "def _restore_file(path: Path, snapshot: bytes | None) -> None:\n"
    "    if snapshot is None:\n"
    "        path.unlink(missing_ok=True)\n"
    "        return\n"
    "    path.parent.mkdir(parents=True, exist_ok=True)\n"
    "    path.write_bytes(snapshot)\n"
    "\n\n"
    "def _extract_json(text: str) -> dict[str, Any]:\n",
    "transaction snapshot helpers",
)

print("v0.7 core runtime materialized")
