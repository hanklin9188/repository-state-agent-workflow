from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..model import ActiveState
from .store import atomic_write_json

INDEX_SCHEMA = "rsaw.relevance-index.v1"
FOCUS_SCHEMA = "rsaw.focus-bundle.v1"
EXTRACTOR_VERSION = 1

_CODE_SUFFIXES = {
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".java",
    ".kt",
    ".kts",
    ".rb",
    ".php",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".md",
    ".mdx",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".jsonc",
}

_SPECIAL_TEXT_NAMES = {
    "Dockerfile",
    "Makefile",
    "Justfile",
    "Procfile",
    "CMakeLists.txt",
    "AGENTS.md",
    "ACTIVE.md",
}

_IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "target",
    "coverage",
    ".next",
    ".turbo",
}

_IGNORED_PREFIXES = (
    ".rsaw/",
    "artifacts/",
)

_SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

_STOP_WORDS = {
    "about",
    "active",
    "after",
    "agent",
    "all",
    "also",
    "and",
    "before",
    "build",
    "builder",
    "change",
    "check",
    "code",
    "complete",
    "context",
    "current",
    "does",
    "edgeflow",
    "exact",
    "file",
    "files",
    "from",
    "gate",
    "into",
    "must",
    "next",
    "none",
    "only",
    "pass",
    "read",
    "repository",
    "required",
    "role",
    "rsaw",
    "runner",
    "src",
    "lib",
    "app",
    "main",
    "should",
    "state",
    "task",
    "test",
    "tests",
    "that",
    "the",
    "then",
    "this",
    "through",
    "validation",
    "with",
    "without",
    "work",
}

_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_./+@-]+")
_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
_GENERIC_SYMBOL_PATTERNS = (
    ("class", re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_]\w*)")),
    ("interface", re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_]\w*)")),
    ("type", re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_]\w*)\s*=")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(")),
    (
        "function",
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?\("),
    ),
    ("function", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(")),
    ("function", re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)\s*\(")),
    ("struct", re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)")),
    ("enum", re.compile(r"^\s*(?:pub\s+)?enum\s+([A-Za-z_]\w*)")),
    ("trait", re.compile(r"^\s*(?:pub\s+)?trait\s+([A-Za-z_]\w*)")),
    ("class", re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?class\s+([A-Za-z_]\w*)")),
    ("function", re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")),
    ("class", re.compile(r"^\s*class\s+([A-Za-z_]\w*)")),
)


@dataclass(frozen=True)
class RelevanceConfig:
    enabled: bool = True
    map_tokens: int = 900
    focus_tokens: int = 3_000
    max_snippets: int = 5
    candidate_limit: int = 20
    snippet_lines: int = 64
    max_file_bytes: int = 200_000
    max_index_files: int = 10_000
    max_provider_input_tokens: int = 180_000
    max_cached_input_tokens: int = 120_000

    @classmethod
    def from_root(cls, root: Path) -> RelevanceConfig:
        path = root / ".rsaw/config.json"
        raw: dict[str, Any] = {}
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                runtime = value.get("runtime", {})
                if isinstance(runtime, dict):
                    candidate = runtime.get("relevance", {})
                    if isinstance(candidate, dict):
                        raw = candidate
        values = {
            "enabled": bool(raw.get("enabled", True)),
            "map_tokens": _bounded_int(raw.get("mapTokens"), 900, 0, 8_000),
            "focus_tokens": _bounded_int(raw.get("focusTokens"), 3_000, 0, 16_000),
            "max_snippets": _bounded_int(raw.get("maxSnippets"), 5, 0, 24),
            "candidate_limit": _bounded_int(raw.get("candidateLimit"), 20, 1, 200),
            "snippet_lines": _bounded_int(raw.get("snippetLines"), 64, 12, 240),
            "max_file_bytes": _bounded_int(raw.get("maxFileBytes"), 200_000, 4_096, 2_000_000),
            "max_index_files": _bounded_int(raw.get("maxIndexFiles"), 10_000, 100, 100_000),
            "max_provider_input_tokens": _bounded_int(
                raw.get("maxProviderInputTokens"), 180_000, 0, 10_000_000
            ),
            "max_cached_input_tokens": _bounded_int(
                raw.get("maxCachedInputTokens"), 120_000, 0, 10_000_000
            ),
        }
        return cls(**values)

    def to_config(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mapTokens": self.map_tokens,
            "focusTokens": self.focus_tokens,
            "maxSnippets": self.max_snippets,
            "candidateLimit": self.candidate_limit,
            "snippetLines": self.snippet_lines,
            "maxFileBytes": self.max_file_bytes,
            "maxIndexFiles": self.max_index_files,
            "maxProviderInputTokens": self.max_provider_input_tokens,
            "maxCachedInputTokens": self.max_cached_input_tokens,
        }


@dataclass(frozen=True)
class FocusSnippet:
    path: str
    start_line: int
    end_line: int
    score: float
    reasons: tuple[str, ...]
    content: str
    sha256: str

    def to_dict(self, *, show_content: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        if not show_content:
            payload.pop("content", None)
        return payload


@dataclass(frozen=True)
class FocusBundle:
    enabled: bool
    task_id: str
    query_sha256: str
    index_sha256: str
    sha256: str
    map_text: str
    snippets: tuple[FocusSnippet, ...]
    map_tokens: int
    snippet_tokens: int
    candidate_count: int
    indexed_files: int
    cache_hits: int
    cache_misses: int
    selected_files: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def total_tokens(self) -> int:
        return self.map_tokens + self.snippet_tokens

    def prompt_block(self, *, max_tokens: int | None = None) -> str:
        if not self.enabled or self.total_tokens <= 0:
            return ""

        limit = max_tokens if max_tokens is not None and max_tokens >= 0 else None
        parts = [
            "## RSAW Focus Context",
            "",
            "This is the preselected repository working set. Use it before searching broadly. "
            "Run additional discovery only for a concrete unresolved question.",
        ]

        def fits(candidate: list[str]) -> bool:
            return limit is None or estimate_tokens("\n".join(candidate)) <= limit

        if self.map_text:
            map_lines: list[str] = []
            for line in self.map_text.splitlines():
                candidate = [
                    *parts,
                    "",
                    "### Structural map",
                    "",
                    "```text",
                    *map_lines,
                    line,
                    "```",
                ]
                if not fits(candidate):
                    break
                map_lines.append(line)
            if map_lines:
                parts.extend(["", "### Structural map", "", "```text", *map_lines, "```"])

        if self.snippets:
            heading_added = False
            for snippet in self.snippets:
                reason = ", ".join(snippet.reasons)
                block = [
                    "",
                    f"#### `{snippet.path}:{snippet.start_line}-{snippet.end_line}` — {reason}",
                    "",
                    "```",
                    snippet.content,
                    "```",
                ]
                candidate = [*parts]
                if not heading_added:
                    candidate.extend(["", "### Focused excerpts"])
                candidate.extend(block)
                if not fits(candidate):
                    continue
                if not heading_added:
                    parts.extend(["", "### Focused excerpts"])
                    heading_added = True
                parts.extend(block)

        text = "\n".join(parts).strip()
        return text if limit is None or estimate_tokens(text) <= limit else ""

    def to_dict(self, *, show_content: bool = False) -> dict[str, Any]:
        return {
            "schemaVersion": FOCUS_SCHEMA,
            "enabled": self.enabled,
            "taskId": self.task_id,
            "querySha256": self.query_sha256,
            "indexSha256": self.index_sha256,
            "focusSha256": self.sha256,
            "mapTokens": self.map_tokens,
            "snippetTokens": self.snippet_tokens,
            "totalTokens": self.total_tokens,
            "candidateCount": self.candidate_count,
            "indexedFiles": self.indexed_files,
            "cacheHits": self.cache_hits,
            "cacheMisses": self.cache_misses,
            "selectedFiles": list(self.selected_files),
            "warnings": list(self.warnings),
            "map": self.map_text if show_content else None,
            "snippets": [snippet.to_dict(show_content=show_content) for snippet in self.snippets],
        }


@dataclass(frozen=True)
class RepositoryIndex:
    files: dict[str, dict[str, Any]]
    sha256: str
    cache_hits: int
    cache_misses: int
    skipped_files: int

    @property
    def indexed_files(self) -> int:
        return len(self.files)


def relevance_defaults() -> dict[str, Any]:
    return RelevanceConfig().to_config()


def migrate_v8(root: Path, *, apply: bool = False) -> dict[str, Any]:
    root = root.resolve()
    config_path = root / ".rsaw/config.json"
    active_path = root / "ACTIVE.md"
    raw: dict[str, Any] = {}
    if config_path.is_file():
        value = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(".rsaw/config.json must be an object")
        raw = value
    before_active = _sha_file(active_path) if active_path.is_file() else ""
    before_config = _sha_file(config_path) if config_path.is_file() else ""
    updated = json.loads(json.dumps(raw))
    updated["schema_version"] = max(int(updated.get("schema_version") or 0), 5)
    runtime = updated.setdefault("runtime", {})
    if not isinstance(runtime, dict):
        raise ValueError("runtime configuration must be an object")
    runtime.setdefault("max_transitions", 100)
    runtime.setdefault("max_total_input_tokens", 5_000_000)
    v6 = runtime.setdefault("v6", {})
    if not isinstance(v6, dict):
        raise ValueError("runtime.v6 must be an object")
    v6.setdefault("enabled", True)
    runtime.setdefault(
        "codex",
        {
            "binary": runtime.get("codex_binary", "codex"),
            "defaultSandbox": runtime.get("sandbox", "workspace-write"),
            "taskSandboxOverrides": {},
        },
    )
    runtime.setdefault(
        "toolBudget",
        {
            "maxToolCallsPerTurn": 32,
            "maxToolOutputTokens": 50_000,
            "maxSingleToolOutputTokens": 20_000,
            "maxBroadDiscoveryCommands": 2,
            "enforce": True,
        },
    )
    relevance = runtime.setdefault("relevance", {})
    if not isinstance(relevance, dict):
        raise ValueError("runtime.relevance must be an object")
    for key, value in relevance_defaults().items():
        relevance.setdefault(key, value)
    backup = root / ".rsaw/config.v071.backup.json"
    payload: dict[str, Any] = {
        "target": "0.8",
        "apply": apply,
        "config": ".rsaw/config.json",
        "backup": ".rsaw/config.v071.backup.json",
        "activeSha256Before": before_active,
        "configSha256Before": before_config,
        "preservesActive": True,
        "relevanceEnabled": bool(relevance.get("enabled", True)),
    }
    if not apply:
        return payload
    if config_path.is_file() and not backup.exists():
        atomic_write_json(backup, raw)
    atomic_write_json(config_path, updated)
    after_active = _sha_file(active_path) if active_path.is_file() else ""
    payload.update(
        {
            "activeSha256After": after_active,
            "configSha256After": _sha_file(config_path),
            "status": "MIGRATED" if updated != raw else "ALREADY_CURRENT",
        }
    )
    if before_active != after_active:
        raise RuntimeError("v0.8 migration changed ACTIVE.md")
    return payload


def build_focus_bundle(
    root: Path,
    state: ActiveState,
    *,
    force_index: bool = False,
) -> FocusBundle:
    root = root.resolve()
    config = RelevanceConfig.from_root(root)
    if not config.enabled:
        return FocusBundle(
            enabled=False,
            task_id=state.task_id,
            query_sha256="",
            index_sha256="",
            sha256="",
            map_text="",
            snippets=(),
            map_tokens=0,
            snippet_tokens=0,
            candidate_count=0,
            indexed_files=0,
            cache_hits=0,
            cache_misses=0,
            selected_files=(),
        )

    index = build_repository_index(root, config=config, force=force_index)
    query_text, exact_paths, query_terms = _build_query(root, state)
    query_sha = hashlib.sha256(query_text.encode("utf-8")).hexdigest()
    required = _required_paths(root, state)
    changed = _changed_files(root)
    ranked = _rank_files(
        index.files,
        query_terms=query_terms,
        exact_paths=exact_paths,
        required_paths=required,
        changed_paths=changed,
        limit=config.candidate_limit,
    )
    map_text = _render_map(index.files, ranked, query_terms, config.map_tokens)
    snippets = _select_snippets(
        root,
        index.files,
        ranked,
        query_terms=query_terms,
        exact_paths=exact_paths,
        required_paths=required,
        config=config,
    )
    map_tokens = estimate_tokens(map_text)
    snippet_tokens = sum(estimate_tokens(snippet.content) for snippet in snippets)
    selected_files = tuple(dict.fromkeys(snippet.path for snippet in snippets))
    canonical = json.dumps(
        {
            "task": state.task_id,
            "query": query_sha,
            "index": index.sha256,
            "map": map_text,
            "snippets": [
                {
                    "path": item.path,
                    "start": item.start_line,
                    "end": item.end_line,
                    "sha256": item.sha256,
                }
                for item in snippets
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    focus_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    warnings: list[str] = []
    if not ranked:
        warnings.append("No repository candidates matched the active task")
    return FocusBundle(
        enabled=True,
        task_id=state.task_id,
        query_sha256=query_sha,
        index_sha256=index.sha256,
        sha256=focus_sha,
        map_text=map_text,
        snippets=tuple(snippets),
        map_tokens=map_tokens,
        snippet_tokens=snippet_tokens,
        candidate_count=len(ranked),
        indexed_files=index.indexed_files,
        cache_hits=index.cache_hits,
        cache_misses=index.cache_misses,
        selected_files=selected_files,
        warnings=tuple(warnings),
    )


def build_repository_index(
    root: Path,
    *,
    config: RelevanceConfig | None = None,
    force: bool = False,
) -> RepositoryIndex:
    root = root.resolve()
    config = config or RelevanceConfig.from_root(root)
    cache_path = root / ".rsaw/cache/relevance-index-v1.json"
    previous: dict[str, Any] = {}
    if cache_path.is_file() and not force:
        try:
            value = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(value, dict) and value.get("schemaVersion") == INDEX_SCHEMA:
                previous = value
        except (OSError, json.JSONDecodeError):
            previous = {}
    previous_files = previous.get("files", {})
    if not isinstance(previous_files, dict):
        previous_files = {}

    records: dict[str, dict[str, Any]] = {}
    cache_hits = 0
    cache_misses = 0
    skipped = 0
    root_resolved = root.resolve()
    for rel_path in _repository_files(root, config.max_index_files):
        path = root / rel_path
        try:
            resolved = path.resolve()
            resolved.relative_to(root_resolved)
            raw = resolved.read_bytes()
        except (OSError, ValueError):
            skipped += 1
            continue
        if len(raw) > config.max_file_bytes or b"\x00" in raw:
            skipped += 1
            continue
        digest = hashlib.sha256(raw).hexdigest()
        cached = previous_files.get(rel_path)
        if (
            not force
            and isinstance(cached, dict)
            and cached.get("sha256") == digest
            and cached.get("extractorVersion") == EXTRACTOR_VERSION
        ):
            records[rel_path] = cached
            cache_hits += 1
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped += 1
            continue
        records[rel_path] = _index_file(rel_path, text, digest)
        cache_misses += 1

    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    index_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    payload = {
        "schemaVersion": INDEX_SCHEMA,
        "extractorVersion": EXTRACTOR_VERSION,
        "indexSha256": index_sha,
        "files": records,
    }
    atomic_write_json(cache_path, payload)
    return RepositoryIndex(
        files=records,
        sha256=index_sha,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        skipped_files=skipped,
    )


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(maximum, max(minimum, parsed))


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repository_files(root: Path, limit: int) -> list[str]:
    paths: list[str] = []
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if completed.returncode == 0:
            paths = [
                value.decode("utf-8", errors="replace")
                for value in completed.stdout.split(b"\0")
                if value
            ]
    except OSError:
        paths = []
    if not paths:
        for directory, dirnames, filenames in os.walk(root):
            current = Path(directory)
            dirnames[:] = [name for name in dirnames if name not in _IGNORED_PARTS]
            for filename in filenames:
                try:
                    paths.append((current / filename).relative_to(root).as_posix())
                except ValueError:
                    continue
    filtered = [path for path in sorted(set(paths)) if _is_indexable_path(path)]
    return filtered[:limit]


def _is_indexable_path(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized.startswith("../"):
        return False
    if any(normalized.startswith(prefix) for prefix in _IGNORED_PREFIXES):
        return False
    path = Path(normalized)
    if any(part in _IGNORED_PARTS for part in path.parts):
        return False
    if (
        path.name in _SENSITIVE_NAMES
        or path.name.startswith(".env")
        or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
    ):
        return False
    if path.name in _SPECIAL_TEXT_NAMES:
        return True
    return path.suffix.lower() in _CODE_SUFFIXES


def _index_file(rel_path: str, text: str, digest: str) -> dict[str, Any]:
    suffix = Path(rel_path).suffix.lower()
    if suffix in {".py", ".pyi"}:
        symbols, imports, keywords = _extract_python(text)
    else:
        symbols, imports, keywords = _extract_generic(text, suffix)
    return {
        "sha256": digest,
        "extractorVersion": EXTRACTOR_VERSION,
        "suffix": suffix,
        "lineCount": len(text.splitlines()),
        "symbols": symbols[:240],
        "imports": imports[:160],
        "keywords": keywords[:200],
    }


def _extract_python(text: str) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _extract_generic(text, ".py")
    symbols: list[dict[str, Any]] = []
    imports: list[str] = []
    names: Counter[str] = Counter()

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def _add(self, node: ast.AST, kind: str, name: str, signature: str) -> None:
            qualified = ".".join([*self.stack, name]) if self.stack else name
            symbols.append(
                {
                    "name": qualified,
                    "shortName": name,
                    "kind": kind,
                    "line": int(getattr(node, "lineno", 1)),
                    "endLine": int(getattr(node, "end_lineno", getattr(node, "lineno", 1))),
                    "signature": signature,
                }
            )

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self._add(node, "class", node.name, f"class {node.name}")
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            try:
                args = ast.unparse(node.args)
            except Exception:
                args = "..."
            self._add(node, "function", node.name, f"def {node.name}({args})")
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            try:
                args = ast.unparse(node.args)
            except Exception:
                args = "..."
            self._add(node, "function", node.name, f"async def {node.name}({args})")
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Import(self, node: ast.Import) -> None:
            imports.extend(alias.name for alias in node.names)
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module:
                imports.append(node.module)
            self.generic_visit(node)

        def visit_Name(self, node: ast.Name) -> None:
            names[node.id] += 1

        def visit_Attribute(self, node: ast.Attribute) -> None:
            names[node.attr] += 1
            self.generic_visit(node)

    Visitor().visit(tree)
    keywords = [name for name, _ in names.most_common(200) if len(name) >= 3]
    return symbols, sorted(set(imports)), keywords


def _extract_generic(text: str, suffix: str) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    symbols: list[dict[str, Any]] = []
    imports: list[str] = []
    words: Counter[str] = Counter()
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if suffix in {".md", ".mdx"} and stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                symbols.append(
                    {
                        "name": heading,
                        "shortName": heading,
                        "kind": "heading",
                        "line": number,
                        "endLine": number,
                        "signature": stripped,
                    }
                )
        for kind, pattern in _GENERIC_SYMBOL_PATTERNS:
            match = pattern.match(line)
            if match:
                name = match.group(1)
                symbols.append(
                    {
                        "name": name,
                        "shortName": name,
                        "kind": kind,
                        "line": number,
                        "endLine": number,
                        "signature": stripped[:240],
                    }
                )
                break
        import_match = re.match(
            r"^\s*(?:from\s+([A-Za-z0-9_./-]+)|import\s+[^\"']*[\"']([^\"']+)|require\([\"']([^\"']+))",
            line,
        )
        if import_match:
            imports.append(next(value for value in import_match.groups() if value))
        words.update(word.lower() for word in _WORD_PATTERN.findall(line))
    keywords = [name for name, _ in words.most_common(200) if name not in _STOP_WORDS]
    return symbols, sorted(set(imports)), keywords


def _build_query(root: Path, state: ActiveState) -> tuple[str, set[str], set[str]]:
    chunks = [
        state.task_id,
        str(getattr(state, "next_action", "") or ""),
        str(getattr(state, "stop_condition", "") or ""),
        str(getattr(state, "next_task_id", "") or ""),
    ]
    task_spec = Path(state.task_spec)
    if task_spec.is_file():
        chunks.append(task_spec.read_text(encoding="utf-8", errors="replace")[:80_000])
    active_pointer = root / ".rsaw/state/active.json"
    if active_pointer.is_file():
        try:
            pointer = json.loads(active_pointer.read_text(encoding="utf-8"))
            capsule_ref = pointer.get("semanticCapsuleRef") if isinstance(pointer, dict) else None
            if isinstance(capsule_ref, str):
                capsule_path = root / capsule_ref
                if capsule_path.is_file() and capsule_path.stat().st_size <= 64_000:
                    chunks.append(capsule_path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            pass
    text = "\n".join(chunk for chunk in chunks if chunk)
    exact_paths = {
        match.group(0).rstrip(".,:;)").replace("\\", "/") for match in _PATH_PATTERN.finditer(text)
    }
    terms = _terms(text)
    return text, exact_paths, terms


def _terms(text: str) -> set[str]:
    values: set[str] = set()
    for raw in _WORD_PATTERN.findall(text):
        split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw).replace("_", " ").replace("-", " ")
        for item in split.split():
            value = item.lower()
            if len(value) >= 3 and value not in _STOP_WORDS and not value.isdigit():
                values.add(value)
    return values


def _required_paths(root: Path, state: ActiveState) -> set[str]:
    paths: set[str] = set()
    for path in getattr(state, "required_reads", ()):
        try:
            paths.add(Path(path).resolve().relative_to(root).as_posix())
        except (OSError, ValueError):
            continue
    with contextlib.suppress(OSError, ValueError):
        paths.add(Path(state.task_spec).resolve().relative_to(root).as_posix())
    paths.update({"ACTIVE.md", "AGENTS.md"})
    return paths


def _changed_files(root: Path) -> set[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except OSError:
        return set()
    if completed.returncode != 0:
        return set()
    changed: set[str] = set()
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        path = text[3:] if len(text) > 3 else text
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[-1]
        changed.add(path.replace("\\", "/"))
    return changed


def _rank_files(
    records: dict[str, dict[str, Any]],
    *,
    query_terms: set[str],
    exact_paths: set[str],
    required_paths: set[str],
    changed_paths: set[str],
    limit: int,
) -> list[tuple[str, float, tuple[str, ...]]]:
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for path, record in records.items():
        if path in required_paths:
            continue
        path_terms = _terms(path)
        basename_terms = _terms(Path(path).stem)
        symbol_names = {
            part
            for symbol in record.get("symbols", [])
            if isinstance(symbol, dict)
            for part in _terms(str(symbol.get("name") or ""))
        }
        keywords = {str(value).lower() for value in record.get("keywords", [])}
        score = 0.0
        why: list[str] = []
        if path in exact_paths or any(path.endswith(value) for value in exact_paths):
            score += 180.0
            why.append("task path")
        if path in changed_paths:
            score += 100.0
            why.append("current change")
        basename_hits = query_terms & basename_terms
        if basename_hits:
            score += 28.0 * len(basename_hits)
            why.append("file name")
        path_hits = query_terms & path_terms
        if path_hits:
            score += 10.0 * len(path_hits)
            why.append("path match")
        symbol_hits = query_terms & symbol_names
        if symbol_hits:
            score += 16.0 * len(symbol_hits)
            why.append("symbol match")
        keyword_hits = query_terms & keywords
        if keyword_hits:
            score += min(40.0, 2.0 * len(keyword_hits))
            why.append("content terms")
        if (
            path.startswith("tests/")
            and {"test", "validation", "reject", "regression"} & query_terms
        ):
            score += 12.0
            why.append("test relevance")
        if score > 0:
            scores[path] = score
            reasons[path] = why

    module_to_path: dict[str, str] = {}
    for path in records:
        without_suffix = str(Path(path).with_suffix("")).replace("/", ".")
        module_to_path[without_suffix] = path
        module_to_path[Path(path).stem] = path
    seeds = sorted(scores, key=lambda value: (-scores[value], value))[:8]
    for seed in seeds:
        record = records[seed]
        for imported in record.get("imports", []):
            imported_value = str(imported).lstrip(".")
            candidates = [
                module_to_path.get(imported_value),
                module_to_path.get(imported_value.split(".")[-1]),
            ]
            for candidate in candidates:
                if candidate and candidate not in required_paths and candidate != seed:
                    scores[candidate] = scores.get(candidate, 0.0) + 12.0
                    reasons.setdefault(candidate, []).append("dependency")

    ranked = [
        (path, score, tuple(dict.fromkeys(reasons.get(path, ["ranked"]))))
        for path, score in scores.items()
    ]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked[:limit]


def _render_map(
    records: dict[str, dict[str, Any]],
    ranked: list[tuple[str, float, tuple[str, ...]]],
    query_terms: set[str],
    budget: int,
) -> str:
    if budget <= 0:
        return ""
    lines: list[str] = []
    for path, _score, reasons in ranked:
        candidate = [f"{path}  [{', '.join(reasons)}]"]
        symbols = [value for value in records[path].get("symbols", []) if isinstance(value, dict)]
        symbols.sort(
            key=lambda value: (
                -len(query_terms & _terms(str(value.get("name") or ""))),
                int(value.get("line") or 0),
                str(value.get("name") or ""),
            )
        )
        for symbol in symbols[:8]:
            signature = str(symbol.get("signature") or symbol.get("name") or "").strip()
            if signature:
                candidate.append(f"  L{int(symbol.get('line') or 1)} {signature[:180]}")
        next_text = "\n".join([*lines, *candidate])
        if estimate_tokens(next_text) > budget:
            break
        lines.extend(candidate)
    return "\n".join(lines)


def _select_snippets(
    root: Path,
    records: dict[str, dict[str, Any]],
    ranked: list[tuple[str, float, tuple[str, ...]]],
    *,
    query_terms: set[str],
    exact_paths: set[str],
    required_paths: set[str],
    config: RelevanceConfig,
) -> list[FocusSnippet]:
    selected: list[FocusSnippet] = []
    used_tokens = 0
    for path, score, reasons in ranked:
        if len(selected) >= config.max_snippets or path in required_paths:
            break
        file_path = root / path
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        if not lines:
            continue
        anchor = _best_anchor(lines, records[path], query_terms, path in exact_paths)
        half = config.snippet_lines // 2
        start = max(0, anchor - half)
        end = min(len(lines), start + config.snippet_lines)
        start = max(0, end - config.snippet_lines)
        content = "\n".join(lines[start:end]).strip()
        if not content:
            continue
        tokens = estimate_tokens(content)
        if used_tokens + tokens > config.focus_tokens:
            remaining = config.focus_tokens - used_tokens
            if remaining < 80:
                break
            max_chars = remaining * 4
            content = content[:max_chars].rstrip()
            tokens = estimate_tokens(content)
            if not content:
                break
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        selected.append(
            FocusSnippet(
                path=path,
                start_line=start + 1,
                end_line=start + len(content.splitlines()),
                score=round(score, 3),
                reasons=reasons,
                content=content,
                sha256=digest,
            )
        )
        used_tokens += tokens
    return selected


def _best_anchor(
    lines: list[str], record: dict[str, Any], query_terms: set[str], exact_path: bool
) -> int:
    best_line = 0
    best_score = -1
    for symbol in record.get("symbols", []):
        if not isinstance(symbol, dict):
            continue
        matches = query_terms & _terms(str(symbol.get("name") or ""))
        score = 20 * len(matches)
        if exact_path:
            score += 2
        if score > best_score:
            best_score = score
            best_line = max(0, int(symbol.get("line") or 1) - 1)
    for index, line in enumerate(lines):
        matches = query_terms & _terms(line)
        score = len(matches)
        if score > best_score:
            best_score = score
            best_line = index
    return best_line


def fixture_context_metrics(
    root: Path,
    state: ActiveState,
    *,
    force_index: bool = False,
) -> dict[str, Any]:
    config = RelevanceConfig.from_root(root)
    bundle = build_focus_bundle(root, state, force_index=force_index)
    index = build_repository_index(root, config=config, force=False)
    baseline_tokens = 0
    for path in index.files:
        try:
            baseline_tokens += estimate_tokens((root / path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    reduction = 1.0 - (bundle.total_tokens / baseline_tokens) if baseline_tokens else 0.0
    return {
        "baselineTokens": baseline_tokens,
        "focusTokens": bundle.total_tokens,
        "reductionRatio": reduction,
        "selectedFiles": list(bundle.selected_files),
        "indexedFiles": bundle.indexed_files,
        "cacheHits": bundle.cache_hits,
        "cacheMisses": bundle.cache_misses,
    }
