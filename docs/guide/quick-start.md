# Quick start

## Generate the case

Requires Python 3.10+.

```bash
make dev      # .venv + editable install of dais (build123d, pytest, ruff)
make build    # build, check and export every design -> out/microsam/
```

`make build` runs `dais build --board microsam --clean`. Each design is built in its own
process, checked (valid solids, no floating features, no part clashing with another), and
exported twice: `.stl` for the slicer, `.step` for CAD (exact geometry, editable in
FreeCAD / Fusion / Onshape).

```text
out/microsam/
├── side-cove/        {stl,step}/  body  bottom  feet          + options.json
├── wrap-cove/        {stl,step}/  body  bottom  feet
├── split/            {stl,step}/  top-case  bottom-case  feet
├── split-trapezoid/  {stl,step}/  top-case  bottom-case  feet
└── coupon/           {stl,step}/  coupon
```

Each design directory is a complete print set: pick one design and print its `stl/`. Parts are
exported in **assembly position**; the [printing guide](/guide/printing) gives each one's
orientation on the bed.

### Options

```bash
dais list                                   # the designs
dais build --design split --design split-trapezoid
dais build --board rp2040zero               # -> out/rp2040zero/
dais render                                 # SVG views -> docs/public/img/
```

| Option | Effect |
|---|---|
| `--board microsam\|rp2040zero` | controller profile the case is sized around (default `microsam`) |
| `--design NAME` | only this design; repeatable (default: all four) |
| `--out DIR` | output root (default `out` for `build`, `docs/public/img` for `render`) |
| `-j N` | parallel processes (default: one per CPU) |
| `--clean` | `build` only: remove `<out>/<board>/` first, so no stale part survives |
| `--pattern NAME\|all` | skin pattern on the split top case -> `<design>-<pattern>/` ([options](/designs/options)) |
| `--plate`, `--fastener`, `--bevel`, `--legacy` | construction options ([options](/designs/options)) |

## Print order

1. **`coupon/`** first: four 1.5 mm test plates with 13.9 / 14.0 / 14.1 / 14.2 mm cutouts. Set
   `SW_CUT` to the tightest one your switch clips into fully, then rebuild.
2. One design directory, oriented as the [printing guide](/guide/printing) lists.

## Flash and assemble

[Firmware](/guide/firmware) gets QMK onto the board; [assembly](/guide/assembly) covers the
bill of materials, wiring and the order of operations. Before soldering, check the
[status page](/guide/status): a few dimensions are still waiting for calipers.
