# Revised BOM: 10×10 Pre-Roll Filler

Checked against the Onshape model (glTF export) plus your choices: **4.75 mm bracket**, **128.8 mm sleeves**,
**nyloc jam nuts + blue threadlocker on the feet**, **M4 nylon-insert handle nuts**, 4-point motor mount.
The motor and its power supply are left out because you already have them.
Fasteners are stainless A2 by default. Order quantities include about 1 spare per small-fastener type.

## A. Fabricated parts
| # | Part | Qty | Specification | Notes |
|---|---|---:|---|---|
| A1 | Main housing | 1 | ASA print, **192 × 192 × 135.0 mm** (128.5 mm channel + 6.5 mm counterbore) | Needs a printer bed of at least 192 mm. Solid volume 2,812 cm³ |
| A2 | Tamping plate | 1 | Print, 157 × 157 × 40 mm: 10 mm plate + 100 integrated pins, about 28 mm long | **Fix in CAD before printing:** the 2 handle-screw holes are Ø3.0. Re-cut them as **M4 countersunk, Ø4.5 clearance**, from the pin side |
| A3 | Top handle | 1 | Print, 110 × 45 × 20 mm, 2 hex pockets for M4 captive nuts (about 7.3 mm across flats, 6 mm deep) | Fits the M4 nyloc nuts (B8) |
| A4 | X-bracket ("Motor Mount") | 1 | **5052-H32, 4.75 mm (3/16")**, laser-cut, 192 × 192 mm; 4 corner holes Ø5.5; **4 motor holes Ø5.5 with 90° countersink to Ø10** | **CAD change:** extrude 5.00 → 4.75. Order the countersinking service (e.g. SendCutSend), since laser cutting alone won't make the 90° seats. Quote needed |

## B. Purchased hardware
| # | Part | Qty needed | Order | Specification | Where it goes / notes |
|---|---|---:|---:|---|---|
| B1 | Long bolts | 4 | 5 (pack) | **M5 × 190 socket head cap screw**, under-head length 190 mm. **At least 60 mm of thread measured from the tip** | Through the housing corners. Half-thread is fine **only** if the thread is ≥ 60 mm. A standard ISO partial thread (about 28 mm) **won't work** |
| B2 | Compression sleeves | 4 | 2 × 300 mm tubes | Aluminium tube, **8 mm OD × 6 mm ID, cut to 128.8 mm** (±0.1), ends faced square and deburred | 2 per tube. They stand 0.3 mm proud of the ASA, so the aluminium carries the bolt clamp load |
| B3 | M5 flat washers | 12 | 13 | ISO 7089 / DIN 125, 5.3 ID × 10 OD × 1.0 mm | 4 under the bolt heads, 4 under the lower locknuts, 4 under the motor nuts |
| B4 | M5 nylon-insert locknuts | 12 | 13 | DIN 985 / ISO 10511, M5 × 0.8, 8 mm across flats | 4 below the bracket (bolts), 4 on the motor screws, **4 as jam nuts on the feet** |
| B5 | Motor screws | 4 | 5 | **M5 × 20 countersunk hex socket, 90°**, DIN 7991 / ISO 10642 (Ø10 head) | Flush in the bracket. Stack 4.75 + 6 + 1 + 5 → **3.25 mm** sticks out below the nut |
| B6 | Handle screws | 2 | 3 | **M4 × 25 countersunk hex socket**, DIN 7991 / ISO 10642 (Ø8 head) | From under the tamper plate, up into the handle nuts. 3 mm sticks out past the nut, 1.2 mm clear of the inside of the handle. **M4 × 16 doesn't reach the nut** |
| B7 | Rubber isolation feet | 4 | 1 × 4-pack | 20 mm Ø × 20 mm tall, **female M5** insert about 10 mm deep (Uxcell) | Screw about 8 mm onto the bolt tip so it never bottoms out. Lock with B4 + B9 |
| B8 | M4 nylon-insert locknuts | 2 | 3 | DIN 985 / ISO 10511, M4 × 0.7, 7 mm across flats × 5 mm | Captive in the handle pockets |
| B9 | Threadlocker, medium (blue) | 1 | 1 | Loctite 243 or equivalent (removable; works on stainless) | Foot inserts and jam nuts. Optionally the motor screws |

## C. Consumables
| # | Item | Qty | Notes |
|---|---|---:|---|
| C1 | ASA filament, 1.75 mm | **2 × 1 kg** | Estimate: housing ~1.2–1.4 kg + tamper ~0.25 kg + handle ~0.04 kg ≈ **1.5–1.8 kg** at 4 walls and 15–25% infill. One spool isn't enough |

## D. Budget (supplier prices carried over from ChatGPT's list, **not re-checked**)
| Item | Order | Price |
|---|---|---:|
| B7 Uxcell feet (Walmart) | 1 × 4-pack | $12.12 |
| B2 ServoCity 8×6 tube | 2 × 300 mm | $10.98 |
| B5 M5 × 20 DIN 7991 (BoltsandNuts, $0.26 ea) | 5 | $1.30 |
| B3 M5 washers (BoltsandNuts, $0.02 ea) | 13 | $0.26 |
| B4 M5 nylocs (BoltsandNuts, $0.06 ea) | 13 | $0.78 |
| C1 ELEGOO ASA ($16.99 ea) | 2 | $33.98 |
| **Known subtotal** | | **$59.42** |
| B1 M5 × 190 bolts, 5-pack | | price pending, **confirm thread length** |
| B6 M4 × 25 countersunk (ChatGPT priced M4 × 16 at $0.17 ea) | 3 | price to be confirmed |
| B8 M4 nylocs (ChatGPT priced plain M4 nuts) | 3 | price to be confirmed |
| B9 Blue threadlocker | 1 | price to be confirmed |
| A4 X-bracket incl. countersinking | 1 | quote needed |

Excludes shipping and tax. BoltsandNuts' minimum order or shipping can outweigh these small amounts, so consider ordering the B3/B4/B5/B6/B8 items from one supplier.

## What changed vs. ChatGPT's BOM
| Line | Was | Now | Why |
|---|---|---|---|
| Housing height | ~128.5 mm | 135.0 mm | Measured. 128.5 is the sleeve length |
| Sleeve length | ~122 mm | **128.8 mm** | Model + 0.3 mm proud (your choice) |
| Motor screws / washers / nuts | 2 each | **4 each** | The model has a 4-point mount |
| Handle screws | M4 × 16 | **M4 × 25** | M4 × 16 ends 1 mm short of the nut |
| Handle nuts | Plain M4 | **M4 nyloc** | Vibration (your choice). Fits the 6 mm pocket |
| Foot locking | Not specified | **+4 M5 nyloc jam nuts + blue threadlocker** | Your choice |
| Long bolts | "Fully threaded" | Half-thread OK **if ≥ 60 mm of thread** | Lower nut sits 55–60 mm from the tip |
| M5 washers / nylocs total | 10 / 6 | **12 / 12** | 4-point motor mount + jam nuts |
| ASA | 1 kg | **2 kg** | Measured part volumes |
| Motor + power supply | Included | Removed | Already procured |

## Geometry check of the final stack (M5 × 190, 4.75 mm bracket, 128.8 mm sleeves)
Under the bolt head: washer 1 + sleeve 128.8 + bracket 4.75 + washer 1 + nyloc 5 = **140.55 mm**, which leaves **49.45 mm** of
bolt below the lower nut. Feet: about 36 mm gap → 5 mm nyloc jam nut → 8 mm into the foot insert (2 mm short of bottoming out).
**Motor-to-table clearance about 19 mm.** Thread needed from the tip: 54.5 mm to the top of the lower nut, plus margin → **at least 60 mm**.

## Assembly order (tool access)
1. Mount the motor to the bracket **first**. From above, drive the M5 × 20 screws with a 3 mm hex key. From below, hold each
   washer + nyloc with an **8 mm open-end wrench** from the outside edge (there's no room for an 8 mm socket next to the motor body).
2. Insert the sleeves into the housing, put the housing on the bracket, then fit the bolts with their top washers.
3. Fit the lower washers and nylocs, then tighten until snug against the sleeves (they carry the clamp load).
4. Thread on the nyloc jam nuts, then the feet with blue threadlocker, about 8 mm deep. Back each jam nut down against its foot insert and tighten.
5. Fit the handle: nyloc nuts into the pockets, then the M4 × 25 screws up through the tamper plate's countersinks.

## To make the CAD match this BOM (optional, but keeps your model accurate)
Bracket 5.00 → 4.75 · sleeve 128.5 → 128.8 · bolts → M5 × 190 · feet → 20 × 20 female M5 · motor nuts → M5 + 4 washers ·
handle screws → M4 × 25 + re-cut tamper holes · add 4 lower washers and 4 jam nuts. Re-export the glTF and I'll re-run all checks (0 API calls).
