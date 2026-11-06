# Version 6.2 validation

## Executed checks

The unmodified Version 6.1 package passed all 432 tests before changes.
The updated suite passes 515 tests, including 83 new cases in
tests/test_neuro_weight.py. No tests were skipped. The suite was also run
from the extracted delivery ZIP. Command: PYTHONPATH=. pytest -q --disable-warnings

Historical fixtures were adjusted to remove fields that did not exist in their
old schemas. Current-schema assertions now expect 7. Existing medication,
respiratory, laboratory, security and mocked-storage tests remain in the suite.

New tests cover zero WAT-1, negative/zero SBS, blank headings and placeholders,
ICP/CPP source values, ranges, conflict rejection, independent I/K/L/M imports,
E-only imports preserving neuro values, weight/Z-score-only output, omitted
percentiles and footnotes, missing Z-score, dated weight selection, observed
versus set Vt, observed zero, missing observed Vt, field conflicts, new-patient
clearing, same-room editing, reversible inclusion, HTML escaping, schema-6
migration, encryption round trips, print-all selection, two-room landscape
exports and long-content continuation without dropped or duplicated values.

UI page rendering and callbacks use the existing Streamlit widget stub. They
do not implement a live browser lifecycle.

## Original-package compatibility

A separate process running the unmodified Version 6.1 code generated a synthetic
encrypted schema-6 archive with routing and visibility rules, four medications,
46 lab rows, vital signs, respiratory settings and notes. The new code opened
that ciphertext with the same generated test key. Every original room field and
Admin setting matched. Only new empty fields and schema 7 were added. No real
handoff archive, password or GitHub token was accessed.

## Export review

The two-room preview was generated with the application export functions,
rendered at 160 dpi and visually checked on both pages. It retains dated CBC
and BMP trees. Weight/Z-score follow diagnoses, WAT/ICP/CPP lead NEURO on page
one, SBS -1 leads NEURO on page two, and observed Vt follows set Vt in RESP.
No clipped or overlapping text was observed in this preview.

## Limits

Streamlit is not installed in this environment. A real browser session, hosted
app deployment and authenticated private storage connection were not tested.
No direct GitHub changes were made. Storage tests use mocked requests.

This is source-text extraction, not a clinical determination of treatment,
current device use or bedside accuracy. No score, weight, Z-score, pressure or
volume is calculated. Unfamiliar source formats may need additional handling.
Use the synthetic examples after deployment, then compare clinical handoffs
with their source. Tests do not establish privacy or regulatory compliance.
