"""Blender-side renderer, run as ``blender -b --factory-startup -P blender_scene.py -- scene.json``.

Runs inside Blender's own Python: it imports only ``bpy``, never ``dais``/build123d. Everything
it needs -- meshes (STL, mm), materials, shots -- comes from the JSON written by ``dais photo``.
Cycles on the CPU only: GPU compute backends are switched off, and the caller also hides the
GPUs from the process (CUDA_VISIBLE_DEVICES="").
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MM = 0.001  # STL in mm, scene in metres
LAYER = 0.2 * MM  # printed layer height

MATERIALS = {
    # name: base colour (linear), roughness, layer-line tilt (deg about X) or None
    "asa-cf": ((0.032, 0.034, 0.037), 0.62, 7.0),  # top shells: printed top down, layers // top
    "asa-cf-flat": ((0.032, 0.034, 0.037), 0.62, 0.0),  # printed flat: layers // floor
    "asa-fuzzy": ((0.032, 0.034, 0.037), 0.75, None),  # slicer fuzzy skin: shown as a coarse noise bump
    "keycap": ((0.88, 0.88, 0.86), 0.42, None),  # white PBT
    "switch": ((0.012, 0.012, 0.013), 0.35, None),
    "tpu": ((0.010, 0.010, 0.010), 0.85, None),
    "pcb": ((0.012, 0.014, 0.013), 0.45, None),
    "metal": ((0.62, 0.62, 0.63), 0.28, None),
}


def material(name: str) -> bpy.types.Material:
    """Principled material; printed ones get faint layer lines and a carbon-fibre fleck."""
    color, rough, tilt = MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if name == "metal":
        bsdf.inputs["Metallic"].default_value = 1.0
    if name == "asa-fuzzy":  # ~0.3 mm grain, the look of fuzzy-skin perimeters (no geometry: slicer-made)
        coord = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 1500.0  # ~0.66 mm grain, like fuzzy-skin point spacing
        noise.inputs["Detail"].default_value = 2.0
        noise.inputs["Roughness"].default_value = 0.7
        nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 1.5 * MM  # dark ASA shows little shading: be generous
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        # walls only: the slicer fuzzes perimeters, the top face (printed on the bed) stays smooth
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Normal"], xyz.inputs["Vector"])
        mask = nt.nodes.new("ShaderNodeMapRange")  # |n.z| 0.4 -> 0.8 maps strength 1 -> 0
        absz = nt.nodes.new("ShaderNodeMath")
        absz.operation = "ABSOLUTE"
        nt.links.new(xyz.outputs["Z"], absz.inputs[0])
        nt.links.new(absz.outputs["Value"], mask.inputs["Value"])
        mask.inputs["From Min"].default_value, mask.inputs["From Max"].default_value = 0.4, 0.8
        mask.inputs["To Min"].default_value, mask.inputs["To Max"].default_value = 1.0, 0.0
        nt.links.new(mask.outputs["Result"], bump.inputs["Strength"])
        return mat
    if tilt is None:
        return mat
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (math.radians(-tilt), 0.0, 0.0)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    # Blender's bands run sin(20 * scale * z): one period every 2 pi / (20 scale) units
    wave.inputs["Scale"].default_value = 2 * math.pi / 20 / LAYER
    wave.inputs["Distortion"].default_value = 0.0
    wave.inputs["Detail"].default_value = 0.0
    nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")  # carbon-fibre sparkle in the roughness
    noise.inputs["Scale"].default_value = 4000.0
    noise.inputs["Detail"].default_value = 2.0
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.35
    ramp.inputs["From Max"].default_value = 0.75
    ramp.inputs["To Min"].default_value = rough + 0.08
    ramp.inputs["To Max"].default_value = rough - 0.18
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.02 * MM
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def import_mesh(path: str, name: str, mat: bpy.types.Material) -> bpy.types.Object:
    """STL (mm) -> smooth-by-angle object in metres."""
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path, global_scale=MM)
    (obj,) = set(bpy.data.objects) - before  # not selected_objects[0]: earlier objects may stay selected
    # the importer applies global_scale as an OBJECT scale (mesh data stays in mm): bake it into the
    # mesh, or every procedural texture in object coordinates runs 1000x too fine and vanishes
    obj.data.transform(Matrix.Diagonal((*obj.scale, 1.0)))
    obj.scale = (1.0, 1.0, 1.0)
    obj.name = name
    obj.data.shade_smooth()
    # curves are tessellated < 3 deg apart: still smooth at 8; facet ridges and groove edges stay crisp
    obj.data.set_sharp_from_angle(angle=math.radians(8))
    obj.data.materials.append(mat)
    return obj


def area_light(name: str, loc: tuple[float, float, float], size: float, energy: float) -> None:
    """Square area light at ``loc`` (m) aimed at the origin."""
    light = bpy.data.lights.new(name, "AREA")
    light.size = size
    light.energy = energy
    obj = bpy.data.objects.new(name, light)
    obj.location = loc
    obj.rotation_euler = (Vector((0, 0, 0.01)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(obj)


def setup(cfg: dict) -> bpy.types.Scene:
    """Empty scene, CPU-only Cycles, transparent film, studio lights, shadow-catcher floor."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = bpy.context.scene
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "NONE"  # no CUDA / OptiX / HIP / oneAPI devices at all
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = cfg["samples"]
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.denoising_use_gpu = False
    # OIDN on the full frame is the memory peak (~1.6 GiB at 1600x1200 with the defaults)
    scene.cycles.denoising_prefilter = cfg.get("denoise_prefilter", "ACCURATE")
    scene.cycles.denoising_quality = cfg.get("denoise_quality", "HIGH")
    scene.cycles.tile_size = 256  # small tiles keep the render buffers small
    scene.render.use_persistent_data = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = cfg["threads"]
    scene.render.resolution_x, scene.render.resolution_y = cfg["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.4  # white keycap reads white, dark shells stay dark grey
    scene.world = bpy.data.worlds.new("studio")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.9, 0.9, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 0.25

    area_light("key", (-0.18, -0.20, 0.26), 0.25, 1.3)
    area_light("fill", (0.24, -0.10, 0.12), 0.30, 0.25)
    area_light("rim", (0.05, 0.28, 0.18), 0.20, 0.6)

    bpy.ops.mesh.primitive_plane_add(size=2.0)
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.is_shadow_catcher = True

    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    return scene


def frame(
    cam: bpy.types.Object,
    objs: list[bpy.types.Object],
    eye: Vector,
    target: Vector,
    lens: float,
    margin: float,
    aspect: float,
    focus: list[float] | None = None,
) -> None:
    """Aim the camera along ``eye - target`` and back off until ``objs`` fit the frame."""
    if focus:  # close-up: a given sphere (mm)
        center, radius = Vector(focus[:3]) * MM, focus[3] * MM
    else:
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        center = sum(pts, Vector()) / len(pts)
        radius = max((p - center).length for p in pts)
    cam.data.lens = lens
    cam.data.clip_start = 1 * MM  # the 0.1 m default clips close-ups away
    cam.data.clip_end = 10.0
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    half_w = math.atan(18.0 / lens)
    half_h = math.atan(math.tan(half_w) / aspect)
    direction = (eye - target).normalized()
    cam.location = center + direction * (radius * margin / math.sin(min(half_w, half_h)))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()


def render_tiles(scene: bpy.types.Scene, out: Path, name: str, tiles: int, overlap: int) -> None:
    """Render ``name`` whole, or as ``tiles`` x ``tiles`` overlapping crops plus a JSON of their
    pixel rectangles (top-left origin) for ``dais.photo`` to stitch.

    The denoiser's memory scales with the pixels it sees at once (~0.7 KiB/px with OIDN): a 2 x 2
    grid cuts the peak from ~1.9 GiB to roughly a third at 1600 x 1200.
    """
    r = scene.render
    if tiles == 1:
        r.use_border = False
        r.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        return
    w, h = r.resolution_x, r.resolution_y
    r.use_border = True
    r.use_crop_to_border = True
    rects = []
    for j in range(tiles):
        for i in range(tiles):
            x0, x1 = max(0, i * w // tiles - overlap), min(w, (i + 1) * w // tiles + overlap)
            y0, y1 = max(0, j * h // tiles - overlap), min(h, (j + 1) * h // tiles + overlap)
            # Blender truncates border * size to whole pixels, and 848 / 1600 * 1600 can land at
            # 847.999...: aim half a pixel inside each cell so the crop is exactly the rectangle
            r.border_min_x, r.border_max_x = (x0 + 0.5) / w, min(1.0, (x1 + 0.5) / w)
            r.border_min_y, r.border_max_y = (h - y1 + 0.5) / h, min(1.0, (h - y0 + 0.5) / h)  # y runs up
            path = out / f"{name}__{i}_{j}.png"
            r.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rects.append({"file": str(path), "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    r.use_border = False
    (out / f"{name}.tiles.json").write_text(json.dumps({"width": w, "height": h, "tiles": rects}))


def main() -> None:
    """Import the meshes once, then render every shot."""
    cfg = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    scene = setup(cfg)
    mats = {name: material(name) for name in MATERIALS}
    objs = {m["name"]: import_mesh(m["file"], m["name"], mats[m["material"]]) for m in cfg["meshes"]}
    floor, cam = bpy.data.objects["floor"], scene.camera
    w, h = cfg["resolution"]
    for shot in cfg["shots"]:
        visible = [objs[n] for n in shot["objects"]]
        for name, obj in objs.items():
            obj.hide_render = name not in shot["objects"]
            obj.location = Vector(shot.get("offsets", {}).get(name, (0, 0, 0))) * MM
        bpy.context.view_layer.update()
        floor.location.z = min((o.matrix_world @ Vector(c)).z for o in visible for c in o.bound_box)
        frame(
            cam,
            visible,
            Vector(shot["eye"]) * MM,
            Vector(shot["target"]) * MM,
            shot.get("lens", 85.0),
            shot.get("margin", 1.05),
            w / h,
            shot.get("focus"),
        )
        render_tiles(scene, Path(cfg["output"]), shot["name"], cfg.get("tiles", 1), cfg.get("tile_overlap", 48))
        print(f"DAIS rendered {shot['name']}", flush=True)


if __name__ == "__main__":
    main()
