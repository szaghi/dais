# Assembly

## Bill of materials

| Part | Notes |
|---|---|
| Khor microSAM (RP2040, Pro Micro / Elite-C footprint, USB-C) | alternative: Waveshare RP2040-Zero (`--board rp2040zero`) |
| 1x MX switch, 3- or 5-pin | plate-mounted, no PCB |
| 2 short wires (~5 cm, 26-28 AWG silicone) | switch pins to board |
| 4x M3 heat-set inserts | hole 4.0 x 5.7 mm (Ruthex / CNC Kitchen style), melted into the screw columns |
| 4x M3x8 button-head screws (ISO 7380) | bottom case -> top case (split, split-trapezoid) |
| 4x M3x6 button-head screws (ISO 7380) | bottom plate -> body bosses (side-cove, wrap-cove) |
| ASA-CF, TPU | shells; feet |
| CA glue | feet into their recesses |

No plate screws: the switch plate is part of the top shell. With `--legacy` (separate plate,
self-tapping) the list is the first prototypes' instead: 4x M2x4 (plate), 4x M2x8 (one-piece)
or 4x M2x6 (split), no inserts. See [Options](/designs/options).

## Wiring

Switch pin 1 -> pad **A3**, switch pin 2 -> pad **A2** (Pro Micro naming; QMK `F4` / `F5`,
RP2040 `GP29` / `GP28` under the RP2040 Community Edition pinout). No diode: one key cannot
ghost.

RP2040-Zero: use pads **GP4** and **GP5** instead.

::: warning Verify before soldering
That the microSAM follows the RP2040 CE pinout is an inference, not a datasheet fact. Flash
first, then short A3-A2 with tweezers and confirm an Enter keypress **before** soldering.
:::

## Order of operations

```mermaid
flowchart LR
  I[Melt the 4 M3<br/>inserts in] --> A[Glue TPU feet]
  A --> B[Seat board<br/>front edge on the stop]
  B --> C[Clip switch into<br/>the top shell]
  C --> E[Solder 2 wires,<br/>flash, test]
  E --> F[Close the case]
  F --> G[Fit the keycap]
```

1. Melt the four M3 inserts into the screw columns from the open side (iron at about the
   filament's print temperature, ~250 deg C for ASA-CF), straight and flush; let them cool.
2. Glue the TPU feet into the recesses under the bottom plate / bottom case.
3. Seat the board in its pocket, front edge against the stop, USB-C toward the back.
4. Push the switch into the top shell from above, through the well, until both clips snap
   under the integrated plate.
5. Solder the two switch wires to the board, [flash](/guide/firmware), test.
6. Close:
   - **side-cove / wrap-cove**: bottom plate into the body opening, USB-C into the back-wall
     slot, 4x **M3x6** into the inserts;
   - **split / split-trapezoid**: lower the top case over the bottom case -- the lip locates in
     the rebate and the USB-C notch closes round the receptacle -- then 4x **M3x8** from below.
7. Fit the keycap.

To take a switch out, open the case and press its two clips from below: a switch puller cannot
reach them through the funnel.

Once closed, re-flash with **bootmagic**: hold the key while plugging the cable in.
