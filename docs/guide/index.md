# About

DAIS -- **D**esktop **A**ssignable **I**nput **S**witch -- is a one-key MX macropad. A dais is a
raised platform for something on display: here, a single key, standard or artisan, sunk in a
well on a small wedge. It pairs a Khor **microSAM** controller (RP2040, Pro Micro / Elite-C
footprint, USB-C), the upstream **QMK** `handwired/onekey` firmware, and a 3D-printed case
generated in Python with [build123d](https://build123d.readthedocs.io).

<Views design="split-trapezoid" :views="[['assembled', 'Split case, trapezoidal plan'], ['detail', 'Low three-quarter']]" />

## Design language

A miniature keyboard rather than a box:

- **A wedge at a 7 deg typing angle** -- the top face, the switch plate and the switch axis all
  share the tilt; front and back faces stay vertical.
- **The key sunk in a 1U well** inside wide bezels (12 mm left and right), the way keys sit
  below the rim of a top-mount case. The cap rises out of a 19.6 mm well, 4 mm deep, with a
  0.5 mm chamfer on its rim.
- **Crisp edge breaks**: R3 vertical corners, a 0.8 mm chamfer on the top perimeter, 1.2 mm
  on the bottom perimeter.
- **Single-wall, sculpted sides, never engravings.** The side profile follows the Baionlenja
  Gehirn without its engravings; the sculpting is either a ball-cutter cove (after the
  Baionlenja Larva) or, in the split designs, the seam itself.

Four [designs](/designs/) explore that language; they share the same key well, plate, board
seat and feet.

## Hardware

| | |
|---|---|
| Controller | Khor microSAM: RP2040, Pro Micro / Elite-C footprint, top-mount USB-C. Measured: 34.6 x 18.4 mm, PCB 1.6 mm, receptacle 9.0 x 4.0 mm, 2.0 mm past the board edge. Alternative: Waveshare RP2040-Zero (`--board rp2040zero`, datasheet nominal). |
| Switch | any MX, 3- or 5-pin, plate-mounted (no PCB), wired straight to two pads |
| Firmware | upstream QMK `handwired/onekey`, keymap `enter` (`KC_ENT` + bootmagic) |
| Case | ASA-CF shells and plate, TPU feet, M2 self-tapping screws |

## Repository layout

| Path | Content |
|---|---|
| `src/dais/` | the parametric case: parameters, layout, the designs, checks, CLI, renderer |
| `tests/` | geometric acceptance tests and the golden-volume regression guard |
| `firmware/keymaps/enter/` | the QMK keymap, copied into a QMK checkout to build |
| `docs/` | this documentation (VitePress); `docs/public/img/` holds the rendered views |
| `out/` | generated STL + STEP, one directory per board and design (not versioned) |
