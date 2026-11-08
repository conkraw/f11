# Version 6.30 verification

Updated automated suite: 2,614 passing tests.
New Version 6.30 tests: 194 cases.

The suite covers exact rolling-24-hour boundaries, future dates, Eastern time and
DST elapsed-time changes, date-only uncertainty, all lactate aliases, source-code
omission, CK and NT-proBNP placement, admission filtering, nonnumeric statuses,
excluded rows, missing admission and failed-import safeguards. Source row objects
are compared before and after display generation to verify no mutation.

Review-rule tests cover all eight requested low-result conditions, explicit
L/LL/LOW flags, high and undirected abnormal flags, latest-normal versus earlier-low
results, preadmission and future values, patient-specific numeric limits with
matching units, and existing Q-section hemoglobin selection. Creatinine tests
cover direction, greater-than-50% threshold, dates and times, seven-day window,
zero baselines, censored results and units. Medication tests cover hidden/excluded,
held, future and ADS-only rows. Device and medication findings remain review
prompts with explicit limitations.

Review-state tests exercise edits, confirmation, dismissal, display hiding,
evidence-fingerprint invalidation, escaped custom wording, encrypted round trips,
source-diagnosis immutability, callback validation, room-switch autosave and
capture of pending editor changes. These UI tests use a Streamlit stub, not a
browser or live Streamlit runtime.

Existing regression expectations were updated only where the specified behavior
changed: schema 24, deterministic clock/admission fixtures for historical lab
examples, source-code omission, numeric-only selected levels, and the separate
static lab-evaluation timestamp in downloaded HTML. No tests were skipped to
obtain a passing result.

A synthetic archive was created and encrypted by the original Version 6.29 code.
The new code opened it with the same synthetic key. Every non-schema field,
including every sheet, mapping, custom room, reset generation and save timestamp,
compared equal. Schema 23 becomes 24. That migrated archive passed an additional
encrypted round trip.

The supplied full SmartPhrase imported with zero errors and no skipped sections.
Checks verified that old lactate and CK and preadmission inflammatory markers do
not appear in the filtered summary, the recent theophylline result and the latest
all-time NT-proBNP are retained, a falling creatinine does not trigger kidney-injury
review, and the valid Epic meters-squared BSA phrase is accepted. The source
specimen is not included in this package. Any test medication mapping used for
this check was synthetic and did not change the user's saved mappings.

The synthetic demonstration PDF renders on one landscape page at the existing
7.2-point body font. The highlighted review band, laboratory groups and device
footer were visually inspected. Text checks confirmed that source lactate codes
and deliberately old CK values were absent, and that reviewed versus unreviewed
labels remain distinguishable. Clinical information is never truncated to fit.

Byte-for-byte unchanged from Version 6.29:
cbc.py, blood_gases.py, medications.py, labs.py, lab_layout.py, vitals.py,
feeds.py, diet.py, devices.py, pacemaker.py, cultures.py, recurring_orders.py,
ventilation.py and noninvasive.py.

The current suite is also run from an extracted copy of the delivery ZIP. The ZIP
has an integrity check plus a SHA-256 manifest for every packaged file except the
manifest itself. No uploaded clinical source files, runtime secrets, synthetic
migration keys, cache files or font files are packaged.

Limitations: Streamlit is not installed in this build environment. Network tests
use mocks. The live app, authenticated private repository connection, multi-user
browser behavior and institutional clinical validation have not been tested.
This feature is a documentation-review aid, not a validated diagnostic system.
No direct changes were made to the user's GitHub repositories.
