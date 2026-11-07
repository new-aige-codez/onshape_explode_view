#!/usr/bin/env python3
"""
SYNTHETIC TEST FIXTURE - NOT THE USER'S CAD.

Builds a crude stand-in of the pre-roll filler from the brief's nominal
dimensions, purely so scripts/build_views.py can be exercised end-to-end when
the real Onshape export is not available. Instance names imitate Onshape's
"<Part name> <n>" convention. Exported Y-up GLB in metres, like Onshape.

    python3 tests/make_test_fixture.py tests/fixture_synthetic.glb
"""
import math
import sys

import bpy  # noqa: E402  (bpy must be imported before bmesh)
import bmesh
from mathutils import Matrix, Vector

MM = 0.001


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def box(bm, sx, sy, sz, c, rotz=0.0):
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx * MM, sy * MM, sz * MM), verts=g["verts"])
    if rotz:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rotz, 3, "Z"), verts=g["verts"])
    bmesh.ops.translate(bm, vec=Vector(c) * MM, verts=g["verts"])


def cyl(bm, r1, h, c, r2=None, seg=24):
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1 * MM,
                              radius2=(r1 if r2 is None else r2) * MM, depth=h * MM)
    bmesh.ops.translate(bm, vec=Vector(c) * MM, verts=g["verts"])


def tube(bm, ro, ri, h, c, seg=24):
    """Annulus (washer / sleeve) as a closed manifold."""
    z0, z1 = (c[2] - h / 2) * MM, (c[2] + h / 2) * MM
    rings = []
    for r, z in ((ro, z0), (ro, z1), (ri, z1), (ri, z0)):
        rings.append([bm.verts.new(((c[0] + r * math.cos(2 * math.pi * k / seg)) * MM,
                                    (c[1] + r * math.sin(2 * math.pi * k / seg)) * MM, z)) for k in range(seg)])
    for a in range(4):
        A, B = rings[a], rings[(a + 1) % 4]
        for k in range(seg):
            bm.faces.new((A[k], A[(k + 1) % seg], B[(k + 1) % seg], B[k]))


def hexnut(bm, af, ri, h, c):
    tube(bm, af / math.sqrt(3), ri, h, c, seg=6)


def boolean_cut(target, cutter_bm):
    cut = mesh_obj("_cutter", cutter_bm)
    m = target.modifiers.new("cut", "BOOLEAN")
    m.operation, m.object = "DIFFERENCE", cut
    try:
        m.solver = "EXACT"
    except Exception:
        pass
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cut, do_unlink=True)


def main(out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    HT = 128.5
    corners = [(sx * 65, sy * 65) for sx in (-1, 1) for sy in (-1, 1)]
    pitch = 12.0
    grid = [(-54 + i * pitch, -54 + j * pitch) for i in range(10) for j in range(10)]

    # housing: 150x150 block, 100 cavities, 4 corner channels
    bm = bmesh.new(); box(bm, 150, 150, HT, (0, 0, HT / 2))
    housing = mesh_obj("Pre-Roll Housing 10x10 <1>", bm)
    bm = bmesh.new()
    for x, y in grid:
        cyl(bm, 4.6, HT + 10, (x, y, HT / 2), seg=16)
    for x, y in corners:
        cyl(bm, 4.25, HT + 10, (x, y, HT / 2), seg=20)
    boolean_cut(housing, bm)

    # tamper plate + 100 pins (one part)
    bm = bmesh.new(); box(bm, 118, 118, 6, (0, 0, 133))
    for x, y in grid:
        cyl(bm, 3.6, 100, (x, y, 80), seg=12)
    mesh_obj("Tamper Plate <1>", bm)

    # handle with 2 captive M4 nuts and 2 M4 countersunk screws from below the plate
    bm = bmesh.new(); box(bm, 100, 22, 24, (0, 0, 148))
    handle = mesh_obj("Handle <1>", bm)
    bm = bmesh.new()
    for x in (-35, 35):
        cyl(bm, 3.8, 6, (x, 0, 145), seg=6)
    boolean_cut(handle, bm)
    for i, x in enumerate((-35, 35), 1):
        bm = bmesh.new(); hexnut(bm, 7, 2.1, 3.2, (x, 0, 145)); mesh_obj(f"M4 Hex Nut <{i}>", bm)
        bm = bmesh.new(); cyl(bm, 2.0, 18, (x, 0, 139)); cyl(bm, 4.0, 2.2, (x, 0, 131.1), r2=2.0)
        mesh_obj(f"M4x18 FHCS <{i}>", bm)

    # housing bolts, washers, sleeves, lower locknuts
    for i, (x, y) in enumerate(corners, 1):
        bm = bmesh.new(); cyl(bm, 2.4, 141.5, (x, y, 129.5 - 141.5 / 2 + 0.01)); cyl(bm, 4.25, 5, (x, y, 132.0))
        mesh_obj(f"M5x140 SHCS <{i}>", bm)
        bm = bmesh.new(); tube(bm, 5.0, 2.7, 1.0, (x, y, 129.0)); mesh_obj(f"M5 Washer <{i}>", bm)
        bm = bmesh.new(); tube(bm, 4.0, 3.0, HT, (x, y, HT / 2)); mesh_obj(f"Al Sleeve 8x6 <{i}>", bm)
        bm = bmesh.new(); hexnut(bm, 8, 2.6, 5, (x, y, -7.25)); mesh_obj(f"M5 Nyloc Nut <{i}>", bm)

    # X bracket 4.75 thick, holes at bolt corners, motor holes, foot holes
    T = 4.75
    bm = bmesh.new()
    box(bm, 250, 22, T, (0, 0, -T / 2), rotz=math.radians(45))
    bracket = mesh_obj("X Bracket 5052 <1>", bm)
    for extra in ((250, 22, -45), (112, 66, 0)):   # proper boolean union, no overlapping faces
        ebm = bmesh.new(); box(ebm, extra[0], extra[1], T, (0, 0, -T / 2), rotz=math.radians(extra[2]))
        e = mesh_obj("_u", ebm)
        m = bracket.modifiers.new("u", "BOOLEAN"); m.operation, m.object = "UNION", e
        bpy.context.view_layer.objects.active = bracket
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(e, do_unlink=True)
    motor_holes = [(sx * 48, sy * 26) for sx in (-1, 1) for sy in (-1, 1)]
    feet = [(sx * 82, sy * 82) for sx in (-1, 1) for sy in (-1, 1)]
    bm = bmesh.new()
    for x, y in corners + motor_holes + feet:
        cyl(bm, 2.75, 20, (x, y, -T / 2), seg=20)
    boolean_cut(bracket, bm)
    # union the X arms properly
    bm = bmesh.new(); bm.from_mesh(bracket.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.to_mesh(bracket.data); bm.free()

    # motor: flange 110x66x4 + body 80x44x44 hanging below
    bm = bmesh.new(); box(bm, 110, 66, 4, (0, 0, -T - 2)); box(bm, 80, 44, 44, (0, 0, -T - 4 - 22))
    motor = mesh_obj("Vibration Motor 3650 <1>", bm)
    bm = bmesh.new()
    for x, y in motor_holes:
        cyl(bm, 2.75, 10, (x, y, -T - 2), seg=16)
    boolean_cut(motor, bm)
    for i, (x, y) in enumerate(motor_holes, 1):
        bm = bmesh.new(); cyl(bm, 2.4, 16, (x, y, -10.6)); cyl(bm, 2.4, 2.6, (x, y, -1.3), r2=4.6)  # countersunk, flush
        mesh_obj(f"M5x16 FHCS <{i}>", bm)
        bm = bmesh.new(); tube(bm, 5.0, 2.7, 1.0, (x, y, -T - 4 - 0.5)); mesh_obj(f"M5 Washer <{i + 4}>", bm)
        bm = bmesh.new(); hexnut(bm, 8, 2.6, 5, (x, y, -T - 5 - 2.5)); mesh_obj(f"M5 Nyloc Nut <{i + 4}>", bm)

    # rubber feet with stud + top nut
    for i, (x, y) in enumerate(feet, 1):
        bm = bmesh.new(); cyl(bm, 10, 58, (x, y, -T - 29)); cyl(bm, 2.4, 10, (x, y, -T + 5))
        mesh_obj(f"Rubber Isolation Foot <{i}>", bm)
        bm = bmesh.new(); hexnut(bm, 8, 2.6, 4, (x, y, 2.0)); mesh_obj(f"M5 Nyloc Nut <{i + 8}>", bm)

    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[-1] if len(sys.argv) > 1 else "tests/fixture_synthetic.glb")
