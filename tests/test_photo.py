"""The photo pipeline without Blender: launch command guarantees, shots, backdrop composite."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from dais import photo


def test_blender_command_masks_gpu_and_caps_ram(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(photo.shutil, "which", lambda name: f"/usr/bin/{name}")
    cmd = photo.blender_command("/opt/blender/x/blender", Path("s.py"), Path("scene.json"), "2G")
    assert cmd[:3] == ["systemd-run", "--user", "--scope"]
    assert "MemoryMax=2G" in cmd and "MemorySwapMax=0" in cmd
    assert "unshare" in cmd and photo.GPU_MASK in cmd
    assert "/dev/dxg" in photo.GPU_MASK and "/usr/lib/wsl" in photo.GPU_MASK
    i = cmd.index("nice")
    assert cmd[i : i + 3] == ["nice", "-n", "19"]
    assert cmd[i + 3 : i + 6] == ["/opt/blender/x/blender", "-b", "--factory-startup"]  # background mode: no OpenGL


def test_blender_command_degrades_without_systemd_or_unshare(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(photo.shutil, "which", lambda name: None)
    cmd = photo.blender_command("blender", Path("s.py"), Path("scene.json"), "2G")
    assert cmd[0] == "nice"


def test_shots() -> None:
    assert [s.name for s in photo.shots(split=False)] == ["hero", "low", "back", "exploded"]
    split = photo.shots(split=True)
    assert split[-1].name == "seam" and split[-1].focus is not None
    assert set(photo.MATERIAL) >= set(next(s for s in split if s.name == "exploded").objects)


def test_composite_lays_render_over_backdrop(tmp_path: Path) -> None:
    fg = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    fg.putpixel((4, 4), (10, 10, 10, 255))
    fg.save(tmp_path / "raw.png")
    photo.composite(tmp_path / "raw.png", tmp_path / "out.webp")
    out = Image.open(tmp_path / "out.webp").convert("RGB")
    assert out.size == (8, 8)
    assert sum(out.getpixel((0, 0))) > 600  # light backdrop where the render is transparent
    assert sum(out.getpixel((4, 4))) < 200  # the dark object stays dark


def test_find_blender(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exe = tmp_path / "blender"
    exe.write_text("")
    assert photo.find_blender(str(exe)) == str(exe)
    monkeypatch.setenv("DAIS_BLENDER", str(exe))
    assert photo.find_blender() == str(exe)


def test_stitch_rebuilds_the_frame_from_overlapping_crops(tmp_path: Path) -> None:
    import json

    import numpy as np

    w, h, ov = 40, 30, 4
    frame = np.random.default_rng(0).integers(0, 256, (h, w, 4), dtype=np.uint8)
    tiles = []
    for j in range(2):
        for i in range(2):
            x0, x1 = max(0, i * w // 2 - ov), min(w, (i + 1) * w // 2 + ov)
            y0, y1 = max(0, j * h // 2 - ov), min(h, (j + 1) * h // 2 + ov)
            f = tmp_path / f"t{i}{j}.png"
            Image.fromarray(frame[y0:y1, x0:x1], "RGBA").save(f)
            tiles.append({"file": str(f), "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    spec = tmp_path / "s.tiles.json"
    spec.write_text(json.dumps({"width": w, "height": h, "tiles": tiles}))
    photo.stitch(spec, tmp_path / "out.png")
    assert np.array_equal(np.asarray(Image.open(tmp_path / "out.png")), frame)  # identical crops: exact

    Image.fromarray(frame[:5, :5], "RGBA").save(tiles[0]["file"])  # wrong size: refuse, never resize
    with pytest.raises(RuntimeError, match="rectangle"):
        photo.stitch(spec, tmp_path / "out.png")
