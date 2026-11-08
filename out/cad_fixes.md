# CAD fixes: Pre-Roll Filler Assembly

All values were measured from the Onshape glTF export (`cache/assembly.gltf`). "Up" means toward the handle,
along the bolt axis. X is Onshape's X axis.

| # | Priority | Problem | Fix |
|---|---|---|---|
| 1 | **Must fix** | Motor: M5 screws with **M4 nuts** | Change the 4 nuts to M5 and add 4 M5 washers |
| 2 | **Must fix** | Handle: the **M4×12 screws stop 4.7 mm short** of the captive nuts, **and the tamper holes are Ø3.0** (too small for M4) | Re-cut the tamper holes as M4 countersunk clearance holes, then change the screws to M4×25 |
| 3 | **Should fix** | 3 rubber feet sit **0.46 mm off** their bolt axis | Re-mate those feet concentric to the bolt |
| 4 | Recommended | The compression sleeves are **exactly flush** with the counterbore floor, so the ASA shares the bolt clamping load | Make the counterbores 0.3 mm deeper |
| 5 | Decide | The bracket is modelled at **5.00 mm**, but your brief says 4.75 mm | Match it to the sheet you'll actually buy |
| 6 | No CAD change | The housing is **135.0 mm** tall, not 128.5 mm (128.5 is the sleeve length) | Update the brief |

---

## 1. Motor screws are M5, nuts are M4 (must fix)

**Evidence.** The 4 motor screws are M5 countersunk: Ø10 head, M5 thread (major Ø5.0, minor Ø4.13), 20 mm long.
The bracket holes are cut for M5 (Ø5.5 clearance plus a Ø10 countersink), and the motor's mounting tabs have
Ø6.1 holes. Only the nuts are wrong: "Prevailing torque nut thin **M4**x0.70" has a Ø3.24 bore and can't go onto an M5 screw.

There are also no washers here, and the bearing surface is poor. An M5 nut (8 mm across flats) on a Ø6.1 hole
grips only a ring about 1 mm wide on the motor tab. That's weak under constant vibration.

**Steps in Onshape**
1. Open the **Pre-Roll Filler Assembly** tab.
2. In the Instance list, Ctrl-click the **4 "Prevailing torque nut thin M4x0.70" instances under the motor**.
   (The other 2 M4 nuts belong to the handle. Leave those alone.)
3. Right-click → **Edit standard content…** → Size **M5** (thread pitch 0.8), same nut type → **✓**. All 4 nuts update.
4. Add washers: **Insert → Standard content** → *ISO → Washers → Plain washer grade A (ISO 7089)* → **M5**. Insert 4.
5. Mate each washer: **Fastened mate**. Put the washer's top-face mate connector on the **bottom face of the
   motor tab, centred on the hole**.
6. Re-mate each nut: edit its existing Fastened mate (or delete it and make a new one) so the nut's top face sits
   on the **washer's bottom face**, concentric to the screw.
7. **Check:** the screw tip should stick out about **3 mm** below each nut (at least 2 threads, 1.6 mm, is needed
   for a prevailing-torque nut to lock). The pocket under the tab is about 9 mm deep and Ø14 or wider, so a
   washer plus nut (6 mm stack, Ø10) fits.

---

## 2. Handle screws don't reach the nuts, and the tamper holes are undersized (must fix)

**Evidence (along one handle-screw axis, from the bottom up)**
| Height (z) | What's there |
|---|---|
| 84.86 | Bottom face of the tamper plate, where the screw head sits |
| 84.86 → 88.49 | A shallow cone, Ø6.0 narrowing to Ø3.0. That's **smaller than the M4 head (Ø8)** |
| 88.49 → 94.86 | A **Ø3.0 hole**. That's **smaller than the M4 thread (Ø4 major, Ø3.2 minor)** |
| 94.86 | Top of the tamper plate / bottom of the handle |
| 94.86 → 101.86 | Ø4.5 clearance hole in the handle (correct) |
| 101.86 → 107.86 | Hex nut pocket (correct). The M4 nut sits at **101.86 → 106.86** |
| ~107.9 → 111.0 | Open space inside the handle |
| **97.20** | **Where the current M4×12 screw ends: 4.66 mm below the nut** |

So the screw never reaches the nut, and in the CAD it overlaps the plate because the hole is too small.
Moving the nuts down won't work, because the nut would have to sit inside the tamper plate. The fix is a
longer screw plus correct holes.

**Screw length.** The tip has to stick out at least 2 threads (1.4 mm) above the nut, to z ≥ 108.3, and must stay
below the handle's internal ceiling at about z 111.0. Measured from the head face at 84.86, that means a length of
23.4–26.1 mm. **→ Use M4×25** (tip at 109.9: 3.0 mm past the nut, 1.2 mm under the ceiling).
M4×20 is too short, because the tip would end inside the nut and its locking feature would never engage.

**Steps in Onshape: tamper plate holes**
1. Open the **Part Studio that contains "Tamper Plate"**.
2. Find the feature that makes the 2 handle-screw holes (the Ø3 hole or cut). Edit it, or delete it and add a new **Hole** feature:
   - **Hole type:** Countersink
   - **Standard:** ISO · **Type:** Countersunk head screw (ISO 10642) · **Size:** M4 · **Fit:** Normal (Ø4.5 clearance)
   - **Start from:** the **bottom face** of the plate (the side with the pins)
   - **Termination:** Through
   - **Countersink:** standard size (about Ø8.4–9.0 × 90°), so the Ø8 head sits flush with or slightly below the bottom face
3. Keep the same hole centres (they already line up with the handle's Ø4.5 holes).

**Steps in Onshape: handle screws**
4. Go back to the assembly and select the 2 handle screws.
   - **If they're standard content:** right-click → *Edit standard content…* → **Length 25** → ✓.
   - **If they're "Part 1" from their own Part Studio or a supplier STEP file (likely, given the name):**
     delete both instances → **Insert → Standard content → ISO 10642 hexagon socket countersunk head screw, M4 × 25**
     → insert 2 → add a **Fastened mate** from each screw's head mate connector to the **new countersink** in the tamper plate.
5. **Check:** each tip should end about 3 mm past the top of its nut and not touch the inside of the handle.

---

## 3. Three rubber feet are 0.46 mm off the bolt axis (should fix)

**Evidence.** Each foot has a threaded bore (Ø4.1, M5 minor diameter) that the 200 mm bolt's tip goes 6.0 mm into.
Offset of each bore centre from its bolt axis:

| Foot instance (glTF name) | Offset | Direction |
|---|---|---|
| Part 1.009 | 0.02 mm | OK |
| Part 1.012 | **0.46 mm** | +X |
| Part 1.014 | **0.46 mm** | +X |
| Part 1.015 | **0.46 mm** | +X |

All three are offset by the same amount in the same direction. That pattern means they were placed off a
reference other than the bolt axis (or copied from a misplaced one), not a geometry error.

**Steps in Onshape**
1. In the assembly, select the **good foot**. In the Mate features list, note what it's mated to.
2. For each of the other three feet: open its mate (the Mate features list highlights it when you select the foot).
3. Edit the mate (or replace it with a **Fastened** or **Revolute** mate) so that:
   - connector 1 = the foot's **bore centre on its top face**
   - connector 2 = the **bolt's tip circle**, or the bracket hole axis
   - **Offset X/Y = 0**. Keep only the vertical offset that puts the foot top at the same height as before
     (6.0 mm of bolt inside the foot).
4. **Check:** select the foot and the bolt and measure. The axis-to-axis distance should be 0.000 mm.

*Design note:* the feet hang on about 49.5 mm of exposed M5 bolt below the lower locknut. If the feet use
plain rubber threads, consider an M5 jam nut on top of each foot so vibration can't unscrew them.

---

## 4. Compression sleeves are flush, not proud (recommended)

**Evidence.** Sleeve: 128.5 mm, running from the bracket top (z -33.636) to z 94.864. The counterbore floor in the
housing is also at z 94.864 (6.5 mm below the top at 101.364). The M5 washer sits on both, so the bolt clamping load
is shared between the aluminium sleeve and the ASA housing. ASA creeps under constant load, especially with
vibration and warmth, so the clamp loosens over time. That's exactly what the sleeves are there to prevent.

**Steps in Onshape**
1. Open the **Part Studio with "Preroll Housing"**. Edit the corner counterbore feature: depth **6.5 → 6.8 mm**.
   (Or shorten the ASA channel length another way. Keep the sleeve at 128.5.)
2. In the assembly, check the 4 upper washers. If they're mated to the **counterbore floor**, re-mate them to the
   **sleeve's top face**, otherwise they'll drop 0.3 mm into the sleeve.
3. **Result:** the sleeve stands 0.3 mm proud and carries the bolt load, and the ASA is held in place without being
   crushed. (If you print the housing, 0.3 mm also absorbs print variation. Adjust to taste, 0.2–0.5 mm.)

---

## 5. Bracket thickness: 5.00 mm vs 4.75 mm (decide)

* **If you'll buy 3/16" (4.76 mm) 5052-H32:** open the Part Studio with **"Motor Mount"** → edit its extrude depth **5.00 → 4.75**.
  Then, in the assembly, check that the lower locknuts and the motor are mated to the bracket's **bottom face**, so
  they follow it up 0.25 mm. The motor screws' countersink (Ø10 → Ø5.5, about 2.25 mm deep) still fits in 4.75 mm.
* **If you'll buy 5 mm metric sheet:** leave the CAD alone and update the brief/BOM to 5.0 mm.

## 6. Housing height 135.0 mm vs 128.5 mm (no CAD change)
The housing is 135.0 mm overall: a 128.5 mm channel plus a 6.5 mm counterbore. 128.5 mm is the sleeve length.
Update the brief.

## Optional: washers under the lower M5 locknuts
The lower locknuts bear directly on the aluminium bracket (Ø5.5 hole, about a 1.25 mm bearing ring). That's
acceptable, but an M5 ISO 7089 washer under each one spreads the load and protects the bracket from fretting under
vibration. If you add one, re-mate each nut onto its washer. The bolt still sticks out a long way below the nut.

---

## Re-verify after fixing (0 API calls)
Re-export the assembly as glTF (same as before), replace `cache/assembly.gltf`, then run:
```
python3 scripts/build_views.py --glb cache/assembly.gltf --out out --no-render
```
`out/report.md` re-checks every nut on its screw (engagement and size match), all axis alignments, and lists any
remaining interferences. The fastener checks should then all show **yes**.
