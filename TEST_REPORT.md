# Version 6.38 validation report

## Baseline and scope

Source package: original PICU637.zip, extracted as the base for this update.
Baseline suite: 3,004 tests passed.
Updated full suite: 3,082 tests passed, including 78 new cases in
`tests/test_mode_specific_ventilator.py`.

The new tests cover the supplied PC, PRVC and home-vent source patterns, nested
labels, Avg/Min/Max parsing, set vs observed separation, inspiratory vs expiratory
volume labels, blank and zero-valued home settings, all supplied mode-name
mappings, synthetic VC cases, original C/D NIV combinations, named advanced NIV,
unknown/missing values, partial import recovery, retained source values,
encryption round trips, editor callbacks, room snapshots, and PDF/HTML/text
output with no cross-room ventilator content.

Existing test expectations were changed only where the user explicitly changed
printed labels or which parameters print for a mode. The original input fixtures
and standard-vs-ISTAT, CBC, lab, medication, and vital-value selection rules were
not changed. Printed-mode label assertions now use Mode rather than Vent Mode.
Legacy observed TV data remain saved even when the new volume-targeted profile
prints only set TV.

The three attached examples' C/D ranges were read through Files. Tests exercise
those source patterns plus the home-vent C section pasted in the conversation.
This release was not tested against every byte of every historical patient paste.
No complete patient sample is added to the package. New PDF previews use existing
synthetic fixtures, not the actual patients' full handoffs.

## Compatibility

A synthetic encrypted archive was created with the unmodified Version 6.37
modules. It was opened with this version and compared against its original JSON.
Every saved field, difficult-airway value, medication rule and timestamp matched.
It was then re-encrypted and reopened with the same generated test key, again
matching exactly. New ventilator values also have encryption round-trip tests.

Schema remains 26. Additional ventilation-value keys and supported NIV labels
mean that an older release may reject data saved with this release. Do not
roll back after saving newly captured ventilator fields.

## Printed output

The app generated PC, PRVC and Home Vent synthetic handoffs. The PDF preflight
reported one landscape page per room and 8-point body text for all three, without
requiring tighter spacing or balanced columns. All three rendered pages were
visually inspected. The middle example includes the retained difficult-airway
alert at the end. No clipped text or overlapping fields were seen.

## Unchanged components

The CBC, blood-gas, medication, laboratory, vital-sign, feeding, device,
pacemaker, anthropometric, export/page-fitting, encryption and GitHub storage
modules are unchanged from 6.37. The changed production files are app.py,
ventilation.py and noninvasive.py, plus new ventilator_modes.py.

No live Streamlit deployment, private repository, live device or patient record
was queried or modified. Interface/storage tests use the existing mocks and
synthetic data. This is software regression testing, not clinical validation.
