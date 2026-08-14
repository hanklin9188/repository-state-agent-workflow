from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..model import ActiveState
from ..parsing import parse_active


@dataclass(frozen=True)
class ContextDocument:
    path: str
    category: str
    bytes: int
    chars: int
    approx_tokens: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextPlan:
    documents: tuple[ContextDocument, ...]
    budget_tokens: int
    max_files: int
    stable_fingerprint: str
    dynamic_fingerprint: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def total_tokens(self) -> int:
        return sum(document.approx_tokens for document in self.documents)

    @property
    def stable_tokens(self) -> int:
        return sum(
            document.approx_tokens for document in self.documents if document.category == "stable"
        )

    @property
    def dynamic_tokens(self) -> int:
        return self.total_tokens - self.stable_tokens

    @property
    def within_budget(self) -> bool:
        return self.total_tokens <= self.budget_tokens

    @property
    def ok(self) -> bool:
        return not self.errors and self.within_budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": [document.to_dict() for document in self.documents],
            "document_count": len(self.documents),
            "total_tokens": self.total_tokens,
            "stable_tokens": self.stable_tokens,
            "dynamic_tokens": self.dynamic_tokens,
            "budget_tokens": self.budget_tokens,
            "within_budget": self.within_budget,
            "stable_fingerprint": self.stable_fingerprint,
            "dynamic_fingerprint": self.dynamic_fingerprint,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def build_context_plan(
    root: Path,
    *,
    budget_tokens: int = 15_000,
    max_files: int = 12,
    max_file_bytes: int = 262_144,
    include_workstream_spec: bool = False,
    state: ActiveState | None = None,
) -> ContextPlan:
    root = root.resolve()
    state = state or parse_active(root)
    candidates: list[tuple[Path, str]] = [(root / "AGENTS.md", "stable")]
    if include_workstream_spec and state.workstream_spec is not None:
        candidates.append((state.workstream_spec, "stable"))
    candidates.extend(
        [
            (root / "ACTIVE.md", "active"),
            (state.task_spec, "task"),
        ]
    )
    candidates.extend((path, "required") for path in state.required_reads)

    documents: list[ContextDocument] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[Path] = set()
    for candidate, category in candidates:
        path = candidate.resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            relative = path.relative_to(root)
        except ValueError:
            errors.append(f"Context path escapes repository: {path}")
            continue
        if not path.is_file():
            errors.append(f"Context file does not exist: {relative.as_posix()}")
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            errors.append(
                f"Context file exceeds {max_file_bytes} bytes: {relative.as_posix()} ({size})"
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"Context file is not UTF-8 text: {relative.as_posix()}")
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        documents.append(
            ContextDocument(
                path=relative.as_posix(),
                category=category,
                bytes=size,
                chars=len(text),
                approx_tokens=(len(text) + 3) // 4,
                sha256=digest,
            )
        )

    if len(documents) > max_files:
        errors.append(f"Context plan has {len(documents)} files; configured maximum is {max_files}")

    total_tokens = sum(document.approx_tokens for document in documents)
    if total_tokens > budget_tokens:
        warnings.append(
            f"Context plan is approximately {total_tokens} tokens; budget is {budget_tokens}"
        )

    stable = tuple(document for document in documents if document.category == "stable")
    dynamic = tuple(document for document in documents if document.category != "stable")
    return ContextPlan(
        documents=tuple(documents),
        budget_tokens=budget_tokens,
        max_files=max_files,
        stable_fingerprint=_fingerprint(stable),
        dynamic_fingerprint=_fingerprint(dynamic),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _fingerprint(documents: tuple[ContextDocument, ...]) -> str:
    payload = "\n".join(
        f"{document.category}:{document.path}:{document.sha256}" for document in documents
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
