# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

DAIS (Desktop Assignable Input Switch): a generic one-key MX macropad. Khor microSAM (RP2040,
Pro Micro footprint) + upstream QMK + a 3D-printed case generated in Python with build123d.
The VitePress site in `docs/` is the full documentation; `README.md` is a short landing page.

## Commands

```bash
make dev                      # .venv + editable install (build123d, pytest, ruff)
make build                    # dais build --clean -> out/microsam/<design>/{stl,step}/
make render                   # dais render -> docs/public/img/<design>/<view>.svg
make params                   # regenerate docs/guide/parameters.md from params.py
make photo                    # Blender Cycles renders -> docs/public/photo/<design>/<shot>.webp (slow, CPU)
make test                     # pytest + coverage (~10 s: builds every design once)
make lint / make fmt          # ruff (config in pyproject.toml, line length 120)
make docs / make docs-dev     # VitePress build / dev server (npm, in docs/)
.venv/bin/pytest tests/test_geometry.py::test_top_case_prints_without_supports   # one test
.venv/bin/dais build --design split --board rp2040zero
```

The directory is not a git repository. `out/` is generated and disposable; `docs/public/img/`
is generated too but is what the docs and README display, so re-render after geometry changes.

## Architecture (`src/dais/`)

- `params.py`: **every dimension is a constant here**, grouped by `# --- Section ---` headers
  that `dais params` parses into the docs page (keep the `NAME = value  # comment`
  shape). `MEASURE` values are placeholders awaiting calipers or the coupon: never change them
  without a measurement.
- `layout.py`: `Layout.for_board(board, front_extra)` derives all sizes; the key height is
  built bottom-up from floor + PCB + `COMP_H` + `WIRE_GAP` + tilted switch drop, so board or
  switch constants move the whole case. Frames: world (z = 0 case bottom, -Y front, +Y back
  USB-C), key frame `lay.key` (plate-top centre, tilted `TILT`), parting frame `parting()` for
  the split seam; `below_roof`/`above_floor`/`half_space`/`between` are clipping slabs.
- `shell.py`: plan outline helpers `plan_pts`/`side_x`/`outline` take insets **normal to each
  edge** so features follow the trapezoid sides -- use them, not axis-aligned boxes, for anything
  hugging a wall. Also the wedge, the key well + plate pilots cutter, the split USB-C cuts.
- `one_piece.py` (body + side/wrap coves), `split.py` (top case, bottom case), `parts.py`
  (plate, bottom plate/floor, feet, coupon).
- `designs.py`: `DESIGNS` registry -- `side-cove`, `wrap-cove`, `split`, `split-trapezoid`.
  A new design is one `Design` entry; CLI, output tree and renderer pick it up (add its docs
  page and sidebar entry by hand). `Design.build()` runs `check()`: valid single solids (feet
  excepted), no pairwise clash > 1e-3 mm^3.
- `cli.py` (`build | render | list | params`, one process per design), `render.py`
  (hidden-line SVGs; switch/cap/PCB/USB are envelope dummies).
- Parts are exported in **assembly position**; each design directory is a complete print set.
- `photo.py` + `blender_scene.py` + `display.py`: photo renders. `blender_scene.py` runs inside
  Blender's Python (only `bpy`, reads a JSON scene; excluded from coverage). `display.py` holds
  display-only keycap/switch models, never part of fit checks.
- **Renders must never touch the GPU** (owner's ADAM tests need all VRAM): Blender runs in an
  `unshare` user+mount namespace masking `/dev/dxg`, `/dev/nvidia*` and `/usr/lib/wsl`
  (`GPU_MASK`), plus `CUDA_VISIBLE_DEVICES=""`, CPU-only Cycles, background mode only (no
  EEVEE/Workbench: they need OpenGL). RAM capped by a `systemd-run --user --scope` with
  `MemoryMax` (default 2G), `nice -n 19`, fixed threads (default 8). Don't weaken any layer.

## Rules learned the hard way

- **Top shells print top-down without supports**: anything inside `body`/`top-case` must grow
  from the top skin (clip columns with `below_roof(lay, lift=0.5)`), never end in mid-air.
  `test_top_case_prints_without_supports` enforces it.
- **OCC booleans can fail silently** (valid solid, cut missing): a cylinder cut into a filleted
  plate corner was dropped at one corner of four. Cut before filleting; verify symmetric cuts.
  `check()` catches overlap, not clearance -- clearance needs its own test.
- Coincident faces in a union give an invalid solid: trim by 0.01 mm.
- Edge breaks select faces by position (`sort_by(Axis.Z)[0]`, seam face along the tilted
  normal): adding lower/higher faces before them changes what gets chamfered.
- `tests/golden_volumes.json` pins every part volume (rel 1e-9). After an **intended** geometry
  change, inspect the renders, then regenerate with `.venv/bin/python tests/test_geometry.py`.
  A refactor must leave it untouched.

## Docs

VitePress 1.x + vitepress-plugin-mermaid; `vite.build.target: 'es2022'` in
`docs/.vitepress/config.mts` is required (mermaid >= 11.16 ships es2022 syntax). Image
galleries use the `<Views design="..." :views="[[view, caption, link?], ...]">` theme component
(it applies the `/dais/` base; raw `<img src="/...">` would not).

## Design constraints from the owner

Rejected directions -- do not re-propose: plain pedestal/box, a thin V-groove, a two-volume
band+inset side, any engraving. Sides stay single-wall and sculpted. When asked for a geometry
change, keep the existing designs and add a variant unless told to replace one. Never set or
bump version numbers (`pyproject.toml` holds a `0.0.0` placeholder).
