# Printing

Every part is exported in **assembly position**: rotate it onto the bed in the slicer as listed.
The shells are **ASA-CF** (it needs a **hardened** nozzle); the feet are **TPU**. Bevels on the
bed are 60 deg from horizontal ([why](/designs/options#bevels)).

## Orientation

| Part | Designs | Orientation | Notes |
|---|---|---|---|
| `body` | side-cove, wrap-cove | **top face on the bed** (rotate -7 deg about X, flip) | no supports: walls lean 7 deg, the cove lip is ~48 deg, the bosses grow from the top skin, the USB-C slot is a 10 mm bridge; the top gets the bed finish |
| `top-case` | split, split-trapezoid, plinth, plinth-long | **top face on the bed** (rotate -7 deg about X, flip) | no supports: every screw column grows from the top skin; open at the parting plane |
| `bottom` | side-cove, wrap-cove | bottom face down | |
| `bottom-case` | split, split-trapezoid, plinth, plinth-long | floor down | the lip top is tilted 7 deg (hidden inside); the rear jaws overhang 30 deg from vertical |
| `board-clamp` | split, split-trapezoid, plinth, plinth-long | **upside down** (top on the bed) | no supports; melt the M3 insert in from the open underside |
| `plate` | `--legacy` / `--plate separate` only | flat, on its face | as dimensionally true as the coupon |
| `feet` | all | flat | TPU; glued into the bottom recesses |
| `coupon` | -- | flat | print **first** |

::: tip Why top-down
The top face is the one you see and touch: printed on the bed it gets the bed's finish and its
chamfered edges come out crisp. The price is that every internal feature must grow from the top
skin -- a boss or column that stopped short of it would start in mid-air. The test suite
checks the top shells for downward-facing faces on every run.
:::

## Switch-fit coupon

`coupon/` holds four 1.5 mm test plates with 13.9, 14.0, 14.1 and 14.2 mm cutouts, each with
its size engraved. Print it in the plate's material and orientation, clip the switch into each,
and set `SW_CUT` in `src/dais/params.py` to the tightest one it clips into **fully**.
Then rebuild.

The integrated plate's cutout prints in the same orientation as the coupon (flat, in the XY
plane), so the coupon result transfers directly.

<Views design="common" :views="[['coupon', 'Switch-fit coupon']]" />

## Clearances

| Fit | Clearance | Constant |
|---|---|---|
| Bottom plate in the body opening | 0.2 mm per side | `BOTTOM_FIT` |
| Board in its pocket (one-piece, `--seat pocket`) | 0.3 mm total | `BOARD_FIT` |
| Board in the generic seat (split, plinth) | none: clamped; any board of the ranges | `SEAT_*` |
| Lip in the rebate (split) | 0.15 mm per side | `LIP_FIT` |
| Pressed keycap in the funnel | 0.5 mm per side (conservative) | `FUNNEL_BOTTOM` |
| Heat-set insert hole | 4.0 x 5.7 mm (M3) | `FASTENERS["insert"]` |
| Plate corners around the body bosses (separate plate) | 0.4 mm | `PLATE_RELIEF` |
| USB-C receptacle in the slot (one-piece, `--seat pocket`) | 0.6 mm total | `USB_SLOT_FIT` |
| USB-C window round the plug overmold (generic seat) | 0.3 mm per side | `USB_WINDOW_PLAY` |

If your printer runs tight or loose, these are the constants to adjust.
