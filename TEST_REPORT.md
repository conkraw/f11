# Version 6.46 local validation

Base: the supplied PICU645.zip. The updated full test suite passed:
3,890 passed in 136.17 seconds. The 86 focused regression cases in
`tests/test_sbs_window_filgrastim.py` also passed independently.

The exact new K structure with a blank SBS Last 24 Hours field and historical
SBS -1 imports without error and displays SBS: None. Tests cover positive and
negative scores, zero, missing data, same-line and multiline boundaries, a
historical value with a recent date, repeated labels, explicit targets, actual
observation times, rolling 24-hour limits, future dates, snapshot aging, source
report times, independent updates, invalid rows, and historical-value isolation.

Additional tests cover the Hematology category, filgrastim biosimilar names,
existing explicit mappings, hidden medications, no duplicate output, manual
editing callbacks, PDF/HTML/text/Print all, and non-mutating rendering.
The existing schema-number assertions were updated from 30 to 31 for the
intentional archive upgrade. No existing tests were removed or skipped.

A synthetic archive was generated and encrypted by the original 6.45 modules.
This release opened it with the same generated test key and preserved all
existing room fields, custom rooms, settings, category names, and saved times.
Only schema 31 and the missing built-in G-CSF category were added. A subsequent
encrypted round trip was identical.

Both preview pages contain synthetic examples. Each fits on one landscape page
at 8-point body text with no extra compression. The generated pages were
rendered and visually inspected. Long real handoffs may still require more pages.

The final delivery ZIP is integrity-checked and contains SHA256SUMS.txt. Focused
regressions are rerun from a clean extraction, with their result recorded in
DELIVERY_VERIFICATION.txt. All shipped Python sources are identical to those
used for the full-suite run.

UI and storage tests use local simulations. No live deployment, private storage,
patient archive, or deployment credentials were accessed or modified. This is
software testing, not clinical validation. The snapshot's report/import time is
not an invented SBS observation time.
