# Native Onshape exploded views: step recipe

Onshape's public API can **read** exploded views but cannot **create** them (the only endpoint is `GET /assemblies/.../explodedviews`), so the native feature has to be entered in the UI. This recipe makes that a mechanical job. All distances come from the collision-checked solution in `out/manifest.json`. Entering them doesn't move the assembled positions or change any mates.

## One-time setup

1. Open the assembly **Pre-Roll Filler Assembly**.
2. Open the **Exploded views** panel (right-hand panel list) → **+ Exploded view**.
3. **Direction for every step:** click any **edge of one of the 4 long corner bolts** (a cylindrical edge or face). Its axis is the machine's vertical axis. Every step moves along that axis only, so parts stay on their bolt axes and the pins stay over their cavities. Use the arrow-flip button so **+ points UP toward the handle** for positive distances and **DOWN toward the motor** for negative ones (or enter the absolute value and flip).
4. Each step below moves a set of parts **from their assembled position** by the given distance. Put each part in **exactly one** step, because Onshape adds the distances when a part appears in several steps.


## View: `01 - Full Machine Exploded`

| Step | Select (count) | How to pick it | CAD name(s) | Direction | Distance |
|---:|---|---|---|:-:|---:|
| 1 | Handle (1) | the blue U-shaped handle on top | Tamper Handle x1 | UP | **330 mm** |
| 2 | Captive M4 handle nuts (2) | the 2 small M4 nuts inside the handle legs (hide the handle temporarily, or pick them in the Instance list) | Prevailing torque nut thin M4x0.70 x2 | UP | **285 mm** |
| 3 | Tamper plate + pins (1) | the tamper plate with its 100 pins | Tamper Plate x1 | UP | **240 mm** |
| 4 | M4 countersunk handle screws (2) | the 2 M4 countersunk screws entering the tamper plate from below, under the handle legs | Part 1 x2 | UP | **191 mm** |
| 5 | M5 housing bolts (4) | the 4 long (200 mm) M5 bolts at the housing corners | Part 1 x4 | UP | **175 mm** |
| 6 | Motor locknuts (4) | the 4 M4 nuts under the motor's mounting tabs | Prevailing torque nut thin M4x0.70 x4 | DOWN | **154 mm** |
| 7 | Upper bearing washers (4) | the 4 M5 washers under the bolt heads (in the corner counterbores) | Plain washer grade A HV200 M5 x4 | UP | **145 mm** |
| 8 | 3650 vibration motor (1) | the vibration motor | Part 1 x1 | DOWN | **105 mm** |
| 9 | Rubber isolation feet (4) | the 4 black rubber feet on the bolt ends | Part 1 x4 | DOWN | **95 mm** |
| 10 | Al compression sleeves (4) | the 4 aluminium sleeves inside the corner channels (hide the housing temporarily to pick them) | Part 1 x4 | UP | **80 mm** |
| 11 | Lower M5 locknuts (4) | the 4 M5 locknuts under the bracket at the corners | Prevailing torque nut thin M5x0.80 x4 | DOWN | **70 mm** |
| 12 | 5052 Al X-bracket (1) | the flat 'Motor Mount' X-bracket under the housing | Motor Mount x1 | DOWN | **40 mm** |
| 13 | Motor mounting screws (4) | the 4 countersunk motor screws, flush in the bracket centre | Part 1 x4 | DOWN | **20 mm** |

*The ASA housing stays fixed (it's the reference).*

Then, optionally: **Explode lines** → pick the bolt-head centre and its foot / locknut centre on each corner (4 lines), plus one line per motor screw. That matches the dashed guides in the renders.


## View: `02 - Motor and Fastener Exploded`

*Before this view:* create a **Display state** named `Motor detail` that hides: Handle, Captive M4 handle nuts, M4 countersunk handle screws, Tamper plate + pins. Exploded views apply across display states, so switch to that display state when you show this view.

| Step | Select (count) | How to pick it | CAD name(s) | Direction | Distance |
|---:|---|---|---|:-:|---:|
| 1 | Motor locknuts (4) | the 4 M4 nuts under the motor's mounting tabs | Prevailing torque nut thin M4x0.70 x4 | DOWN | **210 mm** |
| 2 | M5 housing bolts (4) | the 4 long (200 mm) M5 bolts at the housing corners | Part 1 x4 | UP | **190 mm** |
| 3 | Upper bearing washers (4) | the 4 M5 washers under the bolt heads (in the corner counterbores) | Plain washer grade A HV200 M5 x4 | UP | **160 mm** |
| 4 | 3650 vibration motor (1) | the vibration motor | Part 1 x1 | DOWN | **150 mm** |
| 5 | Rubber isolation feet (4) | the 4 black rubber feet on the bolt ends | Part 1 x4 | DOWN | **140 mm** |
| 6 | Al compression sleeves (4) | the 4 aluminium sleeves inside the corner channels (hide the housing temporarily to pick them) | Part 1 x4 | UP | **110 mm** |
| 7 | Lower M5 locknuts (4) | the 4 M5 locknuts under the bracket at the corners | Prevailing torque nut thin M5x0.80 x4 | DOWN | **100 mm** |
| 8 | 5052 Al X-bracket (1) | the flat 'Motor Mount' X-bracket under the housing | Motor Mount x1 | DOWN | **55 mm** |
| 9 | Motor mounting screws (4) | the 4 countersunk motor screws, flush in the bracket centre | Part 1 x4 | DOWN | **25 mm** |

*The ASA housing stays fixed (it's the reference).*

Then, optionally: **Explode lines** → pick the bolt-head centre and its foot / locknut centre on each corner (4 lines), plus one line per motor screw. That matches the dashed guides in the renders.


## After you've built them
* I can read the views back (`GET .../explodedviews` plus the assembly definition with `explodedViewId`, about 3–4 read-only calls) and check every instance against these targets **once an API key works**.
* Or send a screenshot of each view and I'll compare it with `out/full_exploded_isometric.png` / `out/motor_mount_exploded.png`.
