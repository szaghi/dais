# Status

All four designs build, pass the geometric checks and are ready for prototype prints. A few
inputs are still placeholders; each one is a single constant in
`src/dais/params.py`, marked `MEASURE`.

## Open items

| # | Item | Constant | Default | How |
|---|---|---|---|---|
| 1 | Switch plate cutout | `SW_CUT` | 14.0 mm | print `coupon/`, take the tightest cutout the switch clips into fully |
| 2 | USB-C cable overmold | `PLUG_W`, `PLUG_H` | 12.5 x 7.5 mm | calipers on the cable you will use |
| 3 | Tallest part on the microSAM under the switch | `COMP_H` | 1.6 mm | calipers; it sets the plate height and so the whole case height |
| 4 | USB-C centre height | -- | ~3.6 mm | board flat on the table, centre of the opening above it |
| 5 | microSAM pinout | -- | RP2040 CE assumed | flash, short A3-A2 with tweezers, confirm an Enter keypress **before** soldering |

::: warning microSAM pinout is an inference
The microSAM is sold as "Elite-C compatible"; that its pads follow the RP2040 Community
Edition map is inferred, not verified from a datasheet. Item 5 is the check.
:::

## Prototype checks

Things only a print can confirm:

- the plate's corner reliefs against the one-piece body bosses (0.4 mm design clearance);
- the split cases' lip in the rebate (0.15 mm per side) and the screw columns against the plate;
- the trapezoid's angled walls printing cleanly top-down.

The RP2040-Zero profile uses datasheet numbers only; measure the board before printing for it.
