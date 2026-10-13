# Options and patterns

Construction choices shared by every design. The defaults are what you get from `make build`;
each one can be switched from the command line, and `--legacy` rebuilds the first prototypes.

| Option | Default | Alternatives | Flag |
|---|---|---|---|
| Switch plate | **integrated** in the top shell | `separate` (screwed, 4x M2x4) | `--plate` |
| Case screws | **M3 heat-set inserts** + M3 button heads | `self-tap` (M2 self-tapping, printed pilots) | `--fastener` |
| Bevel angle | **60 deg** from horizontal | any; 45 = the first prototypes | `--bevel` |
| Skin pattern | none | `flutes`, `knurl`, `hex`, `ripple`, `all` (split designs) | `--pattern` |

```bash
dais build                                  # defaults -> out/microsam/<design>/
dais build --pattern knurl                  # -> out/microsam/split-knurl/, split-trapezoid-knurl/
dais build --pattern all --design split     # every pattern on the split case
dais build --legacy                         # separate plate, M2 self-tapping, 45 deg bevels
```

Each output directory carries an `options.json` recording what it was built with.

## Integrated switch plate

The plate is no longer a separate part screwed under the top skin: the top shell carries a
1.5 mm web with the 14 mm cutout, so the switch clips straight into the case and the four plate
screws disappear.

- **Printed top down without supports.** A flat ring stepping in from the 19.6 mm key well to
  the cutout would overhang 2.8 mm. Instead the well narrows in a **45 deg funnel** to 15.8 mm
  at the plate top (the MX top housing is 15.6 mm), leaving only the 0.9 mm switch seat as a
  short horizontal overhang.
- **Keycap clearance.** A fully pressed keycap (4 mm travel) clears the funnel by 0.5 mm per
  side in the conservative model used here; real Cherry-profile caps bottom out about 1 mm
  higher. The funnel corners are sharp on purpose: rounded ones would pinch the cap's corners.
- **Clips.** The web is exactly `PLATE_T` = 1.5 mm, as MX clips need. Set `SW_CUT` from the
  coupon as before.
- **Removing a switch** needs the case open: press the clips from below. A switch puller cannot
  reach them through the funnel.

<Views design="split" :views="[['section', 'Section: funnel, integrated plate, switch'], ['underside', 'Top case from below: the plate web and the insert columns']]" />

## Heat-set inserts

M3 heat-set inserts (hole 4.0 x 5.7 mm, Ruthex / CNC Kitchen style) are melted into the screw
columns from the open side, then the case closes with **M3 button-head** screws (ISO 7380,
head 5.7 x 1.65 mm), which sit in 1.8 mm counterbores.

| | Split designs | One-piece designs |
|---|---|---|
| Insert in | the 4 top-case columns (R4, from the rebate) | the 4 body bosses (R4, from below) |
| Screws | 4x M3x8, 5 mm in the insert | 4x M3x6, 4.3 mm in the insert |

Install them before assembly: soldering iron at about the filament's print temperature
(~250 deg C for ASA-CF), press straight in until flush, let it cool before loading. The columns
leave 2 mm of plastic around each hole.

## Bevels

The edges that print against the bed -- the top perimeter and the key-well rim of the top
shells, the bottom edge of the split bottom case -- are chamfered at **60 deg from
horizontal** instead of 45. On the bed each 0.2 mm layer then steps in 0.12 mm instead of
0.2 mm, so the bevel prints smoother and overhangs only 30 deg. Corner lifting (warping) is a
different defect: brim, enclosure, bed temperature.

## Skin patterns

Optional textures on the front and both sides of the split top case (the back, with the USB-C,
stays plain), 0.5 mm deep in the 3 mm wall, in a band parallel to the top. Each is shaped to
print top down without supports: no surface faces the bed at more than 45 deg, and the lower
groove ends ramp out at 56 deg (49 deg once the 7 deg print tilt is counted) instead of
stopping on a flat ceiling. The tests check every pattern for overhangs.

| Pattern | Geometry |
|---|---|
| `flutes` | vertical grooves, R1.0 cutter, 2.6 mm pitch |
| `knurl` | crossed 90 deg V-grooves at +-45 deg, 2.4 mm pitch: raised diamonds |
| `hex` | pointy-top hexagonal pockets, 3.0 mm across flats, 45 deg drafted walls, rows parallel to the top |
| `ripple` | wide shallow grooves (R4) swept along a gentle sine, parallel to the top |

<Views :views="[
  ['split-flutes/detail', 'flutes'],
  ['split-knurl/detail', 'knurl'],
  ['split-hex/detail', 'hex'],
  ['split-ripple/detail', 'ripple'],
]" />

<Views photo :views="[
  ['split-flutes/hero', 'flutes'],
  ['split-knurl/hero', 'knurl'],
  ['split-hex/hero', 'hex'],
  ['split-ripple/hero', 'ripple'],
]" />
