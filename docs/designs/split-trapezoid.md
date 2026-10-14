# Split case, trapezoidal plan

`out/<board>/split-trapezoid/` -- **top-case**, **bottom-case**, **board-clamp**, **feet**

The [split case](./split) with an isosceles-trapezoid plan: the back keeps its 43.6 mm width,
the front grows to **53.6 mm** (`TRAP_FRONT_EXTRA = 10`, each side angled ~6.4 deg in plan).
Seam, rounded rim, inset bottom case, lip in the rebate, integrated plate, M3 inserts, **M3x8**
screws and the [controller seat](./split#controller-seat-and-usb-c) are those of the split case
(51.4 mm deep). The rim, rebate, lip, cavity and screw axes all follow the angled sides: the screws
stay 5.5 mm from both walls of each corner.

<Views photo design="split-trapezoid" :views="[['hero', 'Render'], ['low', 'Low three-quarter'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded'], ['seam', 'The seam: rounded rim over the shadow step']]" />

The line drawings below are generated from the same geometry; the renders are Blender Cycles
with a display-only keycap and switch ([how](/guide/development#photo-renders)).

<Views design="split-trapezoid" :views="[['assembled', 'Assembled'], ['detail', 'Low three-quarter'], ['plan', 'Plan (front at the bottom)'], ['front', 'Front']]" />

<Views design="split-trapezoid" :views="[['side', 'Side'], ['back', 'Back (USB-C)'], ['exploded', 'Exploded'], ['section', 'Section at x = 0 (back on the right)'], ['seam', 'Seam close-up'], ['base-board', 'Bottom case with board']]" />
