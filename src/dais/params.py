"""Every tunable dimension of the case, in mm and degrees, and the supported controller boards.

Look constants shape the case; fit constants follow the hardware. Values marked MEASURE are
placeholders waiting for calipers or the switch-fit coupon.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
WELL_RIM = 0.5  # chamfer on the well rim: height (the run follows Options.bevel)
TOP_EDGE = 0.8  # chamfer, top perimeter (on the bed when printing): height
R_CORNER = 3.0  # vertical body corners
BOTTOM_EDGE = 1.2  # chamfer, bottom perimeter (on the bed for the split bottom case): height
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

# --- Integrated switch plate ---------------------------------------------------------
FUNNEL_BOTTOM = 15.8  # well narrows at 45 deg to this at the plate top (MX top housing 15.6)
PLATE_SCREW_PILOT = 1.7  # separate plate only: M2 self-tapping pilots in the top skin
PLATE_SCREW_CLEAR = 2.4  # separate plate only: M2 clearance holes in the plate

# --- Shell and fasteners -------------------------------------------------------------
WALL = 3.0

# --- Split designs: bottom case inserted into the top case -------------------------
SPLIT_STEP = 1.0  # bottom case outer face inside the top case outer face (the shadow step)
RIM_WALL = 1.8  # top case wall over the rebate
RIM_R = 1.5  # convex round on the top case's lower outer edge
REBATE_H = 3.0  # rebate height inside the top case, above the parting plane
LIP_T = 1.2  # bottom case lip thickness (slides into the rebate)
LIP_FIT = 0.15  # clearance per side, lip in the rebate
LIP_TOP_GAP = 0.2  # lip top below the rebate top
SPLIT_BOSS_INSET = 2.5  # screw axis from the inner wall (bottom-case columns fuse into the wall)
SPLIT_FRONT_Z = 2.0  # top case lower edge on the front face, above the case bottom (seam rises TILT)
TRAP_FRONT_EXTRA = 10.0  # trapezoid plan: front this much wider than the back (sides ~6.4 deg)

# --- Plinth designs: high top up to the artisan's base line ----------------------------
# artisan (calipers, 2026-10-14): 19.0 wide in its lower 4-5 mm, resting 4.0 above the 4.0 mm top
# face, i.e. 8.0 above the plate top; pressed (4 mm travel) its base drops to 4.0 above the plate
ARTISAN_WELL = 20.2  # key hole: 19.0 + 0.6 per side; straight walls down to 2.2 above the plate
ARTISAN_TOP = 7.5  # top face above the plate top: 0.5 under the artisan's base, switch hidden
PLINTH_BEZEL = 9.5  # narrowest that keeps the R4 insert columns clear of the board pocket
PLINTH_EDGE = 2.5  # large top-perimeter chamfer (height): light catches it, the slab reads thinner
LONG_FRONT_BEZEL = 7.0  # board-behind plinth: top face in front of the key hole
LONG_PIN_GAP = 2.0  # board-behind plinth: switch pins -> board front stop, room for the wires

# --- Feet ------------------------------------------------------------------------------
FOOT_W = 6.0
FOOT_T = 1.4  # TPU strip thickness
FOOT_RECESS = 0.6  # recess depth: strips stand 0.8 mm proud
FOOT_INSET = 5.0  # strip centre-line distance from the bottom plate front/back edge


# --- Skin patterns (split top case sides) ------------------------------------------------
PATTERN_RAMP = 56.0  # lower band edge ramps out at this angle from the wall: >= 45 + TILT + margin, as printed
PATTERN_MARGIN = 1.2  # clear of the corner rounds, along each face
PATTERN_BOTTOM = 0.8  # band starts this far above the rebate top (full wall thickness behind it)
PATTERN_TOP = 1.0  # band stops this far below the top bevel
PATTERN_MAX_UP = 0.55  # relief faces turned toward the bed: normal up-component cap (~33 deg + 7 deg tilt < 45)
PATTERN_SEED = 7  # random layouts are reproducible
FUZZY_SKIN = 1.2  # fuzzy: modifier shell thickness inside the outer wall (slicer fuzzy skin applies there)
VORONOI_CELL = 3.6  # voronoi: mean cell spacing
VORONOI_GROOVE = 1.6  # groove width at the surface
VORONOI_DEPTH = 0.45  # groove depth
VORONOI_DRAFT = 58.0  # groove wall angle from the wall normal (>= 57: printable top down)
FACET_TILE = 6.0  # facets: target tile size (an inverted pyramid per tile)
FACET_DEPTH = (1.0, 1.8)  # apex depth range into the 3 mm wall (>= 1.2 mm of wall left)
# "-full" variants: the whole flat side, from the rim round at the seam up to the top bevel line
FULL_MARGIN = 0.3  # clear of the corner rounds, the rim round and the top bevel
MIN_WALL = 1.0  # wall left behind any relief; over the rebate (RIM_WALL thick) it caps the depth
USB_KEEPOUT = 1.5  # "-full" variants wrap the back too: plain margin round the USB-C plug notch


# --- Fasteners -------------------------------------------------------------------------
@dataclass(frozen=True)
class Fastener:
    """How the case closes: screw, anchor hole and the bosses around it."""

    label: str
    hole_d: float  # anchor hole: self-tapping pilot, or heat-set insert hole
    hole_depth: float  # split top-case column: hole depth above the column bottom
    body_hole: float  # one-piece body boss: hole length from 1 mm below the boss bottom
    tip: float  # split: screw tip above the top-case column bottom
    split_screw_l: float  # split: all four screws the same length (deeper counterbores at the back)
    clear_d: float  # clearance hole through the bottom plate / bottom case
    head_d: float  # counterbore diameter
    head_h: float  # counterbore depth (head height + margin)
    boss_r: float  # one-piece body bosses and split bottom-case columns
    top_boss_r: float  # split top-case columns
    boss_inset: float  # one-piece: boss axis from the inner wall (keeps the counterbore in the plate)


FASTENERS = {
    # M2 self-tapping screws straight into printed pilots (split M2x6, one-piece M2x8)
    "self-tap": Fastener("M2 self-tapping", 1.7, 3.6, 8.0, 3.2, 6.0, 2.4, 4.2, 1.8, 3.0, 2.5, 3.2),
    # M3 heat-set inserts (hole 4.0 x 5.7, Ruthex/CNC Kitchen style) + M3 button-head ISO 7380
    # screws (head 5.7 x 1.65): split M3x8 (5 mm in the insert), one-piece M3x6 (4.3 mm)
    "insert": Fastener("M3 heat-set insert", 4.0, 6.2, 7.2, 5.0, 8.0, 3.4, 6.0, 1.8, 4.0, 4.0, 4.2),
}


# --- Build options -----------------------------------------------------------------------
Pattern = Literal["fuzzy", "voronoi", "facets", "fuzzy-full", "voronoi-full", "facets-full"]
PATTERNS: tuple[str, ...] = ("fuzzy", "voronoi", "facets", "fuzzy-full", "voronoi-full", "facets-full")


@dataclass(frozen=True)
class Options:
    """Construction choices shared by every design."""

    plate: Literal["integrated", "separate"] = "integrated"  # switch plate part of the top shell, or screwed
    fastener: Literal["insert", "self-tap"] = "insert"
    bevel: float = 60.0  # chamfer angle from horizontal (the bed): 45 = classic; steeper prints cleaner
    pattern: Pattern | None = None  # split top case sides: fuzzy (slicer modifier), voronoi, facets

    @property
    def fast(self) -> Fastener:
        return FASTENERS[self.fastener]


LEGACY = Options(plate="separate", fastener="self-tap", bevel=45.0)  # the first prototypes


# --- Design looks ------------------------------------------------------------------------
@dataclass(frozen=True)
class Look:
    """Top-side proportions of a design; the defaults are the first four designs."""

    bezel: float = BEZEL  # top face beyond the key hole, left/right
    well: float = WELL  # key hole opening
    well_depth: float = WELL_DEPTH  # top face above the plate top
    top_edge: float = TOP_EDGE  # top-perimeter chamfer height
    board: Literal["under", "behind"] = "under"  # controller under the switch, or behind it (lower plate)
    front_bezel: float = 0.0  # board behind: top face in front of the key hole (the key moves forward)


PLINTH = Look(bezel=PLINTH_BEZEL, well=ARTISAN_WELL, well_depth=ARTISAN_TOP, top_edge=PLINTH_EDGE)
PLINTH_LONG = Look(
    bezel=PLINTH_BEZEL,
    well=ARTISAN_WELL,
    well_depth=ARTISAN_TOP,
    top_edge=PLINTH_EDGE,
    board="behind",
    front_bezel=LONG_FRONT_BEZEL,
)
