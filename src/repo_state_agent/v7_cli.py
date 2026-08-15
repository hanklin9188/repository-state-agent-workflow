from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import shutil
import socket
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from . import __version__, cli as legacy_cli
from .active_format import canonicalize_active_text, replace_section
from .parsing import parse_active
from .runtime.codex import CodexAdapter
from .runtime.report import load_runtime_summary
from .runtime.store import atomic_write_json, utc_now
from .runtime.tool_budget import ToolBudget, ToolBudgetGuard
from .runtime.tui.v6 import LiveDashboardV6, preview_v6, should_use_v6_tui
from .runtime.v6 import (
    V6Options,
    _next_checkpoint_index,
    compile_context,
    migrate_v6,
    migrate_v7,
    supervise_v6,
    synthetic_acceptance,
    v6_efficiency_view,
    v6_enabled,
)
from .verify import verify_repository

_SANDBOXES = ("read-only", "workspace-write", "danger-full-access")
_EXPECTED_OPERATOR_STATUSES = {"PAUSED", "COMPLETE", "LIMIT_REACHED", "DRY_RUN"}


def _nonempty_reason(value: str) -> str:
    reason = value.strip()
    if not reason:
        raise argparse.ArgumentTypeError("reason must contain non-whitespace text")
    return reason


def _operator_identity() -> dict[str, Any]:
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    identity: dict[str, Any] = {
        "user": user,
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "python": str(Path(sys.executable).resolve()),
    }
    if hasattr(os, "getuid"):
        identity["uid"] = os.getuid()
    if hasattr(os, "getgid"):
        identity["gid"] = os.getgid()
    return identity


def _json_document_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _snapshot_file(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def _restore_file(path: Path, snapshot: bytes | None) -> None:
    if snapshot is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(snapshot)


def _operator_action_path(root: Path, timestamp: str, suffix: str) -> Path:
    slug = timestamp.replace(":", "").replace("+", "-")
    return root / ".rsaw/state/operator-actions" / f"{slug}-{suffix}.json"


def _write_operator_action(root: Path, *, suffix: str, payload: dict[str, Any]) -> Path:
    timestamp = str(payload.get("timestamp") or utc_now())
    bound = {
        "schemaVersion": "rsaw.operator-action.v2",
        "operator": _operator_identity(),
        **payload,
        "timestamp": timestamp,
    }
    canonical = json.dumps(bound, sort_keys=True, separators=(",", ":")).encode("utf-8")
    bound["contentSha256"] = hashlib.sha256(canonical).hexdigest()
    path = _operator_action_path(root, timestamp, suffix)
    atomic_write_json(path, bound)
    return path


def _root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _path_after_command(argv: list[str], command: str) -> Path:
    try:
        index = argv.index(command)
    except ValueError:
        return Path(".").resolve()
    if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
        return _root(argv[index + 1])
    return Path(".").resolve()


def _load_config(root: Path) -> dict[str, Any]:
    path = root / ".rsaw/config.json"
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(".rsaw/config.json must be an object")
    return value


def _save_config(root: Path, value: dict[str, Any]) -> None:
    atomic_write_json(root / ".rsaw/config.json", value)


def _runtime_config(root: Path) -> dict[str, Any]:
    raw = _load_config(root)
    runtime = raw.get("runtime", {})
    return runtime if isinstance(runtime, dict) else {}


def _codex_profile(
    root: Path,
    *,
    requested_binary: str = "auto",
    requested_sandbox: str = "auto",
    forced_sandbox_task: str | None = None,
) -> dict[str, Any]:
    runtime = _runtime_config(root)
    codex = runtime.get("codex", {})
    if not isinstance(codex, dict):
        codex = {}
    configured_binary = str(codex.get("binary") or runtime.get("codex_binary") or "codex")
    binary = configured_binary if requested_binary == "auto" else requested_binary
    default_sandbox = str(
        codex.get("defaultSandbox") or runtime.get("sandbox") or "workspace-write"
    )
    if default_sandbox not in _SANDBOXES:
        raise ValueError(f"unsupported default sandbox mode: {default_sandbox}")
    raw_overrides = codex.get("taskSandboxOverrides", {})
    if not isinstance(raw_overrides, dict):
        raise ValueError("runtime.codex.taskSandboxOverrides must be an object")
    overrides: dict[str, str] = {}
    for task, mode in raw_overrides.items():
        task_id = str(task).strip()
        sandbox = str(mode).strip()
        if not task_id:
            raise ValueError("task sandbox override has an empty task ID")
        if sandbox not in _SANDBOXES:
            raise ValueError(f"unsupported sandbox for task {task_id}: {sandbox}")
        overrides[task_id] = sandbox
    forced = None if requested_sandbox == "auto" else requested_sandbox
    if forced is not None and forced not in _SANDBOXES:
        raise ValueError(f"unsupported CLI sandbox mode: {forced}")
    return {
        "binary": binary,
        "defaultSandbox": default_sandbox,
        "taskSandboxOverrides": overrides,
        "forcedSandbox": forced,
        "forcedSandboxTask": forced_sandbox_task if forced else None,
    }


def _resolve_profile_sandbox(profile: dict[str, Any], task_id: str) -> tuple[str, str]:
    forced = profile.get("forcedSandbox")
    forced_task = str(profile.get("forcedSandboxTask") or "")
    if forced and task_id == forced_task:
        return str(forced), "CLI task override"
    overrides = profile.get("taskSandboxOverrides", {})
    if isinstance(overrides, dict) and task_id in overrides:
        return str(overrides[task_id]), "task override"
    return str(profile["defaultSandbox"]), "default"


def _resolve_codex_settings(
    root: Path,
    *,
    requested_binary: str = "auto",
    requested_sandbox: str = "auto",
) -> tuple[str, str, str]:
    state = parse_active(root)
    profile = _codex_profile(
        root,
        requested_binary=requested_binary,
        requested_sandbox=requested_sandbox,
        forced_sandbox_task=state.task_id,
    )
    sandbox, source = _resolve_profile_sandbox(profile, state.task_id)
    return str(profile["binary"]), sandbox, source


def _tool_budget(options: V6Options) -> ToolBudget:
    return ToolBudget(
        max_tool_calls_per_turn=options.max_tool_calls_per_turn,
        max_tool_output_tokens=options.max_tool_output_tokens,
        max_single_tool_output_tokens=options.max_single_tool_output_tokens,
        max_broad_discovery_commands=options.max_broad_discovery_commands,
        enforce=options.enforce_tool_budget,
    )


def _installation_view() -> dict[str, Any]:
    try:
        package_version = version("repository-state-agent-workflow")
    except PackageNotFoundError:
        package_version = "unknown"
    launcher = shutil.which("rsaw")
    return {
        "packageVersion": package_version,
        "python": sys.executable,
        "launcher": launcher,
        "launcherMatchesPythonPrefix": bool(
            launcher and Path(launcher).resolve().parent == Path(sys.executable).resolve().parent
        ),
        "moduleFallback": f"{sys.executable} -m repo_state_agent",
    }


def _preflight_payload(
    root: Path,
    *,
    codex_binary: str = "auto",
    sandbox: str = "auto",
) -> dict[str, Any]:
    verification = verify_repository(root)
    state = parse_active(root)
    options = V6Options.from_root(root)
    profile = _codex_profile(
        root,
        requested_binary=codex_binary,
        requested_sandbox=sandbox,
        forced_sandbox_task=state.task_id,
    )
    resolved_sandbox, sandbox_source = _resolve_profile_sandbox(profile, state.task_id)
    binary = str(profile["binary"])
    adapter = CodexAdapter(
        binary=binary,
        sandbox=str(profile["defaultSandbox"]),
        task_sandbox_overrides=dict(profile["taskSandboxOverrides"]),
        forced_sandbox=profile.get("forcedSandbox"),
        forced_sandbox_task=profile.get("forcedSandboxTask"),
        quiet=True,
    )
    doctor = adapter.doctor()
    if verification.ok and doctor.ok and not state.human_gate:
        status = "READY"
    elif state.human_gate and verification.ok and doctor.ok:
        status = "PAUSED"
    else:
        status = "FAILED"
    return {
        "status": status,
        "repository": str(root),
        "task": state.task_id,
        "role": state.current_role or state.next_role,
        "checkpoint": _next_checkpoint_index(root),
        "humanGate": state.human_gate or None,
        "continuation": state.continuation,
        "repositoryVerification": {
            "ok": verification.ok,
            "errors": verification.errors,
            "warnings": verification.warnings,
        },
        "codex": {
            **doctor.to_dict(),
            "requestedBinary": codex_binary,
            "resolvedSandbox": resolved_sandbox,
            "sandboxSource": sandbox_source,
            "sandboxPolicy": ("task-scoped CLI" if profile.get("forcedSandbox") else "task-aware"),
            "taskSandboxOverrideCount": len(profile["taskSandboxOverrides"]),
        },
        "toolBudget": _tool_budget(options).__dict__,
        "installation": _installation_view(),
    }


def _migrate(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw migrate")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--to", default="0.7", choices=["0.6", "0.7"])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fn = migrate_v7 if args.to == "0.7" else migrate_v6
    result = fn(_root(args.path), apply=args.apply)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("APPLY" if args.apply else "PLAN")
        for key, value in result.items():
            print(f"{key:30} {value}")
    return 0


def _upgrade(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw upgrade")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    forwarded = [args.path, "--to", "0.7"]
    if args.apply:
        forwarded.append("--apply")
    if args.json:
        forwarded.append("--json")
    return _migrate(forwarded)


def _compile(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw compile")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument(
        "--mode",
        choices=["FRESH", "CONTINUE", "COMPACT", "REVIEW", "RECOVERY"],
        default="FRESH",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show-content", action="store_true")
    args = parser.parse_args(argv)
    root = _root(args.path)
    try:
        envelope = compile_context(root, mode=args.mode)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    payload = envelope.to_dict()
    if not args.show_content:
        for component in payload["components"]:
            component.pop("content", None)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"MODE               {envelope.mode}")
        print(f"ROLE               {envelope.role}")
        print(f"TASK               {envelope.task_id}")
        print(f"ENVELOPE TOKENS    {envelope.total_tokens}")
        print(f"CAPSULE TOKENS     {envelope.capsule_tokens}")
        print(f"EXACT EVIDENCE     {envelope.exact_evidence_tokens}")
        print(f"REPEATED INPUT     {envelope.repeated_input_tokens}")
        print(f"EVIDENCE RESEND    {envelope.evidence_resend_tokens}")
        print(f"SHA256             {envelope.sha256}")
        for warning in envelope.warnings:
            print(f"WARNING: {warning}")
    return 0


def _acceptance(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw acceptance")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--horizon", choices=["4", "16", "64", "all"], default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    horizons = [4, 16, 64] if args.horizon == "all" else [int(args.horizon)]
    results = [synthetic_acceptance(_root(args.path), value) for value in horizons]
    ok = all(bool(row["pass"]) for row in results)
    if args.json:
        print(json.dumps({"ok": ok, "results": results}, indent=2))
    else:
        print("PASS" if ok else "FAIL")
        for row in results:
            print(
                f"{row['checkpoints']:>2} checkpoints  continue={row['continues']}  "
                f"compact={row['compactions']}  rotate={row['rotations']}  "
                f"relay={row['manualRelay']}"
            )
    return 0 if ok else 1


def _preflight(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw preflight")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--codex-bin", default="auto")
    parser.add_argument("--sandbox", default="auto", choices=["auto", *_SANDBOXES])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = _preflight_payload(
        _root(args.path),
        codex_binary=args.codex_bin,
        sandbox=args.sandbox,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"STATUS              {payload['status']}")
        print(f"TASK                {payload['task']}")
        print(f"ROLE                {payload['role']}")
        print(f"CHECKPOINT          {payload['checkpoint']}")
        print(f"SANDBOX             {payload['codex']['resolvedSandbox']}")
        print(f"CODEX               {payload['codex']['binary']}")
        print(f"REPOSITORY VERIFY   {payload['repositoryVerification']['ok']}")
        print(f"HUMAN GATE          {payload['humanGate'] or 'none'}")
        installation = payload["installation"]
        if not installation["launcherMatchesPythonPrefix"]:
            print(
                "WARNING: rsaw launcher and active Python environment differ; "
                f"use `{installation['moduleFallback']}` or reinstall in this environment"
            )
        for error in payload["repositoryVerification"]["errors"]:
            print(f"ERROR: {error}")
        for error in payload["codex"]["errors"]:
            print(f"ERROR: {error}")
    return 0 if payload["status"] in {"READY", "PAUSED"} else 1


def _run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw run")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--agent", choices=["codex"], default="codex")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--strict-exit-codes", action="store_true")
    tui = parser.add_mutually_exclusive_group()
    tui.add_argument("--tui", action="store_true")
    tui.add_argument("--no-tui", action="store_true")
    parser.add_argument("--codex-bin", default="auto")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--sandbox", default="auto", choices=["auto", *_SANDBOXES])
    parser.add_argument("--approve-for-me", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print(f"ERROR: unsupported v0.7 run options: {' '.join(unknown)}", file=sys.stderr)
        return 2

    root = _root(args.path)
    options = V6Options.from_root(root, quiet=args.quiet, dry_run=args.dry_run)
    state = parse_active(root)
    profile = _codex_profile(
        root,
        requested_binary=args.codex_bin,
        requested_sandbox=args.sandbox,
        forced_sandbox_task=state.task_id,
    )
    sandbox, sandbox_source = _resolve_profile_sandbox(profile, state.task_id)
    binary = str(profile["binary"])
    use_tui = should_use_v6_tui(
        force=args.tui,
        disable=args.no_tui,
        json_output=args.json,
        quiet=args.quiet,
        dry_run=args.dry_run,
    )
    dashboard = (
        LiveDashboardV6(
            root,
            tool_call_limit=options.max_tool_calls_per_turn,
            tool_output_limit=options.max_tool_output_tokens,
        )
        if use_tui
        else None
    )
    guard = ToolBudgetGuard(
        _tool_budget(options),
        event_sink=dashboard.handle_supervisor_event if dashboard else None,
    )
    adapter = CodexAdapter(
        binary=binary,
        model=args.model,
        profile=args.profile,
        sandbox=str(profile["defaultSandbox"]),
        task_sandbox_overrides=dict(profile["taskSandboxOverrides"]),
        forced_sandbox=profile.get("forcedSandbox"),
        forced_sandbox_task=profile.get("forcedSandboxTask"),
        approve_for_me=args.approve_for_me,
        quiet=bool(args.quiet or dashboard),
        event_sink=dashboard.handle_codex_event if dashboard else None,
        event_guard=guard.observe,
    )
    if dashboard:
        with dashboard:
            result = supervise_v6(
                root,
                adapter,
                options,
                event_sink=dashboard.handle_supervisor_event,
            )
            dashboard.finalize(result.status, result.reason)
    else:
        result = supervise_v6(root, adapter, options)

    payload = {
        "status": result.status,
        "reason": result.reason,
        "run_id": result.run_id,
        "summary_path": (
            str(result.summary_path.relative_to(root)) if result.summary_path else None
        ),
        "exit_code": result.exit_code,
        "runtime": f"v{__version__}",
        "sandbox": sandbox,
        "sandbox_source": sandbox_source,
        "sandbox_policy": ("task-scoped CLI" if profile.get("forcedSandbox") else "task-aware"),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif not dashboard:
        print(f"RSAW {result.status}: {result.reason}")
        if result.summary_path:
            print(f"Summary: {result.summary_path}")

    if not args.strict_exit_codes and result.status in _EXPECTED_OPERATOR_STATUSES:
        return 0
    return result.exit_code


def _start(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw start")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--codex-bin", default="auto")
    parser.add_argument("--sandbox", default="auto", choices=["auto", *_SANDBOXES])
    parser.add_argument("--no-tui", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    args = parser.parse_args(argv)
    root = _root(args.path)
    preflight = _preflight_payload(
        root,
        codex_binary=args.codex_bin,
        sandbox=args.sandbox,
    )
    if preflight["status"] == "FAILED":
        print(json.dumps(preflight, indent=2))
        return 1
    if preflight["status"] == "PAUSED":
        print(f"RSAW PAUSED: {preflight['humanGate']}")
        return 0
    forwarded = [args.path, "--agent", "codex", "--codex-bin", args.codex_bin]
    forwarded.extend(["--sandbox", args.sandbox])
    if args.no_tui:
        forwarded.append("--no-tui")
    else:
        forwarded.append("--tui")
    if args.model:
        forwarded.extend(["--model", args.model])
    if args.profile:
        forwarded.extend(["--profile", args.profile])
    return _run(forwarded)


def _report(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw report")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--run-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = _root(args.path)
    try:
        summary = load_runtime_summary(root, args.run_id)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if "model_calls" not in summary:
        delegated = ["report", args.path]
        if args.run_id:
            delegated.extend(["--run-id", args.run_id])
        if args.json:
            delegated.append("--json")
        return legacy_cli.main(delegated)
    view = v6_efficiency_view(summary)
    if args.json:
        print(json.dumps(view, indent=2))
        return 0
    print(f"RUN                  {view.get('run_id')}")
    print(f"STATUS               {view.get('status')} ({view.get('reason')})")
    print(f"CHECKPOINTS          {view.get('checkpoints_observed')}")
    print(f"MODEL CALLS          {view.get('model_calls')}")
    print(f"TOOL CALLS           {view.get('tool_calls')}")
    print(f"TOOL OUTPUT          {view.get('tool_output_tokens')}")
    print(f"BROAD DISCOVERY      {view.get('recovery_rediscovery_commands')}")
    print(f"BUDGET ABORTS        {view.get('tool_budget_aborts')}")
    print(f"FRESH CONTEXTS       {view.get('fresh_contexts')}")
    print(f"COMPACTIONS          {view.get('context_compactions')}")
    print(f"ROLE ROTATIONS       {view.get('role_rotations')}")
    print(f"INPUT / SUCCESS      {view.get('input_tokens_per_successful_checkpoint')}")
    print(f"CACHED / SUCCESS     {view.get('cached_input_tokens_per_successful_checkpoint')}")
    print(f"FRESH / SUCCESS      {view.get('fresh_input_tokens_per_successful_checkpoint')}")
    print(f"REPEATED INPUT       {view.get('repeated_input_tokens')}")
    print(f"EVIDENCE RESEND      {view.get('evidence_resend_tokens')}")
    print(f"MEAN OCCUPANCY       {view.get('mean_context_occupancy')}")
    return 0


def _preview(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw preview")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--seconds", type=float, default=7.0)
    args = parser.parse_args(argv)
    preview_v6(_root(args.path), seconds=args.seconds)
    return 0


def _state(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw state")
    sub = parser.add_subparsers(dest="action", required=True)
    normalize = sub.add_parser("normalize")
    normalize.add_argument("path", nargs="?", default=".")
    normalize.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = _root(args.path)
    path = root / "ACTIVE.md"
    before = path.read_text(encoding="utf-8")
    after = canonicalize_active_text(before)
    changed = before != after
    if changed:
        path.write_text(after, encoding="utf-8")
    verification = verify_repository(root)
    if not verification.ok:
        path.write_text(before, encoding="utf-8")
        print("ERROR: normalization would leave repository invalid", file=sys.stderr)
        for error in verification.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    payload = {
        "status": "NORMALIZED" if changed else "UNCHANGED",
        "lines": len(after.splitlines()),
        "sha256": hashlib.sha256(after.encode("utf-8")).hexdigest(),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{payload['status']}: ACTIVE.md ({payload['lines']} lines)")
    return 0


def _gate(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw gate")
    sub = parser.add_subparsers(dest="action", required=True)
    show = sub.add_parser("show")
    show.add_argument("path", nargs="?", default=".")
    show.add_argument("--json", action="store_true")
    clear = sub.add_parser("clear")
    clear.add_argument("path", nargs="?", default=".")
    clear.add_argument("--reason", required=True, type=_nonempty_reason)
    clear.add_argument("--yes", action="store_true")
    clear.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = _root(args.path)
    state = parse_active(root)
    if args.action == "show":
        payload = {
            "humanGate": state.human_gate or None,
            "continuation": state.continuation,
            "reason": state.continuation_reason,
        }
        print(json.dumps(payload, indent=2) if args.json else payload)
        return 0
    if not args.yes:
        print("ERROR: gate clear requires --yes", file=sys.stderr)
        return 2

    active_path = root / "ACTIVE.md"
    before = active_path.read_bytes()
    before_text = before.decode("utf-8")
    text = replace_section(before_text, "Human Gate", "None.")
    current_role = (state.current_role or "").strip().lower()
    next_role = (state.next_role or state.current_role or "").strip().lower()
    continuation = (
        "ROTATE_REQUIRED"
        if current_role and next_role and current_role != next_role
        else "CONTINUE_ALLOWED"
    )
    text = replace_section(
        text,
        "Continuation Gate",
        (f"Decision: {continuation}\nReason: OPERATOR_GATE_CLEARED:{args.reason.strip()}"),
    )
    if "## Blockers" in text:
        text = replace_section(text, "Blockers", "None.")
    text = text.replace("Human Gate active", "Human Gate cleared")
    after_text = canonicalize_active_text(text)
    after = after_text.encode("utf-8")
    action_path: Path | None = None
    try:
        active_path.write_bytes(after)
        verification = verify_repository(root)
        if not verification.ok:
            raise RuntimeError(
                "gate clear would leave repository invalid: " + ";".join(verification.errors)
            )
        action_path = _write_operator_action(
            root,
            suffix="gate-clear",
            payload={
                "action": "CLEAR_HUMAN_GATE",
                "reason": args.reason.strip(),
                "task": state.task_id,
                "beforeSha256": _sha256_bytes(before),
                "afterSha256": _sha256_bytes(after),
                "continuation": continuation,
                "timestamp": utc_now(),
            },
        )
    except Exception as exc:
        active_path.write_bytes(before)
        if action_path is not None:
            action_path.unlink(missing_ok=True)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "status": "CLEARED",
        "task": state.task_id,
        "reason": args.reason.strip(),
        "audit": action_path.relative_to(root).as_posix(),
    }
    print(json.dumps(payload, indent=2) if args.json else "Human Gate cleared")
    return 0


def _sandbox(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw sandbox")
    sub = parser.add_subparsers(dest="action", required=True)
    show = sub.add_parser("show")
    show.add_argument("path", nargs="?", default=".")
    show.add_argument("--json", action="store_true")
    set_parser = sub.add_parser("set")
    set_parser.add_argument("path", nargs="?", default=".")
    set_parser.add_argument("--task", default="current")
    set_parser.add_argument("--mode", choices=_SANDBOXES, required=True)
    set_parser.add_argument("--reason", required=True, type=_nonempty_reason)
    set_parser.add_argument("--yes", action="store_true")
    set_parser.add_argument("--json", action="store_true")
    clear = sub.add_parser("clear")
    clear.add_argument("path", nargs="?", default=".")
    clear.add_argument("--task", default="current")
    clear.add_argument("--reason", required=True, type=_nonempty_reason)
    clear.add_argument("--yes", action="store_true")
    clear.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = _root(args.path)
    state = parse_active(root)
    if args.action == "show":
        binary, sandbox, source = _resolve_codex_settings(root)
        payload = {
            "task": state.task_id,
            "binary": binary,
            "sandbox": sandbox,
            "source": source,
        }
        print(json.dumps(payload, indent=2) if args.json else payload)
        return 0
    if not args.yes:
        print("ERROR: sandbox changes require --yes", file=sys.stderr)
        return 2

    task = state.task_id if args.task == "current" else args.task.strip()
    if not task:
        print("ERROR: sandbox task ID must not be empty", file=sys.stderr)
        return 2
    config_path = root / ".rsaw/config.json"
    before = _snapshot_file(config_path)
    config = _load_config(root)
    runtime = config.setdefault("runtime", {})
    if not isinstance(runtime, dict):
        print("ERROR: runtime configuration must be an object", file=sys.stderr)
        return 1
    codex = runtime.setdefault("codex", {})
    if not isinstance(codex, dict):
        print("ERROR: runtime.codex must be an object", file=sys.stderr)
        return 1
    overrides = codex.setdefault("taskSandboxOverrides", {})
    if not isinstance(overrides, dict):
        print("ERROR: taskSandboxOverrides must be an object", file=sys.stderr)
        return 1
    before_mode = overrides.get(task)
    if args.action == "set":
        overrides[task] = args.mode
        status = "SET"
        suffix = "sandbox-set"
        action = "SET_TASK_SANDBOX"
    else:
        overrides.pop(task, None)
        status = "CLEARED"
        suffix = "sandbox-clear"
        action = "CLEAR_TASK_SANDBOX"
    after_bytes = _json_document_bytes(config)
    action_path: Path | None = None
    try:
        _save_config(root, config)
        _codex_profile(root)
        verification = verify_repository(root)
        if not verification.ok:
            raise RuntimeError(
                "sandbox change would leave repository invalid: " + ";".join(verification.errors)
            )
        action_path = _write_operator_action(
            root,
            suffix=suffix,
            payload={
                "action": action,
                "reason": args.reason.strip(),
                "task": task,
                "beforeSandbox": before_mode,
                "afterSandbox": overrides.get(task),
                "beforeConfigSha256": (_sha256_bytes(before) if before is not None else None),
                "afterConfigSha256": _sha256_bytes(after_bytes),
                "timestamp": utc_now(),
            },
        )
    except Exception as exc:
        _restore_file(config_path, before)
        if action_path is not None:
            action_path.unlink(missing_ok=True)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    payload = {
        "status": status,
        "task": task,
        "sandbox": overrides.get(task),
        "reason": args.reason.strip(),
        "audit": action_path.relative_to(root).as_posix(),
    }
    print(json.dumps(payload, indent=2) if args.json else payload)
    return 0


def _help() -> int:
    print(
        f"""Repository-State Agent Workflow (RSAW) v{__version__}

Daily use:
  rsaw start .                     preflight + supervised Codex + live TUI
  rsaw preflight .                 verify repository, Codex, sandbox, and budgets
  rsaw status .                    show active task
  rsaw report .                    show runtime efficiency

Operator controls:
  rsaw gate show .
  rsaw gate clear . --reason \"prerequisite restored\" --yes
  rsaw sandbox show .
  rsaw sandbox set . --task current --mode danger-full-access --reason "reviewed GPU boundary" --yes
  rsaw sandbox clear . --task current --reason "boundary closed" --yes
  rsaw state normalize .

Runtime / migration:
  rsaw upgrade . --apply
  rsaw migrate . --to 0.7 --apply
  rsaw compile . --mode FRESH
  rsaw run . --agent codex
  rsaw acceptance . --horizon all
  rsaw preview .

Legacy commands such as init, verify, status, next, footprint, archive, checkpoint,
prompt, doctor, context, and report remain available.
"""
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        return _help()
    if args[0] in {"-V", "--version", "version"}:
        print(f"RSAW {__version__}")
        return 0
    command = args[0]
    rest = args[1:]
    if command == "migrate":
        return _migrate(rest)
    if command == "upgrade":
        return _upgrade(rest)
    if command == "compile":
        return _compile(rest)
    if command == "acceptance":
        return _acceptance(rest)
    if command in {"preview", "preview-v6"}:
        return _preview(rest)
    if command == "preflight":
        return _preflight(rest)
    if command == "start":
        return _start(rest)
    if command == "gate":
        return _gate(rest)
    if command == "sandbox":
        return _sandbox(rest)
    if command == "state":
        return _state(rest)
    if command == "report":
        root = _path_after_command(args, "report")
        if v6_enabled(root):
            return _report(rest)
        return legacy_cli.main(args)
    if command == "run":
        root = _path_after_command(args, "run")
        if v6_enabled(root):
            return _run(rest)
        return legacy_cli.main(args)
    return legacy_cli.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
