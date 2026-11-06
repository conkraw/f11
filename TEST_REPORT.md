# Version 6.4 validation

## Executed checks

The unmodified Version 6.3 package passed 552 tests before changes. The updated
suite passes 588 tests, including 36 new tests in tests/test_spo2_range.py.
Command: PYTHONPATH=. pytest -q --disable-warnings

Coverage includes the supplied Avg/Min/Max syntax, optional colon and units in
the label, tabs, case, subscript 2, nonbreaking spaces, decimal precision,
reordered statistics, zero and equal limits, and unchanged ordinary vitals.
Incomplete, conflicting, reversed or malformed limits do not produce a guessed
range and do not replace the draft. The average is never used as an endpoint.

Integration checks cover one-click E import, E-only replacement without changes
to other sections, repeated imports without duplication, omitted and empty E,
editing/inclusion callbacks, placement before respiratory support and notes,
PDF/HTML/text and multi-room export, and an encrypted archive round trip.
The earlier 552 tests cover the inherited medication, ventilation, labs,
neurologic observations, weight, compact printing and storage behavior.

## Print check

A synthetic compact handoff includes the new SpO2 summary. Its PDF output fits
on one landscape page and contains SpO2: 93% to 100% in RESP with no average.
The new preview was rendered and visually inspected. The range is legible at
the top of RESP. No clipping, overlaps or missing range text were found.

## Compatibility and limits

Archive schema remains 7. Existing fields, medication rules, encryption,
storage, authentication, export implementation and requirements are unchanged.
Previously saved summaries are not automatically rewritten. Re-paste a complete
E block to replace its imported vital signs with the new parser behavior.

Streamlit is not installed in this build environment. UI tests use widget
stubs, not a real hosted browser session. No authenticated live private data
repository was accessed. No direct GitHub changes were made.
