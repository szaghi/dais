# Wrap cove

`out/<board>/wrap-cove/` -- **body**, **bottom**, **plate**, **feet**

The [side-cove](./side-cove) body with one **continuous cove** instead of two. The same R3
ball cutter runs along the front wall, turns both R3 front corners at constant depth (a torus
quarter around each corner axis), then follows each side, rising with the top and drifting
outward until it runs out 4.5 mm before the back -- no interruption at the corners.

<Views photo design="wrap-cove" :views="[['hero', 'Render'], ['low', 'Low three-quarter'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded']]" />

The line drawings below are generated from the same geometry; the renders are Blender Cycles
with a display-only keycap and switch ([how](/guide/development#photo-renders)).

<Views design="wrap-cove" :views="[['assembled', 'Assembled'], ['detail', 'Low three-quarter'], ['front', 'Front'], ['side', 'Side']]" />

## Cove

| | |
|---|---|
| Cutter | R3 ball, 1.0 mm deep along the front and round the corners |
| Height | lower edge 5.0 mm above the case bottom on the front face; the side runs rise 7 deg with the top |
| Ends | each side run drifts out and runs out 4.5 mm before the back face |

Everything else -- body, bosses, bottom plate, USB-C, **4x M2x8** screws -- is the
[side-cove](./side-cove) design.

<Views design="wrap-cove" :views="[['exploded', 'Exploded'], ['section', 'Section at x = 0 (back on the right)'], ['back', 'Back (USB-C)'], ['plan', 'Plan']]" />
