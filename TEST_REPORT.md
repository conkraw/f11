# Version 6.28 validation

The original Version 6.27 package passed all 2,229 inherited tests before edits.
The updated suite passed 2,324 tests: 2,229 inherited tests plus 95 diet/lactate
checks. Existing migration fixture shapes and current-schema expectations were
updated for the new diet field. Lactate output assertions were updated for the
requested endpoints. No inherited tests were removed or skipped.

Tests cover adult/pediatric regular and liquid diets, NPO with exceptions,
tube-feeding types, PN/TPN/PPN and label exclusion, inactive order exclusion,
multiple-order warnings, duplicated summaries, missing/empty X, independent
partial updates, failed-X hiding, manual corrections, HTML escaping, room
switch autosave, output inclusion, and encrypted storage.

Lactate tests cover all requested aliases, cross-alias date selection, explicit
time sorting, same-date ambiguity, numeric and flagged results, zero, supplied
units, comparisons, rejected samples, nonnumeric values, exclusions, empty
snapshots, and preservation of source records. Nothing is averaged or converted.
The earliest result is only the earliest in the pasted G snapshot.

Eight supplied X-section excerpts and four supplied lactate-row patterns were
checked separately. Original complete patient documents are not included in
this package, and are not claimed to have been tested end-to-end in this update.

A synthetic archive was generated with the actual original Version 6.27 code,
encrypted, and opened with Version 6.28 using the same key. Every prior room
field, setting, saved timestamp and reset generation was preserved. The only
new snapshot is diet=null and the schema changes from 21 to 22. A second
same-key encrypted round trip passed.

Three synthetic landscape preview pages were rendered and visually inspected.
Each room fits on one page. Diet appears below intake/output and before feeds.
Lactate appears in Cardiovascular after vital signs/pacing, before CV Infusions.
The two values retain their individual dates and original component codes.

Unchanged runtime modules, byte-for-byte compared with the delivered 6.27 ZIP:

admin_access.py, blood_gases.py, cbc.py, create_secrets.py, cultures.py, demographics.py, devices.py, feeds.py, fluid_balance.py, github_store.py, guide_store.py, handoff_reset.py, infusions.py, lab_layout.py, medication_groups.py, medications.py, microbiology_display.py, noninvasive.py, observations.py, output_text.py, pacemaker.py, print_time.py, recurring_orders.py, save_status.py, security.py, set_admin_password.py, user_guide.py, ventilation.py, viral.py, vitals.py.

The delivery ZIP is read back and verified with SHA256SUMS.txt. The full test
suite is also rerun from an independent extraction of that ZIP. No deployment
secrets, encryption keys, real patient input files or new font files are added.

Limits: UI tests use Streamlit widget stubs. GitHub tests use mocked responses.
The live Streamlit deployment and authenticated private repository were not
accessed or tested. Missing collection times, stale orders and clinical context
still require source review. The app does not make treatment decisions.
