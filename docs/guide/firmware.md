# Firmware

The macropad runs upstream **QMK**, keyboard `handwired/onekey`: no custom keyboard definition,
only the keymap in `firmware/keymaps/enter/`.

| File | Content |
|---|---|
| `keymap.c` | the single key sends `KC_ENT` |
| `rules.mk` | `BOOTMAGIC_ENABLE = yes`: hold the key while plugging in -> bootloader (the closed case hides the board's buttons) |

The key is **assignable**: Enter is only the default. To send anything else, change the keycode in
`keymap.c` (any QMK keycode, a modifier combination such as `LCTL(KC_S)`, or a macro), rebuild
and re-flash -- bootmagic makes that possible with the case closed.

## Build

```bash
python3 -m venv ~/.venv-qmk && ~/.venv-qmk/bin/pip install qmk
~/.venv-qmk/bin/qmk setup                       # clones ~/qmk_firmware + toolchain
cp -r firmware/keymaps/enter ~/qmk_firmware/keyboards/handwired/onekey/keymaps/

# microSAM (Pro Micro footprint, RP2040)
qmk compile -kb handwired/onekey/promicro -km enter -e CONVERT_TO=rp2040_ce
# RP2040-Zero
qmk compile -kb handwired/onekey/rp2040 -km enter
```

The microSAM uses the Pro Micro target converted to RP2040 with `CONVERT_TO=rp2040_ce`; the
RP2040-Zero has its own target.

## Flash

1. Put the board in bootloader mode: BOOT button / double-tap RESET the first time; afterwards
   **hold the key while plugging in** (bootmagic).
2. An `RPI-RP2` drive appears; copy the `.uf2` onto it. The board reboots into the firmware.

From WSL, copy the `.uf2` to `/mnt/c/...` and drag it onto the drive in Explorer.
