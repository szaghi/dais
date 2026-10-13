"""Every tunable dimension of the case, in mm and degrees, and the supported controller boards.

Look constants shape the case; fit constants follow the hardware. Values marked MEASURE are
placeholders waiting for calipers or the switch-fit coupon.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Align

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX = (Align.CENTER, Align.CENTER, Align.MAX)


@dataclass(frozen=True)
class Board:
    """Controller board envelope, component side up, USB-C at +Y."""

    length: float  # Y, along the USB axis
    width: float  # X
    pcb_t: float
    usb_w: float  # USB-C receptacle width
    usb_h: float  # USB-C receptacle height above the PCB top
    usb_overhang: float  # receptacle face beyond the PCB back edge
    pin_row_x: float | None  # half-spacing of through-hole pin rows (solder joints below), None if castellated only


BOARDS = {
    # Khor microSAM: RP2040, Pro Micro / Elite-C footprint, top-mount USB-C. Calipers, 2026-10-12.
    "microsam": Board(length=34.6, width=18.4, pcb_t=1.6, usb_w=9.0, usb_h=4.0, usb_overhang=2.0, pin_row_x=7.62),
    # Waveshare RP2040-Zero, datasheet nominal. All MEASURE.
    "rp2040zero": Board(length=23.5, width=18.0, pcb_t=1.0, usb_w=8.94, usb_h=3.26, usb_overhang=0.0, pin_row_x=None),
}

# --- Look -------------------------------------------------------------------------
TILT = 7.0  # typing angle, deg
BEZEL = 12.0  # top face beyond the key well, left/right (front/back grow with the board)
WELL = 19.6  # key well opening: 1U cap (18.0-18.4) + ~0.6 per side
WELL_DEPTH = 4.0  # top face above the plate top: the cap sits sunk in the well
WELL_R = 1.0  # well corner radius
WELL_RIM = 0.5  # 45 deg chamfer on the well rim
TOP_EDGE = 0.8  # 45 deg chamfer, top perimeter (on the bed when printing)
R_CORNER = 3.0  # vertical body corners
BOTTOM_EDGE = 1.2  # 45 deg chamfer, bottom perimeter
# cove: a ball cutter plunged near the front, drifting outward until it runs out at the back --
# a teardrop with a round head at the front and a long tapering tail, parallel to the top
COVE_BOTTOM = 5.0  # lower edge of the cove on the front face, above the case bottom
COVE_DEPTH = 1.0  # at the head
COVE_BALL = 3.0  # cutter radius: with COVE_DEPTH sets the head width (~4.5 mm), ~48 deg print overhang
COVE_MARGIN = 4.5  # visible gap between each cove end and the nearest face edge (centres the cove)

# --- Switch and plate ------------------------------------------------------------
SW_CUT = 14.0  # plate cutout, set from the coupon test
PLATE_T = 1.5  # MX clips lock on 1.5 mm, do not change
PLATE = 28.0  # square plate size
PLATE_SCREW = 11.8  # +-x, +-y of the plate screws in the key frame
PLATE_RELIEF = 0.4  # plate corner relief clearance around the one-piece body bosses
SW_HALF = 7.0  # half-width of the switch bottom housing
SW_BELOW = 5.0  # plate top -> bottom of switch housing
SW_PINS = 3.3  # pin length below the housing
SW_PIN_Y = 5.08  # farthest pin from the switch centre
WIRE_GAP = 3.5  # free height between the lowest switch point and the board parts

# --- Board seat -------------------------------------------------------------------
BOTTOM_T = 3.5  # bottom plate / floor thickness
BOTTOM_FIT = 0.2  # clearance per side, bottom plate in the body opening
BOARD_FIT = 0.3  # total clearance of the board pocket
POCKET_D = 0.6  # board pocket depth
COMP_H = 1.6  # tallest part on the board top under the switch, MEASURE
STOP_T = 1.5  # front stop: takes the cable insertion force
JOINT_GROOVE_W = 2.6  # clearance under each through-hole pin row
JOINT_GROOVE_D = 1.2

# --- USB-C cable plug ------------------------------------------------------------
PLUG_W = 12.5  # overmold recess, MEASURE your cable's overmold
PLUG_H = 7.5
USB_SLOT_FIT = 0.6  # clearance around the receptacle in the wall slot
USB_WALL_LEFT = 0.6  # wall left where the receptacle face sits

# --- Shell and fasteners -------------------------------------------------------------
WALL = 3.0
BOSS_R = 3.0
BOSS_H = 8.0  # pilot depth into the one-piece body bosses (the bosses run up to the roof)
BOSS_INSET = 3.2  # boss centre from the inner wall: keeps the counterbores inside the bottom plate
SCREW_PILOT = 1.7  # M2 self-tapping pilot
SCREW_CLEAR = 2.4
SCREW_HEAD_D = 4.2
SCREW_HEAD_H = 1.8

# --- Split designs: bottom case inserted into the top case -------------------------
SPLIT_STEP = 1.0  # bottom case outer face inside the top case outer face (the shadow step)
RIM_WALL = 1.8  # top case wall over the rebate
RIM_R = 1.5  # convex round on the top case's lower outer edge
REBATE_H = 3.0  # rebate height inside the top case, above the parting plane
LIP_T = 1.2  # bottom case lip thickness (slides into the rebate)
LIP_FIT = 0.15  # clearance per side, lip in the rebate
LIP_TOP_GAP = 0.2  # lip top below the rebate top
SPLIT_BOSS_INSET = 2.5  # screw axis from the inner wall (bottom-case columns fuse into the wall)
TOP_BOSS_R = 2.5  # top-case screw column
SPLIT_FRONT_Z = 2.0  # top case lower edge on the front face, above the case bottom (seam rises TILT)
SPLIT_SCREW_L = 6.0  # all four M2 screws the same length: deeper counterbores where the seam is higher
SPLIT_SCREW_ENGAGE = 4.0  # thread engagement in the top-case column
TRAP_FRONT_EXTRA = 10.0  # trapezoid plan: front this much wider than the back (sides ~6.4 deg)

# --- Feet ------------------------------------------------------------------------------
FOOT_W = 6.0
FOOT_T = 1.4  # TPU strip thickness
FOOT_RECESS = 0.6  # recess depth: strips stand 0.8 mm proud
FOOT_INSET = 5.0  # strip centre-line distance from the bottom plate front/back edge
