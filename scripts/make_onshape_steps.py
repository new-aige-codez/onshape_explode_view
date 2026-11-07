#!/usr/bin/env python3
"""
Turn the solved explosion (out/manifest.json) into a click-by-click recipe for
building NATIVE exploded views in Onshape's Explode tool.

Onshape's public API has no endpoint to create exploded views (only
GET .../explodedviews), so the native feature must be entered in the UI;
this script makes that mechanical. No API calls.

    python3 scripts/make_onshape_steps.py            -> out/onshape_explode_steps.md
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
man = json.load(open(os.path.join(ROOT, "out", "manifest.json")))
cfg = json.load(open(os.path.join(ROOT, "config", "explode_config.json")))
groups = cfg["groups"]

# what each group looks like on screen, so it can be picked in the graphics area
HOW_TO_PICK = {
    "handle": "the blue U-shaped handle on top",
    "handle_nut": "the 2 small M4 nuts inside the handle legs (hide the handle temporarily, or pick them in the Instance list)",
    "handle_screw": "the 2 M4 countersunk screws entering the tamper plate from below, under the handle legs",
    "tamper": "the tamper plate with its 100 pins",
    "housing_bolt": "the 4 long (200 mm) M5 bolts at the housing corners",
    "upper_washer": "the 4 M5 washers under the bolt heads (in the corner counterbores)",
    "sleeve": "the 4 aluminium sleeves inside the corner channels (hide the housing temporarily to pick them)",
    "bracket": "the flat 'Motor Mount' X-bracket under the housing",
    "lower_locknut": "the 4 M5 locknuts under the bracket at the corners",
    "motor_screw": "the 4 countersunk motor screws, flush in the bracket centre",
    "motor": "the vibration motor",
    "motor_nut": "the 4 M4 nuts under the motor's mounting tabs",
    "foot": "the 4 black rubber feet on the bolt ends",
}

by_group = {}
for c in man["components"]:
    by_group.setdefault(c["explode_group"], []).append(c)


def steps_for(view):
    v = man["views"][view]
    off, hidden = v["offsets_mm"], set(v["hidden_groups"])
    rows = []
    for g, lst in by_group.items():
        if g in hidden or g == "housing" or not lst:
            continue
        dz = off.get(g, 0.0)
        if abs(dz) < 0.5:
            continue
        rows.append((g, dz, lst))
    # animate from the outside in: largest |dZ| first
    rows.sort(key=lambda r: -abs(r[1]))
    return rows, hidden


def names(lst):
    seen = {}
    for c in lst:
        seen[c["base_name"]] = seen.get(c["base_name"], 0) + 1
    return ", ".join(f"{n} x{q}" for n, q in seen.items())


out = []
w = out.append
w("# Native Onshape exploded views: step recipe\n")
w("Onshape's public API can **read** exploded views but cannot **create** them (the only endpoint is "
  "`GET /assemblies/.../explodedviews`), so the native feature has to be entered in the UI. This recipe makes that "
  "a mechanical job. All distances come from the collision-checked solution in `out/manifest.json`. Entering them "
  "doesn't move the assembled positions or change any mates.\n")
w("## One-time setup\n")
w("1. Open the assembly **Pre-Roll Filler Assembly**.\n"
  "2. Open the **Exploded views** panel (right-hand panel list) → **+ Exploded view**.\n"
  "3. **Direction for every step:** click any **edge of one of the 4 long corner bolts** (a cylindrical edge or face). "
  "Its axis is the machine's vertical axis. Every step moves along that axis only, so parts stay on their bolt axes "
  "and the pins stay over their cavities. Use the arrow-flip button so **+ points UP toward the handle** for "
  "positive distances and **DOWN toward the motor** for negative ones (or enter the absolute value and flip).\n"
  "4. Each step below moves a set of parts **from their assembled position** by the given distance. Put each part "
  "in **exactly one** step, because Onshape adds the distances when a part appears in several steps.\n")

for view, title in (("full_exploded_isometric", "01 - Full Machine Exploded"),
                    ("motor_mount_exploded", "02 - Motor and Fastener Exploded")):
    rows, hidden = steps_for(view)
    w(f"\n## View: `{title}`\n")
    if hidden:
        hid = ", ".join(groups[g]["label"] for g in sorted(hidden) if g in by_group)
        w(f"*Before this view:* create a **Display state** named `Motor detail` that hides: {hid}. "
          "Exploded views apply across display states, so switch to that display state when you show this view.\n")
    w("| Step | Select (count) | How to pick it | CAD name(s) | Direction | Distance |\n"
      "|---:|---|---|---|:-:|---:|")
    for i, (g, dz, lst) in enumerate(rows, 1):
        w(f"| {i} | {groups[g]['label']} ({len(lst)}) | {HOW_TO_PICK.get(g, '')} | {names(lst)} | "
          f"{'UP' if dz > 0 else 'DOWN'} | **{abs(dz):.0f} mm** |")
    w("\n*The ASA housing stays fixed (it's the reference).*")
    w("\nThen, optionally: **Explode lines** → pick the bolt-head centre and its foot / locknut centre on each corner "
      "(4 lines), plus one line per motor screw. That matches the dashed guides in the renders.\n")

w("\n## After you've built them\n"
  "* I can read the views back (`GET .../explodedviews` plus the assembly definition with `explodedViewId`, about "
  "3–4 read-only calls) and check every instance against these targets **once an API key works**.\n"
  "* Or send a screenshot of each view and I'll compare it with `out/full_exploded_isometric.png` / "
  "`out/motor_mount_exploded.png`.\n")
open(os.path.join(ROOT, "out", "onshape_explode_steps.md"), "w").write("\n".join(out))
print("wrote out/onshape_explode_steps.md")
