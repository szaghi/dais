# Development

## Make targets

| Target | Does |
|---|---|
| `make dev` | `.venv` + editable install with the dev extras (pytest, pytest-cov, ruff) |
| `make build` | `dais build --clean`: every design -> `out/$(BOARD)/` (default `BOARD=microsam`) |
| `make render` | `dais render`: the SVG views -> `docs/public/img/` |
| `make params` | regenerate [Parameters](/guide/parameters) from `params.py` |
| `make test` | pytest with coverage |
| `make lint` / `make fmt` | ruff check + format check / auto-fix + format |
| `make docs` / `make docs-dev` | build / serve this documentation (Node.js + npm) |
| `make clean` | remove caches, build artifacts and `out/` |

```bash
.venv/bin/pytest tests/test_geometry.py::test_top_case_prints_without_supports   # one test
make build BOARD=rp2040zero
```

## Tests

The tests build every design once per session (about 10 s) and check what the build-time
`check()` cannot:

| Test | Guards |
|---|---|
| `test_golden_volumes` | every part's volume against `tests/golden_volumes.json`: any unintended geometry change fails |
| `test_top_case_prints_without_supports` | no downward-facing face inside the split top cases in print orientation |
| `test_body_only_overhang_is_the_usb_bridge` | the one-piece body's only overhang is the bridged USB-C slot roof |
| `test_plate_relief_clears_every_body_boss` | 0.4 mm around all four bosses (a silent OCC cut failure once missed one) |
| `test_split_columns_clear_the_plate` | > 1 mm between the plate and the top-case columns |
| `test_build_writes_design_tree` | the `out/<board>/<design>/{stl,step}/` layout |
| `test_params_page_lists_every_constant` | the parameters page covers `params.py` |

### After an intended geometry change

The golden-volume test fails by design. Check the change in the views (`make render`), then
regenerate the reference:

```bash
.venv/bin/python tests/test_geometry.py     # rewrites tests/golden_volumes.json
```

## Photo renders

`dais photo` (or `make photo`) renders each design through **Blender Cycles** into
`docs/public/photo/<design>/<shot>.webp`: `hero`, `low`, `back`, `exploded`, plus `seam` for the
split designs. Dark-grey ASA-CF shells with faint layer lines, a white display-only Cherry-profile
keycap (`display.py`), a shadow-catcher floor laid over a light backdrop.

```bash
dais photo --preview --design split --shot hero     # 800x600, 24 samples: seconds
dais photo                                          # 1600x1200, 128 samples, every design
```

| Option | Default | |
|---|---|---|
| `--threads` | 8 | Cycles CPU threads |
| `--memory` | `2G` | hard RAM cap of the Blender process |
| `--tiles` | 2 (preview 1) | render and denoise as N x N overlapping crops: bounds the denoiser's memory |
| `--samples` | 128 (preview 24) | |
| `--blender` | `$DAIS_BLENDER`, PATH, `/opt/blender/*/blender` | |

The renders are built never to disturb other work on the machine:

- **The GPU is invisible to Blender.** It runs in a private user + mount namespace where the WSL
  GPU device (`/dev/dxg`, or `/dev/nvidia*` on native Linux) is bound to `/dev/null` and the WSL
  driver libraries (`/usr/lib/wsl`) are an empty tmpfs; Cycles logs `CUEW initialization failed`
  and has no GPU device at all. `CUDA_VISIBLE_DEVICES=""` and CPU-only Cycles settings are kept
  as further layers. Only Cycles in background mode is used: EEVEE/Workbench would need OpenGL.
- **RAM is capped** with a systemd user scope (`MemoryMax`, no swap): over the cap the render
  is killed, not your other jobs. The peak is the denoiser (OIDN), whose memory scales with the
  pixels it sees at once: a whole 1600 x 1200 frame reaches ~1.9 GiB, so finals render as
  `--tiles 2` -- four crops with a 48 px overlap, denoised separately and stitched with linear
  blends -- and peak at ~0.75 GiB for ~30% more time. Previews (800 x 600) use one tile.
- **CPU priority is the lowest** (`nice -n 19`) with a fixed thread count.

Meshes and the scene description go to `out/<board>/photo-work/`; `blender_scene.py` runs inside
Blender's own Python and reads only that JSON.

## Changing the design

- **A look or fit dimension**: edit the constant in `params.py`, then `make build test render params`.
- **A new design**: add a `Design` to `designs.DESIGNS`; the CLI, the output tree and the
  renderer pick it up. Add its page under `docs/designs/` and its entry in the sidebar.
- **A new board**: add a `Board` to `params.BOARDS` with caliper numbers.

Keep the existing designs when exploring a new direction: add a variant rather than replacing
one.
