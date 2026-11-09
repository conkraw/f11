# Version 6.40 validation report

## Baseline and regression checks

The input was the actual delivered PICU639.zip. ZIP integrity and its SHA-256
file manifest were verified before editing. Its original suite passed:

3247 passed in 42.25 seconds.

The updated suite passed after the requested display expectations were updated:

3374 test cases. See the extracted-delivery validation run.

The added test module supplies 122 synthetic cases. Five additional cases come
from the existing parametrized group-choice tests expanding to the new choices.
No tests were removed. Historical assertions were changed only where the user
requested new labels, category placement, or a different presentation order.

The coverage includes generic-name and source-annotation matching, case handling,
nonmatching suffixes, local dexamethasone exclusions, hidden/excluded medications,
explicit group overrides, new grouping callbacks and encrypted rule round trips,
continuous vs PRN paralytics, no duplicate medication entries, stable same-name
taper order, alphabetic category/medication order, preserved Last Admin emphasis,
TV source-field preservation, single/multiple/same-day/cross-day lactates, old and
future result exclusion, time-window boundaries, result exclusion, flags/units,
PDF/HTML/text agreement, and a two-room PDF packet.

## Compatibility and scope

A synthetic archive was created and encrypted with the unmodified 6.39 code.
The updated code opened it using the same key, with exact equality to the saved
original fields, mappings, custom room and timestamps.

Changed production files:

app.py
infusions.py
lab_windows.py
medication_groups.py
ventilation.py

The schema/model file, medication source parser, lab parser, CBC parser,
blood-gas parser, security and storage implementation are byte-for-byte unchanged.
An AST comparison confirmed that format_ventilation is the only changed
function/class in ventilation.py. Ventilator input parsing is unchanged.

No new dependencies or secret settings were added. New enum/group choices require
this or a compatible later version after they have been saved.

## Rendering

The delivered synthetic preview renders to one landscape page at 8-point body
text. It was rasterized with the PDF rendering utility and visually inspected.
The PDF opens correctly in PyMuPDF and has no encryption, XFA, or scanned pages.
The preview demonstrates the new neurologic order, preserved infusion emphasis,
Observed TV, and the compact lactate trend. Actual clinical handoffs can need
more than one page depending on their contents. No clinical text is removed to
force a page target.

## Limits

The UI checks use a Streamlit widget stub, not a live browser deployment. Storage
and conflict tests are simulated. The user's running application, repository,
credentials and live patient archive were not accessed or modified. Patient
uploads and private runtime inputs are not included in the delivery package.
The tests use synthetic records and do not validate medication indications or
clinical treatment choices. This update changes presentation and group defaults.
