from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts/check_markdown_links.py"
SPEC = importlib.util.spec_from_file_location("check_markdown_links", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_valid_local_link(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[Guide](docs/guide.md)\n", encoding="utf-8")
    (tmp_path / "docs/guide.md").write_text("# Guide\n", encoding="utf-8")
    assert MODULE.check_links(tmp_path) == []


def test_missing_local_link(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[Missing](docs/missing.md)\n", encoding="utf-8")
    errors = MODULE.check_links(tmp_path)
    assert len(errors) == 1
    assert "missing target" in errors[0]


def test_external_and_anchor_links_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "[Web](https://example.com) [Section](#section)\n", encoding="utf-8"
    )
    assert MODULE.check_links(tmp_path) == []
