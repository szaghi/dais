"""Shared fixtures: every design built once per test session (OCC builds are slow)."""

from __future__ import annotations

import pytest
from build123d import Part

from dais.designs import DESIGNS
from dais.layout import Layout

BOARD = "microsam"


@pytest.fixture(scope="session")
def built() -> dict[str, tuple[Layout, dict[str, Part]]]:
    """Design name -> (layout, checked parts) for the default board."""
    return {name: (d.layout(BOARD), d.build(BOARD)) for name, d in DESIGNS.items()}
