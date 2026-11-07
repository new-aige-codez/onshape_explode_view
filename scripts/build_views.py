#!/usr/bin/env python3
"""
Offline exploded-view builder for the 10x10 pre-roll filling machine.

Runs on Blender's Python API either as the pip `bpy` module:
    python3 scripts/build_views.py --glb export/assembly.glb --out out/
or inside a Blender install:
    blender -b -P scripts/build_views.py -- --glb export/assembly.glb --out out/

Input : a GLB/glTF export of the Onshape assembly (UI export = 0 API calls),
        optionally the cached assembly-definition JSON and BOM JSON/CSV from
        scripts/onshape_fetch.py.
Output: renders, editable .blend (keyframed views + cameras), manifest JSON,
        BOM CSV/MD, verification report MD.

Nothing here talks to Onshape. The source CAD is never modified.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import time

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

FRAMES = {  # timeline frame that holds each view state in the .blend
    "assembled_isometric": 1,
    "full_exploded_isometric": 60,
    "motor_mount_exploded": 120,
    "corner_fastener_detail": 180,
}
TITLES = {
    "assembled_isometric": "10x10 Pre-Roll Filler - Assembled",
    "full_exploded_isometric": "10x10 Pre-Roll Filler - Full Exploded View",
    "motor_mount_exploded": "Housing Attachment & Motor Mount - Exploded Detail",
    "corner_fastener_detail": "Corner Connection Detail (cutaway, visualization only)",
}


# --------------------------------------------------------------------------- args
def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--glb", required=True, help="GLB/glTF export of the assembly")
    p.add_argument("--config", default=os.path.join(ROOT, "config", "explode_config.json"))
    p.add_argument("--out", default=os.path.join(ROOT, "out"))
    p.add_argument("--assembly-json", help="cached Onshape assembly definition (optional)")
    p.add_argument("--bom-json", help="cached Onshape BOM JSON (optional)")
    p.add_argument("--views", help="comma list of views to render (default: all in config)")
    p.add_argument("--samples", type=int, help="override render samples")
    p.add_argument("--long-edge", type=int, help="override long edge px")
    p.add_argument("--no-render", action="store_true", help="checks + manifest + .blend only")
    p.add_argument("--dump-names", action="store_true", help="list parts + classification and exit")
    p.add_argument("--watermark", help="text stamped on every render (e.g. for test fixtures)")
    return p.parse_args(argv)


# --------------------------------------------------------------------------- helpers
class Ctx:
    pass


def log(*a):
    print("[explode]", *a, flush=True)


def strip_instance_suffix(name):
    n = re.sub(r"\.\d{3}$", "", name)          # Blender duplicate suffix
    n = re.sub(r"\s*<\d+>$", "", n)             # Onshape instance suffix
    return n.strip()


def mat_to_list(m, scale_mm):
    out = []
    for r in range(4):
        row = []
        for c in range(4):
            v = m[r][c] * (scale_mm if (c == 3 and r < 3) else 1.0)
            row.append(round(v, 6))
        out.append(row)
    return out


class Part:
    """One movable instance (repeated instances stay separate)."""

    def __init__(self, ob, node_path, mm):
        self.ob = ob
        self.name = ob.name
        self.node_path = node_path
        self.mesh_name = ob.data.name
        self.base_name = strip_instance_suffix(ob.name)
        self.group = None
        self.kind = None
        self.rule = None
        self.assembled = ob.matrix_world.copy()
        me = ob.data
        me.calc_loop_triangles()
        n = len(me.vertices)
        co = np.empty(n * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(self.assembled)
        w = co @ M[:3, :3].T + M[:3, 3]
        self.verts0 = w * mm  # world, assembled, millimetres
        tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", tris)
        self.tris = tris.reshape(-1, 3).tolist()
        self.bmin = self.verts0.min(axis=0)
        self.bmax = self.verts0.max(axis=0)
        self.center = (self.bmin + self.bmax) / 2
        self.size = self.bmax - self.bmin
        self._bvh_cache = {}

    def bvh(self, dz):
        key = round(dz, 4)
        if key not in self._bvh_cache:
            v = self.verts0 + np.array([0.0, 0.0, dz])
            self._bvh_cache = {key: BVHTree.FromPolygons(v.tolist(), self.tris, epsilon=0.0)}
        return self._bvh_cache[key]

    def bbox(self, dz):
        return self.bmin + [0, 0, dz], self.bmax + [0, 0, dz]

    @property
    def xy(self):
        return self.center[:2]


# --------------------------------------------------------------------------- import
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


UP_ROTATIONS = {  # rotation that brings the model's "up" (toward the handle) onto +Z
    "+Z": Matrix.Identity(4),
    "-Z": Matrix.Rotation(math.pi, 4, "X"),
    "+Y": Matrix.Rotation(math.pi / 2, 4, "X"),
    "-Y": Matrix.Rotation(-math.pi / 2, 4, "X"),
    "+X": Matrix.Rotation(-math.pi / 2, 4, "Y"),
    "-X": Matrix.Rotation(math.pi / 2, 4, "Y"),
}


def import_assembly(path, mm, up_axis="+Z"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and len(o.data.vertices) > 0]
    paths = {}
    for o in meshes:
        chain, p = [], o.parent
        while p is not None:
            chain.append(p.name)
            p = p.parent
        paths[o.name] = "/".join(reversed(chain))
    # flatten hierarchy: every part becomes an independent world-space object
    # (plus one rigid whole-assembly rotation so the machine's up axis is +Z;
    #  relative placements are untouched)
    R = UP_ROTATIONS[up_axis]
    for o in meshes:
        mw = R @ o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    for o in new:
        if o not in meshes:
            bpy.data.objects.remove(o, do_unlink=True)
    parts = [Part(o, paths[o.name], mm) for o in meshes]
    log(f"imported {len(parts)} mesh instances from {os.path.basename(path)}")
    return parts


# --------------------------------------------------------------------------- classify
def classify(parts, cfg):
    cl = cfg["classification"]
    tol = cl["axis_match_tolerance_mm"]
    rules = [(re.compile(rx, re.I), tgt) for rx, tgt in cl["keyword_rules"]]
    overrides = [(re.compile(rx, re.I), g) for rx, g in cl.get("overrides", {}).items()]

    for p in parts:
        for rx, g in overrides:
            if rx.search(p.name):
                p.group, p.rule = g, f"override:{rx.pattern}"
                break
        if p.group:
            continue
        # size signatures (sorted bbox dims, mm) for generically named CAD parts like "Part 1"
        dims = sorted(p.size.tolist())
        for sig in cl.get("geometry_rules", []):
            if all(abs(a - b) <= sig.get("tol_mm", 0.6) for a, b in zip(dims, sorted(sig["dims_mm"]))):
                tgt = sig["target"]
                p.rule = f"geometry:{sig['dims_mm']}"
                if tgt.startswith("kind:"):
                    p.kind = tgt[5:]
                else:
                    p.group = tgt
                break
        if p.group or p.kind:
            continue
        for rx, tgt in rules:
            if rx.search(p.name):
                p.rule = rx.pattern
                if tgt.startswith("kind:"):
                    p.kind = tgt[5:]
                else:
                    p.group = tgt
                break

    housings = [p for p in parts if p.group == "housing"]
    if not housings:
        # geometric fallback: the largest unclassified body is the housing
        cand = [p for p in parts if p.group is None and p.kind is None] or parts
        h = max(cand, key=lambda q: float(np.prod(q.size)))
        h.group, h.rule = "housing", "fallback:largest-volume"
        housings = [h]
    H = max(housings, key=lambda q: float(np.prod(q.size)))
    for p in housings:
        if p is not H:
            p.group, p.rule = "unassigned", "duplicate-housing-match"
    hz_mid = H.center[2]
    htop = H.bmax[2]

    # long screws through the housing = housing bolts
    for p in parts:
        if p.kind == "screw" and p.size[2] >= cl["long_bolt_min_length_mm"]:
            p.group = "housing_bolt"
    bolt_axes = [p.xy for p in parts if p.group == "housing_bolt"]
    foot_axes = [p.xy for p in parts if p.group == "foot"]
    handles = [p for p in parts if p.group == "handle"]

    def under_handle(p):
        return any(np.all(p.xy >= h.bmin[:2] - 5) and np.all(p.xy <= h.bmax[:2] + 5) for h in handles)

    def near(xy, axes):
        return any(np.linalg.norm(xy - a) <= tol for a in axes)

    for p in parts:
        if p.group or not p.kind:
            continue
        on_bolt, on_foot = near(p.xy, bolt_axes), near(p.xy, foot_axes)
        above = p.center[2] > htop - 1.0 or (p.center[2] > hz_mid and under_handle(p))
        if p.kind == "washer":
            p.group = ("upper_washer" if p.center[2] > hz_mid else "lower_washer") if on_bolt else \
                      "foot_hardware" if on_foot else "upper_washer" if above else "motor_washer"
        elif p.kind == "nut":
            p.group = ("lower_locknut" if p.center[2] < hz_mid else "upper_washer") if on_bolt else \
                      "foot_hardware" if on_foot else "handle_nut" if above else "motor_nut"
        elif p.kind == "screw":
            p.group = "foot_hardware" if on_foot else "handle_screw" if above else "motor_screw"
        p.rule = (p.rule or "") + " +position"
    for p in parts:
        if p.group is None:
            p.group, p.rule = "unassigned", "no rule matched"
        if p.group not in cfg["groups"]:
            log(f"WARNING group '{p.group}' for {p.name} missing in config -> unassigned")
            p.group = "unassigned"
    return H


# --------------------------------------------------------------------------- explosion solver
def footprints_overlap(a, b, pad=0.5):
    return not (a.bmax[0] + pad < b.bmin[0] or b.bmax[0] + pad < a.bmin[0] or
                a.bmax[1] + pad < b.bmin[1] or b.bmax[1] + pad < a.bmin[1])


def solve_offsets(parts, offsets, cfg, hidden, hz_mid):
    """Push groups outward (away from the fixed housing) until no two visible
    parts of different groups intersect and assembled stacking order is kept
    with a minimum gap."""
    s = cfg["solver"]
    gap, step = s["min_gap_mm"], s["push_step_mm"]
    off = dict(offsets)
    vis = [p for p in parts if p.group not in hidden]
    pairs = []
    for i, a in enumerate(vis):
        for b in vis[i + 1:]:
            if a.group != b.group and footprints_overlap(a, b):
                # stacked = assembled z-intervals disjoint -> keep order + gap
                if a.bmin[2] >= b.bmax[2] - 0.05:
                    pairs.append((a, b, "stack", b, a))      # (.., lower, upper)
                elif b.bmin[2] >= a.bmax[2] - 0.05:
                    pairs.append((a, b, "stack", a, b))
                else:
                    pairs.append((a, b, "mesh", None, None))
    moves = []
    # explicit clearance rules, e.g. handle screws must sit fully below the tamper pin tips
    for g_move, g_ref, side in s.get("must_clear", []):
        mv = [p for p in vis if p.group == g_move]
        rf = [p for p in vis if p.group == g_ref]
        if not mv or not rf:
            continue
        if side == "below":
            limit = min(p.bmin[2] for p in rf) + off.get(g_ref, 0) - gap
            need = limit - max(p.bmax[2] for p in mv)
            if off.get(g_move, 0) > need:
                off[g_move] = math.floor(need)
                moves.append({"iter": -1, "group": g_move, "new_z_mm": off[g_move], "reason": f"must_clear below {g_ref}"})
        else:
            limit = max(p.bmax[2] for p in rf) + off.get(g_ref, 0) + gap
            need = limit - min(p.bmin[2] for p in mv)
            if off.get(g_move, 0) < need:
                off[g_move] = math.ceil(need)
                moves.append({"iter": -1, "group": g_move, "new_z_mm": off[g_move], "reason": f"must_clear above {g_ref}"})
    for it in range(s["max_iterations"]):
        bad = None
        for a, b, mode, lo, up in pairs:
            da, db = off.get(a.group, 0.0), off.get(b.group, 0.0)
            if mode == "stack":
                dl, du = off.get(lo.group, 0.0), off.get(up.group, 0.0)
                if abs(du - dl) > 1e-6 and (up.bmin[2] + du) - (lo.bmax[2] + dl) < gap:
                    bad = (a, b, "gap")
                    break
            else:
                if abs(da - db) < 1e-6:
                    continue  # moved together -> same relation as assembled CAD
                amin, amax = a.bbox(da)
                bmin, bmax = b.bbox(db)
                if amax[2] < bmin[2] or bmax[2] < amin[2]:
                    continue
                if a.bvh(da).overlap(b.bvh(db)):
                    bad = (a, b, "intersect")
                    break
        if not bad:
            return off, moves, []
        a, b, why = bad
        # move the group further from the housing (larger |offset|); ties -> by side
        ga, gb = a.group, b.group
        if ga == "housing":
            mover = gb
        elif gb == "housing":
            mover = ga
        else:
            mover = ga if abs(off.get(ga, 0)) >= abs(off.get(gb, 0)) else gb
        o = off.get(mover, 0.0)
        sign = 1.0 if o > 0 or (o == 0 and [p for p in vis if p.group == mover][0].center[2] > hz_mid) else -1.0
        off[mover] = off.get(mover, 0.0) + sign * step
        moves.append({"iter": it, "group": mover, "new_z_mm": off[mover], "reason": why,
                      "between": [a.name, b.name]})
    # report what is still wrong
    remaining = []
    for a, b, mode, lo, up in pairs:
        da, db = off.get(a.group, 0.0), off.get(b.group, 0.0)
        if mode == "mesh" and abs(da - db) > 1e-6 and a.bvh(da).overlap(b.bvh(db)):
            remaining.append([a.name, b.name])
    return off, moves, remaining


# --------------------------------------------------------------------------- checks
def ray_hits(part, xy, z_from, z_to):
    """Cast a vertical ray at xy through a part (assembled). Return list of hit z."""
    bvh = part.bvh(0.0)
    hits, z = [], z_from
    d = Vector((0, 0, -1)) if z_to < z_from else Vector((0, 0, 1))
    for _ in range(64):
        loc, nrm, idx, dist = bvh.ray_cast(Vector((xy[0], xy[1], z)), d, abs(z_to - z))
        if loc is None:
            break
        hits.append(loc.z)
        z = loc.z + d.z * 0.01
    return hits


def run_checks(parts, H, cfg, off_full):
    R = {"inventory": {}, "checks": []}
    by = {}
    for p in parts:
        by.setdefault(p.group, []).append(p)
    exp = {k: v for k, v in cfg["expected_inventory"].items() if not k.startswith("_")}
    for g, n in exp.items():
        have = len(by.get(g, []))
        R["inventory"][g] = {"expected": n, "found": have, "ok": have == n}
    for g, lst in by.items():
        if g not in exp:
            R["inventory"][g] = {"expected": None, "found": len(lst), "ok": g != "unassigned"}

    def add(name, ok, detail):
        R["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    add("total instances imported", len(parts) > 0, f"{len(parts)} mesh instances")
    un = [p.name for p in by.get("unassigned", [])]
    add("every instance classified", not un, "unclassified: " + (", ".join(un) if un else "none"))

    # housing dims
    ex = cfg.get("expected_dims", {})
    hh = ex.get("housing_height_mm", 128.5)
    add(f"housing height vs brief ({hh} mm)", abs(H.size[2] - hh) < 1.0,
        f"CAD {H.size[2]:.2f} mm (bbox {H.size[0]:.1f} x {H.size[1]:.1f} x {H.size[2]:.1f})")

    # bracket thickness
    for b in by.get("bracket", []):
        bt = ex.get("bracket_thickness_mm", 4.75)
        add(f"bracket thickness vs brief ({bt} mm)", abs(b.size[2] - bt) < 0.1, f"{b.name}: CAD {b.size[2]:.2f} mm")

    # motor envelope
    for m in by.get("motor", []):
        dims = sorted(m.size.tolist(), reverse=True)
        ok = all(abs(a - b) < 6 for a, b in zip(dims, [110, 66, 48]))
        add("motor envelope ~110x66x48", ok, f"{m.name}: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
        for b in by.get("bracket", []):
            dxy = np.linalg.norm(m.xy - b.xy)
            add("motor centred on bracket", dxy < 2.0, f"XY offset motor->bracket centre {dxy:.2f} mm")
            dims_xy = m.size[:2]
            add("motor orientation", True, f"motor long axis along {'X' if dims_xy[0] >= dims_xy[1] else 'Y'}; "
                f"below bracket: {m.bmax[2] <= b.bmax[2] + 0.5}")

    # housing bolt axes
    tol = cfg["classification"]["axis_match_tolerance_mm"]
    for bolt in by.get("housing_bolt", []):
        row = []
        for g in ("sleeve", "upper_washer", "lower_locknut"):
            cand = by.get(g, [])
            if not cand:
                row.append(f"{g}: none")
                continue
            q = min(cand, key=lambda c: np.linalg.norm(c.xy - bolt.xy))
            row.append(f"{g} {q.name} dXY={np.linalg.norm(q.xy - bolt.xy):.2f}")
        ok_axis = all("none" in r or float(r.split("dXY=")[1]) < 0.5 for r in row)
        add(f"coaxial stack @ {bolt.name}", ok_axis, "; ".join(row))
        # holes: a vertical ray at the bolt axis should pass through bracket and housing channel
        for g in ("bracket",):
            for b in by.get(g, []):
                hits = ray_hits(b, bolt.xy, b.bmax[2] + 5, b.bmin[2] - 5)
                add(f"bracket hole on axis of {bolt.name}", not hits,
                    "clear" if not hits else f"ray hit bracket material at z={hits[0]:.2f} (hole missing/offset)")
        hits = ray_hits(H, bolt.xy, H.bmax[2] + 5, H.bmin[2] - 5)
        add(f"housing channel on axis of {bolt.name}", not hits,
            "clear through-channel" if not hits else f"ray hit housing at z={hits[0]:.2f}")

    # motor screws through bracket holes
    for s in by.get("motor_screw", []):
        for b in by.get("bracket", []):
            hits = ray_hits(b, s.xy, b.bmax[2] + 5, b.bmin[2] - 5)
            add(f"bracket hole for {s.name}", not hits, "clear" if not hits else f"hit at z={hits[0]:.2f}")

    # tamper alignment + pins over cavities
    for t in by.get("tamper", []):
        dxy = np.linalg.norm(t.xy - H.xy)
        add("tamper centred over housing", dxy < 1.0, f"XY offset {dxy:.2f} mm; explosion is pure +Z so offset is preserved")
        tips = t.verts0[t.verts0[:, 2] < t.bmax[2] - 15.0]
        if len(tips):
            # greedy clustering of pin geometry (unique 0.5 mm XY cells) into pins
            cells = np.unique(np.round(tips[:, :2] * 2) / 2, axis=0)
            centres, members = [], []
            for c in cells:
                for k, q in enumerate(centres):
                    if np.linalg.norm(c - q) < 5.0:
                        members[k].append(c)
                        centres[k] = np.mean(members[k], axis=0)
                        break
                else:
                    centres.append(c)
                    members.append([c])
            in_cav = 0
            for c in centres:
                hits = ray_hits(H, c, H.bmax[2] + 5, H.bmin[2] - 5)
                if not hits or hits[0] < H.bmax[2] - 5:
                    in_cav += 1
            add("tamper pins over cavities", in_cav == len(centres),
                f"{len(centres)} pin clusters detected, {in_cav} sit over open cavities")

    # assembled interferences (CAD info)
    inter = []
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            if footprints_overlap(a, b, 0) and not (a.bmax[2] < b.bmin[2] or b.bmax[2] < a.bmin[2]):
                if a.bvh(0.0).overlap(b.bvh(0.0)):
                    inter.append(f"{a.name} x {b.name}")
    R["checks"].append({"check": "assembled-state contacts/interferences (INFO: touching faces and nominal "
                        "threads count; review for real clashes)", "ok": None,
                        "detail": f"{len(inter)} pairs: " + ", ".join(inter[:40]) + (" ..." if len(inter) > 40 else "")
                        if inter else "none"})
    return R


# --------------------------------------------------------------------------- materials / scene
def make_material(name, spec):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        nt.nodes.clear()
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs[0], out.inputs[0])
    c = spec["color"]
    bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0)
    bsdf.inputs["Roughness"].default_value = spec.get("roughness", 0.5)
    if "anisotropic" in spec:
        for key in ("Anisotropic", "Anisotropy"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = spec["anisotropic"]
    m.diffuse_color = (c[0], c[1], c[2], 1)
    return m


def assign_materials(parts, cfg):
    mats = {k: make_material(k, v) for k, v in cfg["materials"].items()}
    for p in parts:
        mname = cfg["groups"][p.group]["material"]
        ob = p.ob
        if not ob.material_slots:
            ob.data.materials.append(None)
        for slot in ob.material_slots:
            slot.link = "OBJECT"
            slot.material = mats[mname]
        p.material = mname
    return mats


def organise_collections(parts, cfg):
    root = bpy.context.scene.collection
    cols = {}
    for p in parts:
        g = p.group
        if g not in cols:
            cols[g] = bpy.data.collections.new(f"{list(cfg['groups']).index(g):02d} {cfg['groups'][g]['label']}")
            root.children.link(cols[g])
        for c in list(p.ob.users_collection):
            c.objects.unlink(p.ob)
        cols[g].objects.link(p.ob)
        p.ob["explode_group"] = g
        p.ob["assembled_matrix_world"] = [v for row in p.assembled for v in row]


def setup_world_and_render(cfg, args):
    sc = bpy.context.scene
    r = cfg["render"]
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = args.samples or r["samples"]
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    for vt in ("Khronos PBR Neutral", "Standard"):
        try:
            sc.view_settings.view_transform = vt
            break
        except Exception:
            continue
    w = bpy.data.worlds.new("Studio")
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    if w.node_tree:
        bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg is None:
            bg = w.node_tree.nodes.new("ShaderNodeBackground")
            out = w.node_tree.nodes.new("ShaderNodeOutputWorld")
            w.node_tree.links.new(bg.outputs[0], out.inputs[0])
        bg.inputs[0].default_value = (0.9, 0.92, 0.95, 1)
        bg.inputs[1].default_value = 0.5
    else:
        w.color = (0.9, 0.92, 0.95)


def add_lights(center, radius, mm):
    """Soft three-point studio rig, sized to the model."""
    s = radius / mm
    rig = bpy.data.collections.new("Studio Lights")
    bpy.context.scene.collection.children.link(rig)
    specs = [("Key", (1.2, -0.6, 1.5), 2.2, 100), ("Fill", (-1.3, 0.9, 0.8), 3.0, 40),
             ("Rim", (-0.4, 1.6, 1.1), 1.4, 60), ("Top", (0, 0, 2.2), 2.5, 30)]
    c = Vector(center) / mm
    for name, d, size, energy in specs:
        L = bpy.data.lights.new(name, "AREA")
        L.size = size * s
        L.energy = energy * (s ** 2)
        ob = bpy.data.objects.new(name, L)
        ob.location = c + Vector(d).normalized() * 3.0 * s
        ob.rotation_euler = (c - ob.location).to_track_quat("-Z", "Y").to_euler()
        rig.objects.link(ob)


def look_rotation(direction):
    return (-Vector(direction)).to_track_quat("-Z", "Y").to_euler()


# --------------------------------------------------------------------------- guides / cutaway
def dashed_line(name, xy, z0, z1, mm, mat, radius=0.35, dash=5.0, gapl=3.5):
    bm = bmesh.new()
    z = z0
    while z < z1:
        ze = min(z + dash, z1)
        geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=radius / mm, radius2=radius / mm,
                                     depth=(ze - z) / mm)
        bmesh.ops.translate(bm, verts=geom["verts"], vec=Vector((xy[0] / mm, xy[1] / mm, (z + ze) / 2 / mm)))
        z = ze + gapl
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    return bpy.data.objects.new(name, me)


def build_guides(view, parts, off, groups, tol, mm, mat, hidden):
    obs = []
    vis = [p for p in parts if p.group not in hidden]
    for p in vis:
        if p.group not in groups:
            continue
        on_axis = [q for q in vis if np.linalg.norm(q.xy - p.xy) <= tol]
        if len(on_axis) < 2:
            continue
        lo = min(q.bmin[2] + off.get(q.group, 0) for q in on_axis)
        hi = max(q.bmax[2] + off.get(q.group, 0) for q in on_axis)
        obs.append(dashed_line(f"GUIDE {view} {p.name}", p.xy, lo - 4, hi + 4, mm, mat))
    return obs


def build_cutaway(H, axis_xy, cam_dir, mm, region=45.0, inset=15.0):
    """Non-destructive quarter cut of a *copy* of the housing at one corner."""
    me = H.ob.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(me)
    bm.free()
    cut = bpy.data.objects.new("Housing CUTAWAY (viz only)", me)
    cut.matrix_world = H.ob.matrix_world.copy()
    for i, slot in enumerate(H.ob.material_slots):
        if i < len(cut.material_slots):
            cut.material_slots[i].link = "OBJECT"
            cut.material_slots[i].material = slot.material
    sx = 1 if cam_dir[0] >= 0 else -1
    sy = 1 if cam_dir[1] >= 0 else -1
    # cutter: box whose inner corner sits exactly on the bolt axis, extending toward the camera
    zc = (H.bmin[2] + H.bmax[2]) / 2
    hz = H.size[2] / 2 + 10
    # inner corner sits `inset` mm behind the bolt axis so the whole channel + sleeve are exposed
    cx = axis_xy[0] + sx * (region / 2 - inset)
    cy = axis_xy[1] + sy * (region / 2 - inset)
    bpy.ops.mesh.primitive_cube_add(size=1)
    cutter = bpy.context.active_object
    cutter.name = "CUTTER (viz only)"
    cutter.scale = (region / mm, region / mm, 2 * hz / mm)
    cutter.location = (cx / mm, cy / mm, zc / mm)
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    mod = cut.modifiers.new("Corner cutaway", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    for solver in ("EXACT", "MANIFOLD", "FLOAT", "FAST"):
        try:
            mod.solver = solver
            break
        except Exception:
            continue
    return cut, cutter


# --------------------------------------------------------------------------- camera + visibility
def frame_camera(name, points_mm, az, el, cfg, args, mm):
    d = Vector((math.cos(math.radians(el)) * math.cos(math.radians(az)),
                math.cos(math.radians(el)) * math.sin(math.radians(az)),
                math.sin(math.radians(el))))
    rot = look_rotation(d)
    R = rot.to_matrix()
    right, up = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0))
    P = np.array(points_mm)
    u = P @ np.array(right)
    v = P @ np.array(up)
    w_ = u.max() - u.min()
    h_ = v.max() - v.min()
    m = cfg["render"]["margin_frac"]
    long_edge = args.long_edge or cfg["render"]["long_edge_px"]
    aspect = max(Ctx.min_aspect, min(1.8, w_ / h_))
    if aspect >= 1:
        rx, ry = long_edge, int(round(long_edge / aspect))
    else:
        rx, ry = int(round(long_edge * aspect)), long_edge
    scale = max(w_, h_ * aspect) if aspect >= 1 else max(h_, w_ / aspect)
    scale *= (1 + 2 * m)
    cu, cv = (u.max() + u.min()) / 2, (v.max() + v.min()) / 2
    ctr = right * cu + up * cv
    dist = float(np.abs(P).max()) * 4 + 1000
    cam_d = bpy.data.cameras.new(name)
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = scale / mm
    cam_d.clip_end = (dist * 3) / mm
    cam = bpy.data.objects.new(name, cam_d)
    cam.location = (ctr + d * dist) / mm
    cam.rotation_euler = rot
    bpy.context.scene.collection.objects.link(cam)
    return cam, (rx, ry), d, scale, (right, up, ctr)


def visibility_report(parts, off, hidden, d, scale, res, basis):
    right, up, _ = basis
    vis = [p for p in parts if p.group not in hidden]
    trees = [(q, q.bvh(off.get(q.group, 0))) for q in vis]
    px_per_mm = max(res) / scale
    out = []
    dvec = Vector(d)
    rng = np.random.default_rng(0)
    for p in vis:
        dz = off.get(p.group, 0)
        V = p.verts0 + [0, 0, dz]
        T = np.array(p.tris)
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        nrm = np.cross(b - a, c - a)
        ln = np.linalg.norm(nrm, axis=1)
        facing = (ln > 1e-9) & ((nrm @ np.array(d)) > 1e-6 * ln)
        cand = np.nonzero(facing)[0]
        if len(cand) == 0:
            cand = np.arange(len(T))
        pick = rng.choice(cand, size=min(60, len(cand)), replace=False, p=(ln[cand] / ln[cand].sum()))
        own = p.bvh(dz)
        seen = front = 0
        for i in pick:
            ctr = (a[i] + b[i] + c[i]) / 3 + nrm[i] / max(ln[i], 1e-12) * 0.02
            org = Vector(ctr) + dvec * 5000
            target_dist = 5000 - 0.01
            if own.ray_cast(org, -dvec, target_dist)[0] is not None:
                continue  # hidden by another face of the same part (concave)
            front += 1
            blocked = any(t.ray_cast(org, -dvec, target_dist)[0] is not None for q, t in trees if q is not p)
            seen += 0 if blocked else 1
        frac = seen / max(front, 1)
        u = V @ np.array(right)
        w = V @ np.array(up)  # noqa
        size_px = max(u.max() - u.min(), w.max() - w.min()) * px_per_mm
        out.append({"part": p.name, "group": p.group, "visible_fraction": round(frac, 2),
                    "projected_size_px": round(float(size_px), 1),
                    "ok": frac >= 0.15 and size_px >= 10})
    return out


# --------------------------------------------------------------------------- keyframes
def key_state(parts, off, hidden, frame, extra_hidden=()):
    for p in parts:
        ob = p.ob
        ob.matrix_world = Matrix.Translation((0, 0, off.get(p.group, 0.0) / Ctx.mm)) @ p.assembled
        h = p.group in hidden or ob in extra_hidden
        ob.hide_render = h
        ob.hide_viewport = h
        ob.keyframe_insert("location", frame=frame)
        ob.keyframe_insert("hide_render", frame=frame)
        ob.keyframe_insert("hide_viewport", frame=frame)


def key_aux(ob, frame, visible):
    ob.hide_render = not visible
    ob.hide_viewport = not visible
    ob.keyframe_insert("hide_render", frame=frame)
    ob.keyframe_insert("hide_viewport", frame=frame)


# --------------------------------------------------------------------------- post
def finish_png(path, bg, title, watermark=None):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGBA")
    base = Image.new("RGBA", im.size, tuple(int(c * 255) for c in bg) + (255,))
    base.alpha_composite(im)
    W, Hh = base.size
    dr = ImageDraw.Draw(base)
    try:
        U = min(W, Hh)
        f = ImageFont.load_default(size=max(16, U // 48))
        fs = ImageFont.load_default(size=max(11, U // 85))
    except TypeError:
        f = fs = ImageFont.load_default()
    pad = W // 60
    sub = "External visualization of the Onshape assembly export. Original CAD unmodified."

    def fit(text, font):
        while font.size > 9 and dr.textlength(text, font=font) > W - 2 * pad:
            font = ImageFont.load_default(size=font.size - 1)
        return font
    try:
        f, fs = fit(title, f), fit(sub, fs)
    except Exception:
        pass
    dr.text((pad, Hh - pad - f.size * 1.4 - fs.size * 1.3), title, fill=(40, 46, 56, 255), font=f)
    dr.text((pad, Hh - pad - fs.size * 1.2), sub, fill=(110, 116, 126, 255), font=fs)
    if watermark:
        try:
            wf = ImageFont.load_default(size=max(20, min(W, Hh) // 30))
        except TypeError:
            wf = f
        try:
            wf = fit(watermark, wf)
        except Exception:
            pass
        dr.text((pad, pad), watermark, fill=(220, 30, 90, 255), font=wf)
    base.convert("RGB").save(path, optimize=True)


# --------------------------------------------------------------------------- outputs
def write_outputs(out, parts, H, cfg, views_state, checks, args, moves):
    mm = Ctx.mm
    manifest = {
        "generator": "scripts/build_views.py",
        "source_geometry": os.path.abspath(args.glb),
        "coordinate_system": "assembly frame from export; +Z up toward handle; housing fixed reference; mm",
        "onshape_document_modified": False,
        "native_onshape_exploded_view_created": False,
        "views": {k: {"frame": FRAMES[k], "offsets_mm": v["offsets"], "hidden_groups": sorted(v["hidden"]),
                      "camera": v.get("camera")} for k, v in views_state.items()},
        "solver_moves": moves,
        "components": [],
    }
    asm = {}
    if args.assembly_json and os.path.exists(args.assembly_json):
        data = json.load(open(args.assembly_json))
        for inst in data.get("rootAssembly", {}).get("instances", []):
            asm[inst.get("name")] = inst
    for p in parts:
        info = asm.get(p.name) or asm.get(p.base_name) or {}
        manifest["components"].append({
            "instance_name": p.name,
            "base_name": p.base_name,
            "part_id": info.get("partId"),
            "part_number": info.get("partNumber"),
            "onshape_instance_id": info.get("id"),
            "parent_path": p.node_path,
            "geometry_ref": f"{os.path.basename(args.glb)}#mesh:{p.mesh_name}",
            "assembled_matrix_world_mm": mat_to_list(p.assembled, mm),
            "bbox_mm": {"min": p.bmin.round(3).tolist(), "max": p.bmax.round(3).tolist()},
            "material": cfg["groups"][p.group]["material"],
            "explode_group": p.group,
            "classification_rule": p.rule,
            "per_view": {k: {"dz_mm": v["offsets"].get(p.group, 0.0), "visible": p.group not in v["hidden"]}
                         for k, v in views_state.items()},
        })
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=2)

    # BOM
    rows = {}
    for p in parts:
        k = (p.group, p.base_name)
        rows.setdefault(k, 0)
        rows[k] += 1
    order = list(cfg["groups"])
    items = sorted(rows.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1]))
    with open(os.path.join(out, "bom.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "qty", "part_name", "explode_group", "group_label", "material_render"])
        for i, ((g, n), q) in enumerate(items, 1):
            w.writerow([i, q, n, g, cfg["groups"][g]["label"], cfg["groups"][g]["material"]])
    with open(os.path.join(out, "bom.md"), "w") as fh:
        fh.write("# Bill of Materials (from exported assembly instances)\n\n")
        fh.write("| # | Qty | Part (CAD name) | Group |\n|---:|---:|---|---|\n")
        for i, ((g, n), q) in enumerate(items, 1):
            fh.write(f"| {i} | {q} | {n} | {cfg['groups'][g]['label']} |\n")
        fh.write(f"\n**Total instances:** {len(parts)}\n")
        if args.bom_json and os.path.exists(args.bom_json):
            fh.write("\nAn Onshape BOM was cached at `" + os.path.basename(args.bom_json) +
                     "`; part numbers/descriptions there are authoritative.\n")

    # report
    with open(os.path.join(out, "report.md"), "w") as fh:
        fh.write("# Exploded-view build report\n\n")
        fh.write("**These are external visualizations.** No native Onshape exploded view was created, "
                 "and the Onshape document, parts and mates were not modified.\n\n")
        if args.watermark:
            fh.write(f"> **{args.watermark}**\n\n")
        fh.write("## Inventory vs. expected\n\n| Group | Expected | Found | OK |\n|---|---:|---:|:-:|\n")
        for g, v in checks["inventory"].items():
            fh.write(f"| {cfg['groups'].get(g, {}).get('label', g)} | {v['expected'] if v['expected'] is not None else '-'}"
                     f" | {v['found']} | {'yes' if v['ok'] else '**NO**'} |\n")
        fh.write("\n## Geometry checks\n\n| Check | OK | Detail |\n|---|:-:|---|\n")
        for c in checks["checks"]:
            ok = "info" if c["ok"] is None else ("yes" if c["ok"] else "**NO**")
            fh.write(f"| {c['check']} | {ok} | {c['detail']} |\n")
        fh.write("\n## Explosion offsets (mm, after collision solver)\n\n")
        for k, v in views_state.items():
            fh.write(f"### {k}\n\n| Group | dZ |\n|---|---:|\n")
            for g in order:
                if g in v["offsets"] and g not in v["hidden"] and any(p.group == g for p in parts):
                    fh.write(f"| {cfg['groups'][g]['label']} | {v['offsets'][g]:+.0f} |\n")
            if v.get("remaining_intersections"):
                fh.write(f"\n**Unresolved intersections:** {v['remaining_intersections']}\n")
            if v.get("visibility"):
                bad = [x for x in v["visibility"] if not x["ok"]]
                fh.write(f"\nVisibility: {len(v['visibility']) - len(bad)}/{len(v['visibility'])} parts clearly visible")
                if bad:
                    fh.write(" - poorly visible: " + ", ".join(f"{x['part']} ({x['visible_fraction']:.0%}, "
                                                               f"{x['projected_size_px']:.0f}px)" for x in bad))
                fh.write("\n")
            fh.write("\n")
        if moves:
            fh.write(f"Collision solver made {len(moves)} adjustments (see manifest.json `solver_moves`).\n")


# --------------------------------------------------------------------------- main
def main():
    args = parse_args()
    cfg = json.load(open(args.config))
    os.makedirs(args.out, exist_ok=True)
    mm = cfg["units_to_mm"]
    Ctx.mm = mm
    reset_scene()
    parts = import_assembly(args.glb, mm, cfg.get("up_axis", "+Z"))
    H = classify(parts, cfg)

    if args.dump_names:
        for p in sorted(parts, key=lambda q: -q.center[2]):
            print(f"{p.name:45s} grp={p.group:15s} kind={str(p.kind):7s} "
                  f"ctr=({p.center[0]:7.1f},{p.center[1]:7.1f},{p.center[2]:7.1f}) "
                  f"size=({p.size[0]:6.1f},{p.size[1]:6.1f},{p.size[2]:6.1f}) mesh={p.mesh_name} rule={p.rule}")
        return

    t0 = time.time()
    assign_materials(parts, cfg)
    organise_collections(parts, cfg)
    setup_world_and_render(cfg, args)
    base_off = {g: float(v["z"]) for g, v in cfg["groups"].items()}
    tol = cfg["classification"]["axis_match_tolerance_mm"]
    guide_mat = make_material("guide", cfg["materials"]["guide"])

    views = cfg["views"]
    wanted = args.views.split(",") if args.views else list(views)
    state, all_moves = {}, []
    aux = []  # (object, frame-where-visible)
    bolts = [p for p in parts if p.group == "housing_bolt"]

    for vname, v in views.items():
        hidden = set(v.get("hide_groups", []))
        if v.get("exploded"):
            offs = dict(base_off)
            offs.update({k: float(z) for k, z in v.get("detail_offsets", {}).items()})
            offs, moves, remaining = solve_offsets(parts, offs, cfg, hidden, H.center[2])
            for mv in moves:
                mv["view"] = vname
            all_moves += moves
        else:
            offs, remaining = {g: 0.0 for g in base_off}, []
        az, el = v["azimuth_deg"], v["elevation_deg"]
        dcam = np.array([math.cos(math.radians(el)) * math.cos(math.radians(az)),
                         math.cos(math.radians(el)) * math.sin(math.radians(az)), math.sin(math.radians(el))])
        extra_hidden, view_aux, focus = set(), [], None
        if v.get("corner_cutaway") and bolts:
            corner = max(bolts, key=lambda b: float(np.dot(b.xy - H.xy, dcam[:2])))
            focus = corner.xy
            for p in parts:
                if p.group in ("housing_bolt", "upper_washer", "sleeve", "lower_locknut", "lower_washer") and \
                        np.linalg.norm(p.xy - corner.xy) > tol:
                    extra_hidden.add(p.ob)
            cut, cutter = build_cutaway(H, corner.xy, dcam, mm)
            bpy.context.scene.collection.objects.link(cut)
            extra_hidden.add(H.ob)
            view_aux.append(cut)
        if v.get("guides"):
            gobs = build_guides(vname, [p for p in parts if p.ob not in extra_hidden], offs,
                                set(v.get("guide_groups", [])), tol, mm, guide_mat, hidden)
            col = bpy.data.collections.get("Guides") or bpy.data.collections.new("Guides")
            if col.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(col)
            for g in gobs:
                col.objects.link(g)
            view_aux += gobs
        # framing points
        pts = []
        for p in parts:
            if p.group in hidden or p.ob in extra_hidden:
                continue
            lo, hi = p.bbox(offs.get(p.group, 0))
            if focus is not None and p.group in ("housing", "bracket"):
                lo = np.maximum(lo, [focus[0] - 45, focus[1] - 45, -1e9])
                hi = np.minimum(hi, [focus[0] + 45, focus[1] + 45, 1e9])
            pts += [[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        Ctx.min_aspect = v.get("min_aspect", 0.55)
        cam, res, dvec, scale, basis = frame_camera(f"CAM {vname}", pts, az, el, cfg, args, mm)
        visibility = None
        if focus is None:
            visibility = visibility_report(parts, offs, hidden, dvec, scale, res, basis)
        state[vname] = {"offsets": offs, "hidden": hidden, "extra_hidden": extra_hidden, "aux": view_aux,
                        "camera": {"name": cam.name, "azimuth_deg": az, "elevation_deg": el,
                                   "ortho_scale_mm": round(scale, 2), "resolution": list(res)},
                        "cam": cam, "res": res, "remaining_intersections": remaining, "visibility": visibility}
        aux += [(o, vname) for o in view_aux]
        log(f"view {vname}: solved ({len([m for m in all_moves if m['view'] == vname]) if v.get('exploded') else 0} "
            f"moves), res {res}, remaining intersections {len(remaining)}")

    # lights sized to the whole exploded scene
    fs = state.get("full_exploded_isometric") or next(iter(state.values()))
    allpts = np.vstack([np.vstack(p.bbox(fs["offsets"].get(p.group, 0))) for p in parts])
    add_lights(allpts.mean(axis=0), float(np.linalg.norm(allpts.max(0) - allpts.min(0))) / 2, mm)

    # keyframes: one frame per view, cameras bound with markers
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = "CONSTANT"
    except Exception:
        pass
    sc = bpy.context.scene
    for vname, st in state.items():
        f = FRAMES[vname]
        key_state(parts, st["offsets"], st["hidden"], f, extra_hidden=st["extra_hidden"])
        for o, owner in aux:
            key_aux(o, f, owner == vname)
        m = sc.timeline_markers.new(vname, frame=f)
        m.camera = st["cam"]
    sc.frame_start, sc.frame_end = 1, max(FRAMES.values())

    checks = run_checks(parts, H, cfg, state.get("full_exploded_isometric", {}).get("offsets", base_off))
    for vname, st in state.items():
        if st["visibility"] and views[vname].get("exploded"):
            groups = {}
            for x in st["visibility"]:
                groups.setdefault(x["group"], []).append(x)
            missing = [g for g, xs in groups.items() if not any(x["ok"] for x in xs)]
            hidden_inst = [x["part"] for x in st["visibility"] if not x["ok"]]
            checks["checks"].append({"check": f"every group clearly visible in {vname}", "ok": not missing,
                                     "detail": (f"groups with no visible instance: {missing}; " if missing else
                                                "all groups visible; ") +
                                               f"occluded instances (normal for back side): {hidden_inst or 'none'}"})
    wrong_mat = [p.name for p in parts if any(s.material is None or s.material.name != cfg["groups"][p.group]["material"]
                                               for s in p.ob.material_slots)]
    checks["checks"].append({"check": "materials assigned per group", "ok": not wrong_mat,
                             "detail": "all correct" if not wrong_mat else ", ".join(wrong_mat)})

    blend = os.path.join(args.out, "preroll_exploded_views.blend")
    sc.frame_set(FRAMES["full_exploded_isometric"])
    sc.camera = state["full_exploded_isometric"]["cam"] if "full_exploded_isometric" in state else sc.camera

    if not args.no_render:
        for vname in wanted:
            st = state[vname]
            sc.frame_set(FRAMES[vname])
            sc.camera = st["cam"]
            sc.render.resolution_x, sc.render.resolution_y = st["res"]
            sc.render.resolution_percentage = 100
            path = os.path.join(args.out, f"{vname}.png")
            sc.render.filepath = path
            t = time.time()
            bpy.ops.render.render(write_still=True)
            finish_png(path, cfg["render"]["background_rgb"], TITLES[vname], args.watermark)
            log(f"rendered {vname} {st['res']} in {time.time() - t:.0f}s")

    sc.frame_set(FRAMES["full_exploded_isometric"])
    sc.camera = state["full_exploded_isometric"]["cam"]
    sc.render.resolution_x, sc.render.resolution_y = state["full_exploded_isometric"]["res"]
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend), compress=True)
    json.dump(checks, open(os.path.join(args.out, "verification.json"), "w"), indent=2)
    write_outputs(args.out, parts, H, cfg, state, checks, args, all_moves)
    bad = [c for c in checks["checks"] if c["ok"] is False]
    n = len([c for c in checks["checks"] if c["ok"] is not None])
    log(f"done in {time.time() - t0:.0f}s; {n - len(bad)}/{n} checks ok")
    for c in bad:
        log(f"  CHECK FAILED: {c['check']}: {c['detail']}")


if __name__ == "__main__":
    main()
