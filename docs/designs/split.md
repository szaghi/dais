# Split case

`out/<board>/split/` -- **top-case**, **bottom-case**, **board-clamp**, **feet**

Two shells parted on a plane parallel to the top. The top case's lower edge is **2.0 mm above
the case bottom at the front** and rises 7 deg toward the back (8.3 mm at the back face), so the
top case takes nearly all the height and only a 2 mm band of the bottom case shows at the front
(0.8 mm of face above the 1.2 mm base chamfer). There is no cove: the joint itself is the feature.

<Views photo design="split" :views="[['hero', 'Render'], ['low', 'Low three-quarter'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded'], ['seam', 'The seam: rounded rim over the shadow step']]" />

The line drawings below are generated from the same geometry; the renders are Blender Cycles
with a display-only keycap and switch ([how](/guide/development#photo-renders)).

<Views design="split" :views="[['assembled', 'Assembled'], ['detail', 'Low three-quarter'], ['side', 'Side'], ['front', 'Front']]" />

## The seam

- **Top case** -- its lower outer edge is a **convex R1.5 round** (`RIM_R`). Inside, the wall is
  thinned to 1.8 mm (`RIM_WALL`) over the lowest 3 mm (`REBATE_H`): a rebate.
- **Bottom case** -- shrunk in plan so its outer face sits **1.0 mm inside** the top case's
  outer face (`SPLIT_STEP`); that step under the rounded rim is the shadow line, all the way
  round. Its upper edge continues as a 1.2 mm **lip inserted into the rebate** (0.15 mm
  clearance per side, 0.2 mm below the rebate top), so the shells locate on each other.

<Views design="split" :views="[['seam', 'Seam close-up: front wall cut at x = 0, outside on the left'], ['section', 'Section at x = 0 (back on the right)']]" />

## Fasteners

- Four bottom-case corner columns (R4, M3 clearance holes) up to the lip top.
- Four top-case columns (R4) from the rebate top **up to the underside of the top skin**, so
  nothing starts in mid-air when the top case prints top-down; each takes an **M3 heat-set
  insert** (hole 4.0 x 5.7 mm) from the open bottom.
- Each screw tip ends 5 mm into its insert. The seam is higher at the back, so the back
  counterbores are deeper (head seat 2.7 mm front, 6.8 mm back): all four screws are the same
  **M3x8** button heads (the build fails if a head would sink below the floor).
- `--legacy`: printed M2 pilots and M2x6 self-tapping screws instead. See
  [Options](./options#heat-set-inserts).

The switch plate is part of the top case: the key well narrows in a 45 deg funnel to the
1.5 mm web that the switch clips into ([integrated plate](./options#integrated-switch-plate)).
Optional [skin patterns](./options#skin-patterns) decorate the front and the sides.

## Skin patterns

The split top case takes optional textures: on its front and sides as a band, or over all four
walls (`-full`). Build them with `dais build --pattern <name>`; details and printing
notes in [Options and patterns](./options#skin-patterns).

<Views photo :views="[
  ['split-voronoi/hero', 'voronoi', './options#voronoi-leather-cells'],
  ['split-voronoi-full/hero', 'voronoi-full', './options#full-side-versions'],
  ['split-facets/hero', 'facets', './options#facets-faceted-panel'],
  ['split-facets-full/hero', 'facets-full', './options#full-side-versions'],
  ['split-fuzzy/hero', 'fuzzy (slicer modifier)', './options#fuzzy-fuzzy-skin-done-by-the-slicer'],
  ['split-fuzzy-full/hero', 'fuzzy-full (slicer modifier)', './options#full-side-versions'],
]" />

## Controller seat and USB-C

The bottom case takes **any Pro Micro-style board with a top-mount USB-C**, not just the
microSAM. The board is clamped, not fitted:

| Range | |
|---|---|
| PCB length | 32.5 - 35.5 mm (`SEAT_LEN`) |
| PCB width | 16.8 - 20.0 mm (`SEAT_W`) |
| PCB thickness | 1.0 - 1.6 mm (`SEAT_PCB_T`) |
| USB-C height above the PCB | 3.2 - 4.0 mm (`SEAT_USB_H`), any overhang up to ~2.5 mm |

- **Rear jaws.** Two wedges beside the USB-C take the PCB's back corners. Their faces are angled
  30 deg in plan (`JAW_PLAN`), so a corner slides toward the centre line whatever the board's
  width, and lean 60 deg over the PCB (`JAW_LEAN`), so they press its top edge down whatever its
  thickness. The lean stops 1 mm above the PCB: the corner pins stay free for wires.
- **Front clamp** (`board-clamp`, a separate part). The same faces on two horns push the front
  corners back into the jaws. It carries an M3 heat-set insert and slides in a slot in the floor;
  one **M3x6** button head from below locks it. Push it against the board, tighten: done. The
  slot covers the whole range, from the longest and widest board to the shortest and narrowest.
- **The USB-C window** is plug-sized (12.5 + 2 x 0.3 mm wide, `PLUG_W`) and goes through the
  whole back wall: the bottom case forms its lower part, the top case closes it from above. There
  is no bridge over the receptacle any more, and the receptacle can sit anywhere in it: the jaws
  centre it, its overhang only changes how far in it sits (the microSAM's face is 1.5 mm inside).
- The floor keeps the pocket (now wide enough for any board of the range) and the solder-joint
  grooves under the Pro Micro pin rows. The front foot is split in two round the screw head.
- The clamp's travel costs depth: the split designs are 51.4 mm deep (44.8 with the fitted
  pocket of the first prototypes, `--seat pocket`, which `--legacy` uses).

<Views design="split" :views="[['base-board', 'Bottom case with board and clamp'], ['back', 'Back: the USB-C window across the seam']]" />

<Views design="split" :views="[['exploded', 'Exploded'], ['underside', 'Top case from below']]" />


