# Assembly

## Bill of materials

| Part | Notes |
|---|---|
| Khor microSAM (RP2040, Pro Micro / Elite-C footprint, USB-C) | alternative: Waveshare RP2040-Zero (`--board rp2040zero`) |
| 1x MX switch, 3- or 5-pin | plate-mounted, no PCB |
| 2 short wires (~5 cm, 26-28 AWG silicone) | switch pins to board |
| 4x M2x4 self-tapping screws | plate -> top skin (all designs) |
| 4x M2x8 self-tapping screws | bottom plate -> body bosses (side-cove, wrap-cove) |
| 4x M2x6 self-tapping screws | bottom case -> top case (split, split-trapezoid) |
| ASA-CF, TPU | shells and plate; feet |
| CA glue | feet into their recesses |

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
  A[Glue TPU feet] --> B[Seat board<br/>front edge on the stop]
  B --> C[Clip switch into plate]
  C --> D[Screw plate under<br/>the top skin, 4x M2x4]
  D --> E[Solder 2 wires,<br/>flash, test]
  E --> F[Close the case]
  F --> G[Fit the keycap]
```

1. Glue the TPU feet into the recesses under the bottom plate / bottom case.
2. Seat the board in its pocket, front edge against the stop, USB-C toward the back.
3. Clip the switch into the plate.
4. Screw the plate under the top skin (4x M2x4), switch up through the well.
5. Solder the two switch wires to the board, [flash](/guide/firmware), test.
6. Close:
   - **side-cove / wrap-cove**: bottom plate into the body opening, USB-C into the back-wall
     slot, 4x **M2x8** into the bosses;
   - **split / split-trapezoid**: lower the top case over the bottom case -- the lip locates in
     the rebate and the USB-C notch closes round the receptacle -- then 4x **M2x6** from below.
7. Fit the keycap.

Once closed, re-flash with **bootmagic**: hold the key while plugging the cable in.
