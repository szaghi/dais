"""The CLI writes the documented output tree."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dais.cli import main
from dais.designs import DESIGNS, variants
from dais.params import Options


def test_build_writes_design_tree(tmp_path: Path) -> None:
    main(["build", "--design", "split", "--out", str(tmp_path), "-j", "1"])
    root = tmp_path / "microsam"
    for part in ("top-case", "bottom-case", "feet"):  # integrated plate: no separate plate part
        assert (root / "split" / "stl" / f"{part}.stl").stat().st_size > 0
        assert (root / "split" / "step" / f"{part}.step").stat().st_size > 0
    assert not (root / "split" / "stl" / "plate.stl").exists()
    assert json.loads((root / "split" / "options.json").read_text())["fastener"] == "insert"
    assert (root / "coupon" / "stl" / "coupon.stl").exists()
    assert sorted(p.name for p in root.iterdir()) == ["coupon", "split"]


def test_build_legacy_pattern_variant(tmp_path: Path) -> None:
    main(["build", "--design", "split", "--legacy", "--pattern", "fuzzy", "--out", str(tmp_path), "-j", "1"])
    variant = tmp_path / "microsam" / "split-fuzzy"
    assert (variant / "stl" / "plate.stl").exists()  # legacy: separate plate
    assert (variant / "stl" / "modifier-fuzzy-skin.stl").exists()  # the slicer modifier
    opt = json.loads((variant / "options.json").read_text())
    assert opt == {"plate": "separate", "fastener": "self-tap", "bevel": 45.0, "pattern": "fuzzy"}


def test_variants_apply_patterns_to_split_designs_only() -> None:
    names = [d for _, _, d in variants(list(DESIGNS), Options(), [None, "facets"])]
    split = ["split", "split-trapezoid", "plinth", "plinth-long"]
    assert names == ["side-cove", "wrap-cove", *split, *(f"{n}-facets" for n in split)]


def test_list(capsys: pytest.CaptureFixture[str]) -> None:
    main(["list"])
    out = capsys.readouterr().out
    for name in ("side-cove", "wrap-cove", "split", "split-trapezoid"):
        assert name in out


def test_params_page_lists_every_constant() -> None:
    from dais import params
    from dais.cli import params_markdown

    page = params_markdown()
    names = [n for n in vars(params) if n.isupper() and n not in ("MIN", "MAX", "BOARDS")]  # BOARDS: own page
    missing = [n for n in names if f"`{n}`" not in page]
    assert missing == []
