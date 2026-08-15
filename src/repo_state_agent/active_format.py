from __future__ import annotations

import re
from pathlib import Path

_SECTION_RE_TEMPLATE = r"(^##\s+{heading}\s*$\n)(.*?)(?=^##\s+|\Z)"


def canonicalize_active_text(text: str) -> str:
    """Return a stable ACTIVE.md representation without changing section content.

    Trailing whitespace and redundant blank lines outside fenced code blocks are removed.
    The canonical form always ends with exactly one newline.
    """

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    output: list[str] = []
    in_fence = False
    previous_blank = False

    for raw_line in normalized.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence

        blank = not stripped
        if blank and previous_blank and not in_fence:
            continue

        output.append(line)
        previous_blank = blank and not in_fence

    while output and not output[0].strip():
        output.pop(0)
    while output and not output[-1].strip():
        output.pop()

    return "\n".join(output) + "\n"


def replace_section(text: str, heading: str, body: str) -> str:
    """Replace or append one level-two Markdown section, then canonicalize."""

    pattern = re.compile(
        _SECTION_RE_TEMPLATE.format(heading=re.escape(heading)),
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    clean_body = body.strip()

    if pattern.search(text):
        updated = pattern.sub(
            lambda match: f"{match.group(1)}\n{clean_body}\n\n",
            text,
            count=1,
        )
    else:
        updated = text.rstrip() + f"\n\n## {heading}\n\n{clean_body}\n"

    return canonicalize_active_text(updated)


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        _SECTION_RE_TEMPLATE.format(heading=re.escape(heading)),
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(2).strip() if match else ""


def active_budget_errors(
    text: str,
    *,
    max_lines: int = 140,
    max_bytes: int = 12_288,
) -> list[str]:
    canonical = canonicalize_active_text(text)
    line_count = len(canonical.splitlines())
    byte_count = len(canonical.encode("utf-8"))
    errors: list[str] = []
    if line_count > max_lines:
        errors.append(f"ACTIVE.md has {line_count} canonical lines; limit is {max_lines}")
    if byte_count > max_bytes:
        errors.append(f"ACTIVE.md has {byte_count} canonical bytes; limit is {max_bytes}")
    return errors


def normalize_active_file(path: Path) -> bool:
    before = path.read_text(encoding="utf-8")
    after = canonicalize_active_text(before)
    if before == after:
        return False
    path.write_text(after, encoding="utf-8")
    return True
