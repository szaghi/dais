# Split case

`out/<board>/split/` -- **top-case**, **bottom-case**, **plate**, **feet**

Two shells parted on a plane parallel to the top. The top case's lower edge is **2.0 mm above
the case bottom at the front** and rises 7 deg toward the back (7.5 mm at the back face), so the
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

- Four bottom-case corner columns (clearance holes) up to the lip top.
- Four top-case columns (blind pilots) from the rebate top **up to the underside of the top
  skin**, so nothing starts in mid-air when the top case prints top-down.
- Each screw tip stops 0.4 mm short of the end of its pilot (3.2 mm of thread). The seam is
  higher at the back, so the back counterbores are deeper (head seat 2.9 mm front, 7.0 mm
  back): all four screws are the same **M2x6** (`SPLIT_SCREW_L`; the build fails if a
  head would sink below the floor).

## USB-C and floor

The seam crosses the receptacle at the back, so the receptacle slot and a 12.5 mm plug notch
are cut through the back of **both** shells (a rectangular cut-out spanning the seam). The floor
is part of the bottom case: the same board pocket, front stop, pin-row grooves and feet
recesses as the one-piece bottom plate.

<Views design="split" :views="[['exploded', 'Exploded'], ['base-board', 'Bottom case with board'], ['back', 'Back (USB-C)'], ['underside', 'Top case from below']]" />
