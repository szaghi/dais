# Side coves

`out/<board>/side-cove/` -- **body**, **bottom**, **feet**

A one-piece wedge with one **teardrop cove** on each side, after the Baionlenja Larva: a
ball-cutter pass plunged near the front (round head) that drifts outward until it runs out near
the back (long tapering tail). The cove runs parallel to the top and is centred along the side,
4.5 mm clear of both the front and the back face.

<Views photo design="side-cove" :views="[['hero', 'Render'], ['low', 'Low three-quarter'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded']]" />

The line drawings below are generated from the same geometry; the renders are Blender Cycles
with a display-only keycap and switch ([how](/guide/development#photo-renders)).

<Views design="side-cove" :views="[['assembled', 'Assembled'], ['detail', 'Low three-quarter'], ['side', 'Side'], ['front', 'Front']]" />

## Cove

| | |
|---|---|
| Cutter | R3 ball (`COVE_BALL`) |
| Depth | 1.0 mm at the head (`COVE_DEPTH`): ~4.5 mm wide on the face |
| Height | lower edge 5.0 mm above the case bottom on the front face (`COVE_BOTTOM`), axis rising 7 deg with the top |
| Ends | 4.5 mm from the front and back faces (`COVE_MARGIN`) |
| Print | the cove's upper lip is a ~48 deg overhang: no supports |

## Body and bottom plate

- **Body**: top skin with the key well and the [integrated switch plate](./options#integrated-switch-plate), the coves, four corner
  bosses running from the bottom plate **up to the top skin** (printed top down, nothing starts
  in mid-air), and the USB-C receptacle slot with an overmold recess open through the bottom edge.
- **Bottom plate**: 3.5 mm, flush inside the body opening with 0.2 mm clearance per side; board
  pocket, front stop (takes the cable insertion force), pin-row grooves for the solder joints,
  feet recesses, four M3 clearance holes with counterbores.
- Closed with **4x M3x6** button-head screws into M3 heat-set inserts in the bosses
  ([options](./options#heat-set-inserts); `--legacy`: M2x8 self-tapping).

<Views design="side-cove" :views="[['exploded', 'Exploded'], ['section', 'Section at x = 0 (back on the right)'], ['underside', 'Body from below'], ['base-board', 'Bottom plate with board']]" />

What to look for in the section: the switch axis tilted 7 deg; the plate web and its funnel
under the top skin; >= 3.5 mm between the lowest switch point and the board parts; the board in its pocket
with the front stop on the left; the USB-C reaching through the back wall.

<Views design="side-cove" :views="[['back', 'Back (USB-C)'], ['plan', 'Plan']]" />
