# Validation report: Version 6.17

## Executed checks

1,578 automated tests passed in the build environment. The original unmodified
Version 6.16 package first passed all 1,431 of its tests. Version 6.17 adds 147
cases covering the new grouping and calcium requirements. Existing assertions
were updated only for intentionally changed headings, default grouping order,
and the added schema-17 setting. Historical archive fixtures now omit the new
setting when constructing older schema versions. No test was disabled or skipped.

Command: python -m pytest -q --disable-warnings

The delivery ZIP is extracted into a clean directory and the complete suite is
run again before delivery. The ZIP has a CRC check and a SHA-256 manifest for
every packaged file apart from the manifest itself.

## New coverage

Tests cover all specified medications, mixed case and known held/start/sequence
prefixes. Heparin tests distinguish an ordered Units/kg/hr dose from product
concentration, Last Rate, flushes, irrigation/lock mixtures, mL/hr carriers,
other units and missing doses. Enoxaparin and cangrelor are separately tested
without applying the heparin unit restriction. PRN grouping requires the recorded
frequency and is tested against scheduled, continuous, once-only and blank values.

Tests check each requested diuretic, one output occurrence per order, preservation
of all original fields, hidden/excluded orders, custom wording and escaping,
source qualifiers, continuous-versus-PRN distinctions, and output-only removal
of (Dosing Weight). Cardiovascular infusion names and ordered doses are checked
for bold PDF/HTML formatting. Multi-room and long-CV-list tests verify complete
continuation without truncation. Existing vitals and lactate remain above CV
Infusions, and existing neurologic observations remain above neurologic groups.

Reusable group choices, Admin editing without an open room, room-change capture
of pending choices, failed write/conflict rollback, manual system reassignment,
re-import persistence and cross-group reset behavior are tested. Calcium tests
confirm both latest and preceding CA results beneath BMP with Mg and Phos,
including dates, abnormal flags and no source mutation.

## Original-code migration check

The original Version 6.16 ZIP was independently extracted and executed to create
a synthetic encrypted schema-16 archive. Version 6.17 opened it with the same
key. Every old room field compared equal, including import warnings, hidden
orders and infusion overrides. Every prior Admin setting compared equal. The
only added setting was medication_groups: []. A new encrypted round trip also
passed. No actual user archive or deployment secret was accessed. Temporary
synthetic keys and archive files are outside the delivered package.

## Unchanged core components

The following runtime files compare byte-for-byte with Version 6.16: cbc.py,
blood_gases.py, labs.py, lab_layout.py, parser.py, noninvasive.py, ventilation.py,
github_store.py, security.py and import_review.py. CA support already existed in
the lab parser, and this release adds explicit regression verification rather
than altering working lab/CBC/gas parsing. Medication source parsing is unchanged,
with only validation of the new optional group choice added.

## Visual inspection

The synthetic PDF was rendered and visually checked. It is one landscape Letter
page at the existing 7.2-point body size. The preview includes title-case Infusions,
CV Infusions, PRN, Paralytic PRN, Fever Control, Diuretics, DVT Prophylaxis and
calcium beside Mg and Phos. CV/neuro infusion names and doses are emphasized,
with pump rates separate. Hidden values and (Dosing Weight) do not reappear in
handoff output. No overlap or clipped content was observed in this preview.

## Limitations

Streamlit is not installed in this build environment. Interface tests use a
widget/session stub, not a live Streamlit browser session. GitHub tests use
mocked storage responses, not an authenticated private repository. No live
Epic, hosted deployment, team-access flow, or actual clinical record was tested.
The tests do not establish clinical validity, drug indications, dose correctness,
privacy compliance or error-free handling of every possible paste. The DVT
Prophylaxis label is a user-defined display heading, not an indication or dose
assessment. Use the synthetic example first in the deployment.
