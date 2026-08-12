from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import archive_active
from .footprint import measure_bootstrap
from .prompts import render_prompt
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


def cmd_prompt(args: argparse.Namespace) -> int:
    print(render_prompt(_root(args.path), args.role))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rsaw", description="Repository-State Agent Workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize workflow files")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    verify = sub.add_parser("verify", help="Verify ACTIVE.md and its references")
    verify.add_argument("path", nargs="?", default=".")
    verify.add_argument("--max-lines", type=int, default=120)
    verify.add_argument("--max-bytes", type=int, default=10_240)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=cmd_verify)

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

    prompt = sub.add_parser("prompt", help="Render a role-specific minimal prompt")
    prompt.add_argument("path", nargs="?", default=".")
    prompt.add_argument("--role", choices=["builder", "reviewer", "decision"], required=True)
    prompt.set_defaults(func=cmd_prompt)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
