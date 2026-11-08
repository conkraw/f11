# Validation report: Version 6.24

## Executed checks

The unmodified Version 6.23 delivery ZIP passed its existing 1,892 tests in this
build environment before changes. Version 6.24 passed 1,994 tests with:

```
PYTHONPATH=.:tests pytest -q --disable-warnings
```

The 102 added tests cover explicit tube methods, hourly rates qualified by the
source label, removed lines, per-device matching, no cross-tube rate inheritance,
backup hourly rates, volume-only intake, unknowns, zero and decimal rates,
conflicts, duplicate lines, partial-section recovery, source escaping, encrypted
round trips, session upgrades, unblurred edits during room autosave, exclusion
and restoration, Print all, clear-all, and FEN/GI output order.

Historical migration fixtures were updated to omit the new feeds field when
constructing an older schema and to expect the new feeds=None default afterward.
Existing clinical behavior assertions were retained. No test is skipped.

The four supplied T-section excerpts were independently checked. They produce:
NJ with its explicit rate, PEG with its explicit rate and removed tube entries
excluded, separate NJ and GT entries with an unknown GT rate, and a jejunostomy
entry with UNK because its backup is volume-only. The supplied patient sources
are not included in the delivery folder or used as the preview records.

A separate process using the unmodified Version 6.23 code created an encrypted
schema-18 archive with 23 synthetic rooms. Version 6.24 opened it using the same
key. Every original room field, save timestamp, setting and reset generation was
unchanged. Formatted preexisting fields were identical, and a new encrypted
round trip retained the migrated content.

The synthetic three-room PDF was rendered at 140 dpi and each page was visually
inspected. Feeds appears beneath totals when present, and above medication
subgroups and notes. The primary-rate, backup-rate and UNK examples each fit on
one landscape page. The source backup volume does not print as an hourly rate.

## Limits

Streamlit UI tests use a widget stub. GitHub tests use mocked responses. The
hosted browser application, real team concurrency and authenticated private data
repository were not exercised. The feeding display is a summary of supplied
records, not verification that all unremoved devices are in current use.

No source method, formula or rate is reconstructed from other sections. Intake
volume is not treated as an hourly rate. Unknowns and review warnings require
comparison with Epic before clinical use.

Existing dependencies are unchanged. No live repository was read or modified.
