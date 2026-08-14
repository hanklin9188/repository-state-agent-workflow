from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from .archive import archive_active
from .continuation import decide_continuation
from .footprint import measure_bootstrap
from .model import ActiveState
from .parsing import parse_active
from .prompts import VALID_MODES, VALID_ROLES, render_prompt
from .runtime.codex import CodexAdapter
from .runtime.config import RuntimeConfig, load_runtime_config
from .runtime.report import efficiency_view, load_runtime_summary
from .runtime.supervisor import options_from_config, supervise
from .scaffold import initialize_repository
from .verify import verify_repository


def _root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def cmd_init(args: argparse.Namespace) -> int:
    created, skipped = initialize_repository(_root(args.path), force=args.force)
    for path in created:
        print(f"CREATE {path}")
    for path in skipped:
        print(f"SKIP   {path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify_repository(_root(args.path), args.max_lines, args.max_bytes)
    payload = {"ok": result.ok, "errors": result.errors, "warnings": result.warnings}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PASS" if result.ok else "FAIL")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.ok else 1


def cmd_footprint(args: argparse.Namespace) -> int:
    root = _root(args.path)
    rows = measure_bootstrap(root, include_required=not args.base_only)
    total = {
        "lines": sum(row.lines for row in rows),
        "bytes": sum(row.bytes for row in rows),
        "chars": sum(row.chars for row in rows),
        "approx_tokens": sum(row.approx_tokens for row in rows),
    }
    if args.json:
        print(
            json.dumps(
                {
                    "files": [
                        {
                            "path": str(row.path.relative_to(root)),
                            "lines": row.lines,
                            "bytes": row.bytes,
                            "chars": row.chars,
                            "approx_tokens": row.approx_tokens,
                        }
                        for row in rows
                    ],
                    "total": total,
                    "token_estimate": "approximate chars/4",
                },
                indent=2,
            )
        )
    else:
        print(f"{'PATH':50} {'LINES':>7} {'BYTES':>9} {'TOKENS~':>9}")
        for row in rows:
            rel = str(row.path.relative_to(root))
            print(f"{rel:50} {row.lines:7d} {row.bytes:9d} {row.approx_tokens:9d}")
        print("-" * 79)
        print(
            f"{'TOTAL':50} {total['lines']:7d} {total['bytes']:9d} "
            f"{total['approx_tokens']:9d}"
        )
        print("Token estimate is approximate: UTF-8 text characters / 4.")
    if args.max_tokens is not None and total["approx_tokens"] > args.max_tokens:
        return 1
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    target = archive_active(_root(args.path), args.label)
    print(target)
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    root = _root(args.path)
    state = parse_active(root)
    label = args.label or f"{state.task_id or 'task'}-checkpoint"
    target = archive_active(root, label)
    print(target)
    return 0


def _state_payload(root: Path) -> dict[str, object]:
    state = parse_active(root)
    decision = decide_continuation(state)
    return {
        "workstream": state.workstream_id or None,
        "workstream_spec": (
            str(state.workstream_spec.relative_to(root)) if state.workstream_spec else None
        ),
        "epoch": state.epoch_id or None,
        "current_role": state.current_role or None,
        "active_task": state.task_id,
        "active_task_spec": str(state.task_spec.relative_to(root)),
        "declared_continuation": state.continuation,
        "runtime_action": decision.action,
        "continuation_reasons": list(decision.reasons),
        "next_task": state.next_task_id or None,
        "next_task_spec": (
            str(state.next_task_spec.relative_to(root)) if state.next_task_spec else None
        ),
        "next_role": state.next_role,
        "human_gate": state.human_gate or None,
        "next_action": state.next_action,
        "stop_condition": state.stop_condition,
    }


def cmd_status(args: argparse.Namespace) -> int:
    root = _root(args.path)
    payload = _state_payload(root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"WORKSTREAM  {payload['workstream'] or 'classic'}")
        print(f"EPOCH       {payload['epoch'] or 'fresh-task'}")
        print(f"ROLE        {payload['current_role'] or payload['next_role']}")
        print(f"TASK        {payload['active_task']} ({payload['active_task_spec']})")
        print(f"ACTION      {payload['runtime_action']}")
        print(f"REASON      {', '.join(payload['continuation_reasons'])}")
        print(f"NEXT TASK   {payload['next_task'] or '-'}")
        print(f"NEXT ROLE   {payload['next_role']}")
        print(f"HUMAN GATE  {payload['human_gate'] or 'none'}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    root = _root(args.path)
    payload = _state_payload(root)
    result = {
        "action": payload["runtime_action"],
        "declared_decision": payload["declared_continuation"],
        "reasons": payload["continuation_reasons"],
        "next_task": payload["next_task"],
        "next_task_spec": payload["next_task_spec"],
        "next_role": payload["next_role"],
        "human_gate": payload["human_gate"],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["action"])
        print(f"Reason: {', '.join(result['reasons'])}")
        if result["next_task"]:
            print(f"Next task: {result['next_task']} ({result['next_task_spec']})")
        print(f"Next role: {result['next_role']}")
        if result["human_gate"]:
            print(f"Human gate: {result['human_gate']}")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    print(render_prompt(_root(args.path), args.role, args.mode))
    return 0


def _codex_adapter(args: argparse.Namespace, config: RuntimeConfig) -> CodexAdapter:
    return CodexAdapter(
        binary=args.codex_bin or config.codex_binary,
        model=args.model if args.model is not None else config.model,
        profile=args.profile if args.profile is not None else config.profile,
        sandbox=args.sandbox or config.sandbox,
        approve_for_me=bool(args.approve_for_me or config.approve_for_me),
        quiet=bool(getattr(args, "quiet", False)),
    )


def cmd_doctor(args: argparse.Namespace) -> int:
    root = _root(args.path)
    config = load_runtime_config(root)
    adapter = _codex_adapter(args, config)
    result = adapter.doctor()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("PASS" if result.ok else "FAIL")
        print(f"Adapter: {result.adapter}")
        print(f"Binary: {result.binary}")
        print(f"Version: {result.version or 'unknown'}")
        if result.capabilities:
            print(f"Capabilities: {', '.join(result.capabilities)}")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.ok else 1


def _interactive_gate(state: ActiveState) -> str | None:
    print("\nRSAW WORKSTREAM PAUSED")
    print(f"Human gate: {state.human_gate or 'unspecified'}")
    print(f"Task: {state.task_id}")
    print("Enter the exact human response for the repository gate.")
    print("Use :quit to leave the supervisor without changing repository state.")
    response = input("rsaw> ").strip()
    if not response or response == ":quit":
        return None
    return response


def cmd_run(args: argparse.Namespace) -> int:
    root = _root(args.path)
    config = load_runtime_config(root)
    config = replace(
        config,
        codex_binary=args.codex_bin or config.codex_binary,
        model=args.model if args.model is not None else config.model,
        profile=args.profile if args.profile is not None else config.profile,
        sandbox=args.sandbox or config.sandbox,
        approve_for_me=bool(args.approve_for_me or config.approve_for_me),
        max_transitions=args.max_transitions or config.max_transitions,
        max_turns_per_epoch=args.max_turns_per_epoch or config.max_turns_per_epoch,
        rotate_input_tokens=(
            args.rotate_input_tokens
            if args.rotate_input_tokens is not None
            else config.rotate_input_tokens
        ),
        max_total_input_tokens=(
            args.max_total_input_tokens
            if args.max_total_input_tokens is not None
            else config.max_total_input_tokens
        ),
        wait_on_pause=bool(args.wait_on_pause or config.wait_on_pause),
    )
    adapter = _codex_adapter(args, config)
    options = options_from_config(config, dry_run=args.dry_run, quiet=args.quiet)
    interactive = (
        not args.no_interactive_gates
        and config.interactive_gates
        and sys.stdin.isatty()
        and not args.dry_run
    )
    result = supervise(
        root,
        adapter,
        options,
        gate_resolver=_interactive_gate if interactive else None,
    )
    payload = {
        "status": result.status,
        "reason": result.reason,
        "run_id": result.run_id,
        "summary_path": (
            str(result.summary_path.relative_to(root)) if result.summary_path else None
        ),
        "exit_code": result.exit_code,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"RSAW {result.status}: {result.reason}")
        if result.summary_path:
            print(f"Summary: {result.summary_path}")
    return result.exit_code


def cmd_report(args: argparse.Namespace) -> int:
    root = _root(args.path)
    try:
        summary = load_runtime_summary(root, args.run_id)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    view = efficiency_view(summary)
    if args.json:
        print(json.dumps(view, indent=2))
    else:
        print(f"RUN          {view['run_id']}")
        print(f"STATUS       {view['status']} ({view['reason']})")
        print(f"WORKSTREAM   {view['workstream']}")
        print(f"TURNS        {view['agent_turns']}")
        print(f"EPOCHS       {view['runtime_epochs']}")
        print(f"FRESH/RESUME {view['fresh_turns']}/{view['resumed_turns']}")
        print(f"CHECKPOINTS  {view['checkpoints_observed']}")
        print(f"INPUT TOKENS {view['usage'].get('input_tokens', 0)}")
        print(f"CACHED INPUT {view['usage'].get('cached_input_tokens', 0)}")
        print(f"OUTPUT       {view['usage'].get('output_tokens', 0)}")
        print(f"TOKENS/CLOSE {view['input_tokens_per_checkpoint']}")
    return 0


def _add_codex_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--codex-bin")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--sandbox")
    parser.add_argument("--approve-for-me", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rsaw", description="Repository-State Agent Workflow"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a plug-and-play RSAW workstream")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    verify = sub.add_parser("verify", help="Verify ACTIVE.md and its references")
    verify.add_argument("path", nargs="?", default=".")
    verify.add_argument("--max-lines", type=int, default=140)
    verify.add_argument("--max-bytes", type=int, default=12_288)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=cmd_verify)

    status = sub.add_parser("status", help="Show the active workstream, task, and action")
    status.add_argument("path", nargs="?", default=".")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    next_cmd = sub.add_parser("next", help="Evaluate the next runtime action")
    next_cmd.add_argument("path", nargs="?", default=".")
    next_cmd.add_argument("--json", action="store_true")
    next_cmd.set_defaults(func=cmd_next)

    footprint = sub.add_parser("footprint", help="Estimate bootstrap context footprint")
    footprint.add_argument("path", nargs="?", default=".")
    footprint.add_argument("--base-only", action="store_true")
    footprint.add_argument("--max-tokens", type=int)
    footprint.add_argument("--json", action="store_true")
    footprint.set_defaults(func=cmd_footprint)

    archive = sub.add_parser("archive", help="Archive ACTIVE.md")
    archive.add_argument("path", nargs="?", default=".")
    archive.add_argument("--label", required=True)
    archive.set_defaults(func=cmd_archive)

    checkpoint = sub.add_parser("checkpoint", help="Archive the current handoff checkpoint")
    checkpoint.add_argument("path", nargs="?", default=".")
    checkpoint.add_argument("--label")
    checkpoint.set_defaults(func=cmd_checkpoint)

    prompt = sub.add_parser("prompt", help="Render the active minimal prompt")
    prompt.add_argument("path", nargs="?", default=".")
    prompt.add_argument("--role", choices=sorted(VALID_ROLES))
    prompt.add_argument("--mode", choices=sorted(VALID_MODES), default="auto")
    prompt.set_defaults(func=cmd_prompt)

    doctor = sub.add_parser("doctor", help="Check runtime adapter compatibility")
    doctor.add_argument("path", nargs="?", default=".")
    doctor.add_argument("--agent", choices=["codex"], default="codex")
    doctor.add_argument("--json", action="store_true")
    _add_codex_options(doctor)
    doctor.set_defaults(func=cmd_doctor)

    run = sub.add_parser("run", help="Supervise a long-lived workstream")
    run.add_argument("path", nargs="?", default=".")
    run.add_argument("--agent", choices=["codex"], default="codex")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--json", action="store_true")
    run.add_argument("--quiet", action="store_true")
    run.add_argument("--no-interactive-gates", action="store_true")
    run.add_argument("--wait-on-pause", action="store_true")
    run.add_argument("--max-transitions", type=int)
    run.add_argument("--max-turns-per-epoch", type=int)
    run.add_argument("--rotate-input-tokens", type=int)
    run.add_argument("--max-total-input-tokens", type=int)
    _add_codex_options(run)
    run.set_defaults(func=cmd_run)

    report = sub.add_parser("report", help="Report measured runtime token and transition data")
    report.add_argument("path", nargs="?", default=".")
    report.add_argument("--run-id")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
