# Version 6.37 validation report

## Baseline and changes

The package was built by extracting the original PICU635.zip. The unmodified
baseline suite was run first: 2,924 tests passed. No Version 6.36 font-size
control or print_options.py module was used.

Current full suite: 3,004 tests passed, including 80 new synthetic cases in
test_compact_airway.py. Existing assertions for explicitly removed output
(headings, printed warnings, timing annotations, order column), the new default
font, and the new current schema were updated to the requested behavior.
Legacy input fixtures, clinical result-selection expectations and parser tests
remain in the suite. The legacy schema fixtures were not changed into new data.

The new coverage includes optional/disabled airway output, all ventilation and
passage responses, field limits, escaping, no invented normal answers, per-room
callbacks, new-patient clearing, clear-all clearing, room-switch capture,
encryption round trips, no cross-room print leakage, failed saves retaining
pending edits, displayed publication times and rejected publications, source
note suppression, NGTD display-only abbreviation and deduplication, unchanged
lab window eligibility, retained lab values/dates/labels, seven-column printing,
and medication fallback when an old mapping used the removed Labs column.

## Migration

A synthetic encrypted archive was created with the unmodified original 6.35
code and opened using this release with the same key. Schema 25 became 26.
Every previous room field, mapping, setting, custom room, reset generation and
saved timestamp compared equal. An added difficult-airway record was then
saved, encrypted, reopened and compared equal.

## Printed output

The app generated a two-room synthetic preview. Both rooms occupy one landscape
page at the default 8-point body font. One has an enabled airway alert and one
does not. The final PDF was rendered to PNGs and visually checked. Lab labels,
values, dates, organism formatting, seven columns, and the final airway band
were inspected. No patient input is bundled with this release.

## Limits

Callback/interface tests use widget stubs and storage tests use simulations.
They are not live-browser or production deployment tests. No live GitHub
repository, Epic session, institution network or deployed app was accessed or
modified. The airway form is clinician-entered documentation, not a validated
clinical decision algorithm. Auto-fitting cannot guarantee one page for every
possible volume of content and never crops text to force that target.
