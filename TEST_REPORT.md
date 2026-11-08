# Validation report: Version 6.25

## Executed tests

The unmodified Version 6.24 ZIP passed all 1,994 existing tests in this build
environment. Version 6.25 passes 2,061 tests with:

    PYTHONPATH=.:tests pytest -q --disable-warnings

The 67 new cases exercise summary parsing, pressure units, reordered statistics,
aliases, case/Unicode/whitespace variants, missing data, single values, zeros,
negative CVP, extremes above 100, conflicting bounds and units, editor controls,
room-change autosave, other rooms, encrypted round trips, PDF/HTML/text and
Print all. No existing test assertion was weakened or skipped.

Both supplied E-block excerpts were separately reproduced against the original
6.24 code. Each was rejected by the old colon-only parser on No data recorded.
The new code imports all six previous vital rows unchanged and the new monitor
range. The ETCO2 example preserves 37 to 177 mmHg. The CVP example preserves
8 to 25 mmHg. The absent monitor in each sample is not invented. These were
E-block checks, not a claim that the complete patient files were retested.
The patient source files are not included in this package.

Only vitals.py contains a clinical behavior change. app.py changes its version
identification and error_store.py changes the technical app version. All other
previous runtime Python modules are byte-for-byte unchanged. Dependencies and
schema 19 are unchanged.

A separate process running the original 6.24 code created an encrypted archive
with synthetic records. Version 6.25 opened it with the same key. Every stored
field, setting, room, reset generation and timestamp was unchanged, and the
existing formatted handoffs were identical. Re-encryption also round-tripped.

The new synthetic PDF was rendered and visually inspected. It fits on one
landscape page. ETCO2 appears above respiratory support and medication groups.
CVP appears above CV Infusions. There was no clipped text or overlap.

The complete release ZIP is integrity/hash checked, extracted again, and its
full test suite rerun before delivery.

## Limits

Streamlit interface tests use a widget stub. GitHub tests use mocked responses.
The hosted browser application, real team concurrency and authenticated private
storage were not tested. No live repository was accessed or changed.

This is extraction of documented values, not verification of bedside validity.
Recorded extremes are not clipped or replaced. Summary averages are omitted,
and values are not calculated from another field, specimen, room, or section.
An ambiguous summary keeps the existing E section with a review warning under
the established section-recovery behavior. Re-paste and verify against Epic.
