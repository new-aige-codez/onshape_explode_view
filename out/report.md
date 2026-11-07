# Exploded-view build report

**These are external visualizations.** No native Onshape exploded view was created, and the Onshape document, parts and mates were not modified.

## Inventory vs. expected

| Group | Expected | Found | OK |
|---|---:|---:|:-:|
| ASA housing | 1 | 1 | yes |
| Tamper plate + pins | 1 | 1 | yes |
| Handle | 1 | 1 | yes |
| 5052 Al X-bracket | 1 | 1 | yes |
| 3650 vibration motor | 1 | 1 | yes |
| M5 housing bolts | 4 | 4 | yes |
| Al compression sleeves | 4 | 4 | yes |
| Upper bearing washers | 4 | 4 | yes |
| Lower M5 locknuts | 4 | 4 | yes |
| M4 countersunk handle screws | 2 | 2 | yes |
| Captive M4 handle nuts | 2 | 2 | yes |
| Rubber isolation feet | 4 | 4 | yes |
| Motor mounting screws | 4 | 4 | yes |
| Motor locknuts | 4 | 4 | yes |
| Lower M5 washers | 0 | 0 | yes |
| Motor washers | 0 | 0 | yes |
| Foot mounting hardware | 0 | 0 | yes |

## Geometry checks

| Check | OK | Detail |
|---|:-:|---|
| total instances imported | yes | 37 mesh instances |
| every instance classified | yes | unclassified: none |
| housing height vs brief (128.5 mm) | **NO** | CAD 135.00 mm (bbox 192.0 x 192.0 x 135.0) |
| bracket thickness vs brief (4.75 mm) | **NO** | Motor Mount: CAD 5.00 mm |
| motor envelope ~110x66x48 | yes | Part 1.002: 110.0 x 66.0 x 48.5 mm |
| motor centred on bracket | yes | XY offset motor->bracket centre 0.00 mm |
| motor orientation | yes | motor long axis along X; below bracket: True |
| coaxial stack @ Part 1.001 | yes | sleeve Part 1.003 dXY=0.00; upper_washer Plain washer grade A HV200 M5 dXY=0.00; lower_locknut Prevailing torque nut thin M5x0.002 dXY=0.00 |
| bracket hole on axis of Part 1.001 | yes | clear |
| housing channel on axis of Part 1.001 | yes | clear through-channel |
| coaxial stack @ Part 1.010 | yes | sleeve Part 1.007 dXY=0.00; upper_washer Plain washer grade A HV200 M5.002 dXY=0.00; lower_locknut Prevailing torque nut thin M5x0.80 dXY=0.00 |
| bracket hole on axis of Part 1.010 | yes | clear |
| housing channel on axis of Part 1.010 | yes | clear through-channel |
| coaxial stack @ Part 1.017 | yes | sleeve Part 1.004 dXY=0.00; upper_washer Plain washer grade A HV200 M5.003 dXY=0.00; lower_locknut Prevailing torque nut thin M5x0.001 dXY=0.00 |
| bracket hole on axis of Part 1.017 | yes | clear |
| housing channel on axis of Part 1.017 | yes | clear through-channel |
| coaxial stack @ Part 1.018 | yes | sleeve Part 1 dXY=0.00; upper_washer Plain washer grade A HV200 M5.001 dXY=0.00; lower_locknut Prevailing torque nut thin M5x0.003 dXY=0.00 |
| bracket hole on axis of Part 1.018 | yes | clear |
| housing channel on axis of Part 1.018 | yes | clear through-channel |
| bracket hole for Part 1.008 | yes | clear |
| bracket hole for Part 1.011 | yes | clear |
| bracket hole for Part 1.013 | yes | clear |
| bracket hole for Part 1.016 | yes | clear |
| tamper centred over housing | yes | XY offset 0.01 mm; explosion is pure +Z so offset is preserved |
| tamper pins over cavities | yes | 100 pin clusters detected, 100 sit over open cavities |
| assembled-state contacts/interferences (INFO: touching faces and nominal threads count; review for real clashes) | info | 43 pairs: Motor Mount x Part 1, Motor Mount x Part 1.002, Motor Mount x Part 1.003, Motor Mount x Part 1.004, Motor Mount x Part 1.007, Motor Mount x Part 1.008, Motor Mount x Part 1.011, Motor Mount x Part 1.013, Motor Mount x Part 1.016, Motor Mount x Preroll Housing, Motor Mount x Prevailing torque nut thin M5x0.001, Motor Mount x Prevailing torque nut thin M5x0.002, Motor Mount x Prevailing torque nut thin M5x0.003, Motor Mount x Prevailing torque nut thin M5x0.80, Part 1 x Plain washer grade A HV200 M5.001, Part 1.001 x Part 1.015, Part 1.001 x Plain washer grade A HV200 M5, Part 1.001 x Prevailing torque nut thin M5x0.002, Part 1.003 x Plain washer grade A HV200 M5, Part 1.004 x Plain washer grade A HV200 M5.003, Part 1.005 x Tamper Plate, Part 1.006 x Tamper Plate, Part 1.007 x Plain washer grade A HV200 M5.002, Part 1.008 x Prevailing torque nut thin M4x0.003, Part 1.009 x Part 1.010, Part 1.010 x Plain washer grade A HV200 M5.002, Part 1.010 x Prevailing torque nut thin M5x0.80, Part 1.011 x Prevailing torque nut thin M4x0.002, Part 1.012 x Part 1.017, Part 1.013 x Prevailing torque nut thin M4x0.004, Part 1.014 x Part 1.018, Part 1.016 x Prevailing torque nut thin M4x0.005, Part 1.017 x Plain washer grade A HV200 M5.003, Part 1.017 x Prevailing torque nut thin M5x0.001, Part 1.018 x Plain washer grade A HV200 M5.001, Part 1.018 x Prevailing torque nut thin M5x0.003, Plain washer grade A HV200 M5 x Preroll Housing, Plain washer grade A HV200 M5.001 x Preroll Housing, Plain washer grade A HV200 M5.002 x Preroll Housing, Plain washer grade A HV200 M5.003 x Preroll Housing ... |
| every group clearly visible in full_exploded_isometric | yes | all groups visible; occluded instances (normal for back side): ['Part 1.005', 'Part 1.008', 'Part 1.010', 'Part 1.011', 'Plain washer grade A HV200 M5.002', 'Prevailing torque nut thin M4x0.003', 'Prevailing torque nut thin M4x0.004', 'Prevailing torque nut thin M5x0.80'] |
| every group clearly visible in motor_mount_exploded | yes | all groups visible; occluded instances (normal for back side): ['Part 1.009'] |
| materials assigned per group | yes | all correct |

## Explosion offsets (mm, after collision solver)

### assembled_isometric

| Group | dZ |
|---|---:|
| Handle | +0 |
| Captive M4 handle nuts | +0 |
| M4 countersunk handle screws | +0 |
| Tamper plate + pins | +0 |
| M5 housing bolts | +0 |
| Upper bearing washers | +0 |
| Al compression sleeves | +0 |
| ASA housing | +0 |
| 5052 Al X-bracket | +0 |
| Lower M5 locknuts | +0 |
| Motor mounting screws | +0 |
| 3650 vibration motor | +0 |
| Motor locknuts | +0 |
| Rubber isolation feet | +0 |

Visibility: 9/37 parts clearly visible - poorly visible: Motor Mount (12%, 1767px), Part 1 (0%, 794px), Part 1.002 (13%, 764px), Part 1.003 (0%, 794px), Part 1.004 (0%, 794px), Part 1.005 (0%, 93px), Part 1.006 (0%, 93px), Part 1.007 (0%, 794px), Part 1.008 (0%, 144px), Part 1.009 (0%, 132px), Part 1.010 (5%, 1218px), Part 1.011 (0%, 144px), Part 1.013 (0%, 144px), Part 1.016 (0%, 144px), Plain washer grade A HV200 M5 (0%, 68px), Plain washer grade A HV200 M5.001 (0%, 68px), Plain washer grade A HV200 M5.002 (0%, 68px), Plain washer grade A HV200 M5.003 (0%, 68px), Prevailing torque nut thin M4x0.001 (0%, 54px), Prevailing torque nut thin M4x0.002 (0%, 54px), Prevailing torque nut thin M4x0.003 (0%, 54px), Prevailing torque nut thin M4x0.004 (0%, 54px), Prevailing torque nut thin M4x0.005 (0%, 54px), Prevailing torque nut thin M4x0.70 (0%, 54px), Prevailing torque nut thin M5x0.001 (0%, 62px), Prevailing torque nut thin M5x0.002 (2%, 62px), Prevailing torque nut thin M5x0.003 (2%, 62px), Prevailing torque nut thin M5x0.80 (0%, 62px)

### full_exploded_isometric

| Group | dZ |
|---|---:|
| Handle | +330 |
| Captive M4 handle nuts | +285 |
| M4 countersunk handle screws | +191 |
| Tamper plate + pins | +240 |
| M5 housing bolts | +175 |
| Upper bearing washers | +145 |
| Al compression sleeves | +80 |
| ASA housing | +0 |
| 5052 Al X-bracket | -40 |
| Lower M5 locknuts | -70 |
| Motor mounting screws | -20 |
| 3650 vibration motor | -105 |
| Motor locknuts | -154 |
| Rubber isolation feet | -95 |

Visibility: 29/37 parts clearly visible - poorly visible: Part 1.005 (0%, 42px), Part 1.008 (0%, 65px), Part 1.010 (9%, 572px), Part 1.011 (5%, 65px), Plain washer grade A HV200 M5.002 (0%, 30px), Prevailing torque nut thin M4x0.003 (0%, 24px), Prevailing torque nut thin M4x0.004 (0%, 24px), Prevailing torque nut thin M5x0.80 (0%, 28px)

### motor_mount_exploded

| Group | dZ |
|---|---:|
| M5 housing bolts | +190 |
| Upper bearing washers | +160 |
| Al compression sleeves | +110 |
| ASA housing | +0 |
| 5052 Al X-bracket | -55 |
| Lower M5 locknuts | -100 |
| Motor mounting screws | -25 |
| 3650 vibration motor | -150 |
| Motor locknuts | -210 |
| Rubber isolation feet | -140 |

Visibility: 30/31 parts clearly visible - poorly visible: Part 1.009 (0%, 67px)

### corner_fastener_detail

| Group | dZ |
|---|---:|
| M5 housing bolts | +175 |
| Upper bearing washers | +150 |
| Al compression sleeves | +85 |
| ASA housing | +0 |
| 5052 Al X-bracket | -25 |
| Lower M5 locknuts | -55 |

Collision solver made 2 adjustments (see manifest.json `solver_moves`).
