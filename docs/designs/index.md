# The designs

Four variants of the same miniature keyboard. All share the 7 deg wedge, the sunken 1U well,
the edge breaks, the switch plate, the board seat and the feet; they differ in how the sides
are sculpted and how the case comes apart.

| Design | Shells | Sides | Plan | Screws |
|---|---|---|---|---|
| [Side coves](./side-cove) | body + flush bottom plate | a teardrop cove on each side | 43.6 x 44.8 mm | 4x M2x8 |
| [Wrap cove](./wrap-cove) | body + flush bottom plate | one cove along front, corners and sides | 43.6 x 44.8 mm | 4x M2x8 |
| [Split case](./split) | top case + inset bottom case | the seam: rounded rim over a 1 mm shadow step | 43.6 x 44.8 mm | 4x M2x6 |
| [Split, trapezoidal](./split-trapezoid) | top case + inset bottom case | as the split case | front 53.6, back 43.6 x 44.8 mm | 4x M2x6 |

All four: height 19.7 mm at the front, 25.2 mm at the back, +0.8 mm of feet.

## Side by side

<Views photo :views="[
  ['side-cove/hero', 'Side coves', './side-cove'],
  ['wrap-cove/hero', 'Wrap cove', './wrap-cove'],
  ['split/hero', 'Split case', './split'],
  ['split-trapezoid/hero', 'Split case, trapezoidal plan', './split-trapezoid'],
]" />

## One-piece or split?

- **One-piece** (side coves, wrap cove): one large body printed top-down, closed from below by
  a flush 3.5 mm bottom plate that carries the board. The cove is the decoration; the bottom
  plate's joint hides underneath.
- **Split**: the top case takes nearly all the height and the bottom case shows only a 2 mm
  band at the front. The parting line is designed rather than hidden -- a convex R1.5 rim over a
  1 mm shadow step, all the way round -- and the board sits in the bottom case's floor, so the
  electronics are open on the bench until the top case closes over them.

Every design directory under `out/<board>/` is a complete print set; the shared parts (plate,
feet, bottom plate) are duplicated into each, so any one of them prints alone.

## The views

Every design page shows the same set of drawings, rendered from the exported geometry by
`dais render`. The switch, keycap, board and USB-C plug are box **envelopes** for fit
checking, not printed parts.
