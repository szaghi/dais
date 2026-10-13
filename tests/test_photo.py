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
