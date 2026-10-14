# Plinth

`out/<board>/plinth/` -- **top-case**, **bottom-case**, **feet**

The [split case](./split) reshaped round the keycap: the top face rises to the keycap's base
line, so the switch housing disappears and an artisan sits *on* the case instead of floating
above it.

| | Split case | Plinth |
|---|---|---|
| Top face above the plate | 4.0 mm | **7.5 mm** (`ARTISAN_TOP`) |
| Key hole | 19.6 mm | **20.2 mm** (`ARTISAN_WELL`) |
| Bezel left/right | 12.0 mm | **9.5 mm** (`PLINTH_BEZEL`) |
| Top-perimeter chamfer | 0.8 mm | **2.5 mm** at 60 deg (`PLINTH_EDGE`) |
| Plan | 43.6 x 44.8 mm | **39.2 x 44.8 mm** |
| Height, front -> back | 19.7 -> 25.2 mm | **23.3 -> 28.8 mm** |

- **Sized from the artisan.** Measured: 19.0 mm wide in its lower 4-5 mm, its base 8.0 mm above
  the plate at rest. The top face stops 0.5 mm under it; pressed (4 mm travel), the base drops
  into the hole. The hole walls are straight down to 2.2 mm above the plate, then the usual 45
  deg funnel: 0.6 mm clearance per side on the flats, 0.43 mm at the R1 corners. A standard
  Cherry-profile keycap sits about 2 mm deep in the hole.
- **Why the case is taller.** The board sits under the switch, so the plate height is fixed by
  the switch pins, the wire gap and the board stack; a higher top face means a taller case.
  The [board-behind plinth](./plinth-long) trades that height for depth.
- **Why the bezel stops at 9.5 mm.** The R4 heat-set insert columns stand in the corners,
  beside the board pocket; a narrower case would put them over the board.
- **The large chamfer** catches the light along the top perimeter, so the slab reads thinner.
- The top skin above the plate is 7.5 mm of solid plastic, about 17.8 cm^3 for the top case
  against 14.5 for the split case.

Seam, rounded rim, inset bottom case, integrated plate, M3 inserts and M3x8 screws are those of
the split case, and so are the [skin patterns](./options#skin-patterns): `dais build --design
plinth --pattern voronoi-full`.

<Views photo design="plinth" :views="[['hero', 'Render'], ['low', 'Low three-quarter']]" />

<Views design="plinth" :views="[['assembled', 'Assembled'], ['detail', 'Low three-quarter'], ['side', 'Side'], ['section', 'Section at x = 0 (back on the right)']]" />

<Views design="plinth" :views="[['plan', 'Plan (front at the bottom)'], ['front', 'Front'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded'], ['seam', 'Seam close-up'], ['base-board', 'Bottom case with board']]" />

## With the full-side skin

<Views :views="[['plinth-voronoi-full/detail', 'voronoi-full'], ['plinth-facets-full/detail', 'facets-full'], ['plinth-voronoi-full/back', 'voronoi-full, back'], ['plinth-facets-full/back', 'facets-full, back']]" />

<Views photo :views="[['plinth-voronoi-full/hero', 'voronoi-full'], ['plinth-voronoi-full/back', 'voronoi-full, back (USB-C)'], ['plinth-facets-full/hero', 'facets-full'], ['plinth-facets-full/back', 'facets-full, back (USB-C)']]" />
