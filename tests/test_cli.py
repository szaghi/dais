"""The CLI writes the documented output tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from dais.cli import main


def test_build_writes_design_tree(tmp_path: Path) -> None:
    main(["build", "--design", "split", "--out", str(tmp_path), "-j", "1"])
    root = tmp_path / "microsam"
    for part in ("top-case", "bottom-case", "plate", "feet"):
        assert (root / "split" / "stl" / f"{part}.stl").stat().st_size > 0
        assert (root / "split" / "step" / f"{part}.step").stat().st_size > 0
    assert (root / "coupon" / "stl" / "coupon.stl").exists()
    assert sorted(p.name for p in root.iterdir()) == ["coupon", "split"]


def test_list(capsys: pytest.CaptureFixture[str]) -> None:
    main(["list"])
    out = capsys.readouterr().out
    for name in ("side-cove", "wrap-cove", "split", "split-trapezoid"):
        assert name in out


def test_params_page_lists_every_constant() -> None:
    from dais import params
    from dais.cli import params_markdown

    page = params_markdown()
    names = [n for n in vars(params) if n.isupper() and n not in ("MIN", "MAX", "BOARDS")]
    missing = [n for n in names if f"`{n}`" not in page]
    assert missing == []
