from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import archive_active
from .continuation import decide_continuation
from .footprint import measure_bootstrap
from .parsing import parse_active
from .prompts import VALID_MODES, VALID_ROLES, render_prompt
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
        "continuation": state.continuation,
        "continuation_action": decision.action,
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
        print(f"GATE        {payload['continuation_action']}")
        print(f"REASON      {', '.join(payload['continuation_reasons'])}")
        print(f"NEXT TASK   {payload['next_task'] or '-'}")
        print(f"NEXT ROLE   {payload['next_role']}")
        print(f"HUMAN GATE  {payload['human_gate'] or 'none'}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    root = _root(args.path)
    payload = _state_payload(root)
    result = {
        "action": payload["continuation_action"],
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

    status = sub.add_parser("status", help="Show the active workstream, task, and gate")
    status.add_argument("path", nargs="?", default=".")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    next_cmd = sub.add_parser("next", help="Evaluate the continuation gate")
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
