from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import cli as legacy_cli
from .runtime.codex import CodexAdapter
from .runtime.report import load_runtime_summary
from .runtime.tui.v6 import LiveDashboardV6, preview_v6, should_use_v6_tui
from .runtime.v6 import (
    V6Options,
    compile_context,
    migrate_v6,
    supervise_v6,
    synthetic_acceptance,
    v6_efficiency_view,
    v6_enabled,
)


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


def _migrate(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw migrate")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--to", default="0.6", choices=["0.6"])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = migrate_v6(_root(args.path), apply=args.apply)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("APPLY" if args.apply else "PLAN")
        for key, value in result.items():
            print(f"{key:30} {value}")
    return 0


def _compile(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw compile")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--mode", choices=["FRESH", "CONTINUE", "COMPACT", "REVIEW", "RECOVERY"], default="FRESH")
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
                f"compact={row['compactions']}  rotate={row['rotations']}  relay={row['manualRelay']}"
            )
    return 0 if ok else 1


def _run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="rsaw run")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--agent", choices=["codex"], default="codex")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    tui = parser.add_mutually_exclusive_group()
    tui.add_argument("--tui", action="store_true")
    tui.add_argument("--no-tui", action="store_true")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--sandbox", default="workspace-write")
    parser.add_argument("--approve-for-me", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print(f"ERROR: unsupported v0.6 run options: {' '.join(unknown)}", file=sys.stderr)
        return 2
    root = _root(args.path)
    options = V6Options.from_root(root, quiet=args.quiet, dry_run=args.dry_run)
    use_tui = should_use_v6_tui(force=args.tui, disable=args.no_tui, json_output=args.json, quiet=args.quiet, dry_run=args.dry_run)
    dashboard = LiveDashboardV6(root) if use_tui else None
    adapter = CodexAdapter(
        binary=args.codex_bin,
        model=args.model,
        profile=args.profile,
        sandbox=args.sandbox,
        approve_for_me=args.approve_for_me,
        quiet=bool(args.quiet or dashboard),
        event_sink=dashboard.handle_codex_event if dashboard else None,
    )
    if dashboard:
        with dashboard:
            result = supervise_v6(root, adapter, options, event_sink=dashboard.handle_supervisor_event)
            dashboard.finalize(result.status, result.reason)
    else:
        result = supervise_v6(root, adapter, options)
    payload = {
        "status": result.status,
        "reason": result.reason,
        "run_id": result.run_id,
        "summary_path": str(result.summary_path.relative_to(root)) if result.summary_path else None,
        "exit_code": result.exit_code,
        "runtime": "v0.6",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif not dashboard:
        print(f"RSAW {result.status}: {result.reason}")
        if result.summary_path:
            print(f"Summary: {result.summary_path}")
    return result.exit_code


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
    parser = argparse.ArgumentParser(prog="rsaw preview-v6")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--seconds", type=float, default=7.0)
    args = parser.parse_args(argv)
    preview_v6(_root(args.path), seconds=args.seconds)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return legacy_cli.main(args)
    command = args[0]
    rest = args[1:]
    if command == "migrate":
        return _migrate(rest)
    if command == "compile":
        return _compile(rest)
    if command == "acceptance":
        return _acceptance(rest)
    if command == "preview-v6":
        return _preview(rest)
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
