from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")
IGNORED_DIRS = {".git", ".venv", "venv", ".tox", ".pytest_cache", ".ruff_cache"}


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in IGNORED_DIRS for part in path.relative_to(root).parts)
    )


def local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if not target or target.startswith(IGNORED_PREFIXES):
        return None
    # Optional Markdown title: path "title"
    if " \"" in target:
        target = target.split(" \"", 1)[0]
    target = unquote(target.split("#", 1)[0])
    return target or None


def check_links(root: Path) -> list[str]:
    errors: list[str] = []
    for document in markdown_files(root):
        text = document.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue
            resolved = (document.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{document.relative_to(root)}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{document.relative_to(root)}:{line}: missing target: {target}")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    root = Path(args[0] if args else ".").resolve()
    errors = check_links(root)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    count = len(markdown_files(root))
    print(f"PASS: checked local links in {count} Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
