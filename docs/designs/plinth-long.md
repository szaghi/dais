# Plinth, board behind the switch

`out/<board>/plinth-long/` -- **top-case**, **bottom-case**, **board-clamp**, **feet**

The [plinth](./plinth) with the board moved from under the switch to behind it. The plate no
longer stands on the board and its components, only on the switch pins and the wire gap over
the floor, so it drops **2.6 mm**. The key moves forward, 7 mm of top face in front of the hole
(`LONG_FRONT_BEZEL`), and the board clamp's front sits 2 mm behind the switch pins
(`LONG_PIN_GAP`).

| | Plinth | Plinth, board behind |
|---|---|---|
| Plate centre above the bottom | 18.5 mm | **15.9 mm** |
| Plan | 39.2 x 51.4 mm | **39.2 x 73.2 mm** |
| Height, front -> back | 22.9 -> 29.2 mm | **21.3 -> 30.3 mm** |

The saving is smaller than it looks: the 7 deg wedge rises over the longer case, so the back
ends up 1.1 mm *higher* than the plinth's, and the case is 22 mm deeper. It is lower only at
the front, where the key is.

<Views photo design="plinth-long" :views="[['hero', 'Render'], ['low', 'Low three-quarter']]" />

<Views design="plinth-long" :views="[['assembled', 'Assembled'], ['detail', 'Low three-quarter'], ['side', 'Side'], ['section', 'Section at x = 0 (back on the right)']]" />

<Views design="plinth-long" :views="[['plan', 'Plan (front at the bottom)'], ['front', 'Front'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded'], ['seam', 'Seam close-up'], ['base-board', 'Bottom case with board']]" />
