# Version 6.39 validation report

## Source and test results

Base: the delivered /mnt/data/PICU638.zip, not a reconstruction.
Original full suite before changes: 3,082 passed.
New focused module: 158 passed in tests/test_cv_resp_endocrine_categories.py.
Updated full suite: 3,247 passed.
The increase of 165 is 158 new tests plus seven additional cases in an existing
parameterized test that automatically covers all supported medication groups.

Existing test expectations were changed only for requested display changes:
- two former HTML-download assertions now extract the surviving PDF download
- the milrinone example expects Inotrope Infusions rather than CV Infusions
- save status expects shared storage rather than the provider name

An existing read-only-editor test found that exposing the new group selector
could add an unnecessary group_mode=auto to legacy medication records. The
snapshot collector now avoids adding unchanged optional automatic settings.
The original assertion was retained and passes.

## Coverage

All requested named defaults, case variants, start/held annotations, lidocaine
infusion-only routing, epinephrine bolus/nebulization exclusions, phenylephrine
local-route exclusions, topical/rectal hydrocortisone exclusions, endocrine
injections versus infusions, matching boundaries, distinct epinephrine versus
norepinephrine and enalapril versus enalaprilat, shared override persistence,
manual clonidine placement, hidden/excluded orders, no duplicate output, output
heading order, Last Admin rate emphasis, encryption round trips, and UI removal
were exercised with synthetic inputs.

UI tests use widget stubs, not a live Streamlit browser. Storage callbacks use
mock responses, not the user's private repository. Removing provider branding
was tested without changing HTTP headers or the storage API endpoint.

## Compatibility

A separate interpreter loaded the unmodified Version 6.38 modules extracted
from the original ZIP and generated an encrypted synthetic archive with two
rooms, a custom room, a remembered medication mapping, saved timestamps and
reset metadata. The new release opened it and compared it exactly with its
original JSON. It was re-encrypted with the same generated test key and reopened
without changing any field. No credentials or clinical handoffs are packaged.

These modules are byte-for-byte unchanged from Version 6.38: parser.py,
importing.py, infusion_rates.py, medication_columns.py, ventilation.py,
ventilator_modes.py, noninvasive.py, labs.py, lab_windows.py, vitals.py, cbc.py,
blood_gases.py, feeds.py, diet.py, devices.py, pacemaker.py, anthropometrics.py,
difficult_airway.py, security.py and models.py.

Medication grouping/validation and display modules changed. Storage adapter
changes are limited to user-facing error wording. The schema remains 26.
Older versions will not understand newly saved group choices.

## Preview

The app generated a synthetic landscape handoff demonstrating every new group.
The actual export renderer reports one page at 8-point body text, without tighter
spacing or adjusted column widths. Its rendered page was visually inspected.
No clinical patient data are used in that preview.

Automatic fitting still runs during export. This synthetic example is not a
promise that every real handoff will fit on one page. Long handoffs continue
rather than dropping entries. The routine UI diagnostics table is removed.

## Limitations

No live deployment, private archive connection, clinical integration, or clinical
validation was performed. Categories implement the user's organizational choices,
not a clinical indication or treatment recommendation. Existing published custom
instructions are not overwritten. Removing UI wording does not add security.
