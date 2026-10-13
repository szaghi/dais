"""Shared fixtures: every design built once per test session (OCC builds are slow)."""

from __future__ import annotations

import pytest
from build123d import Part

from dais.designs import DESIGNS
from dais.layout import Layout
from dais.params import LEGACY, Options

BOARD = "microsam"

Built = dict[str, tuple[Layout, dict[str, Part]]]


def build_all(opt: Options) -> Built:
    """Design name -> (layout, checked parts) for the default board."""
    return {name: (d.layout(BOARD, opt), d.build(BOARD, opt)) for name, d in DESIGNS.items()}


@pytest.fixture(scope="session")
def built() -> Built:
    """The default construction: integrated plate, M3 heat-set inserts, 60 deg bevels."""
    return build_all(Options())


@pytest.fixture(scope="session")
def built_legacy() -> Built:
    """The first prototypes: separate plate, M2 self-tapping screws, 45 deg bevels."""
    return build_all(LEGACY)
