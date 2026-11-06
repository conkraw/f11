# Version 6.3 validation

## Executed checks

The unmodified Version 6.2 package passed all 515 tests before changes.
The updated package passes 552 tests, including 37 new tests in
tests/test_compact_pn.py. No tests were skipped. The complete suite was also rerun from the extracted delivery ZIP. Command:
PYTHONPATH=. pytest -q --disable-warnings

The new checks cover standalone/tab-indented/bulleted/trailing-cell And
connectors, line endings, preserved PN doses/rates, separate lipid orders,
held/start-date context, mapping and exact hiding, mixed taper/And sequences,
atomic rejection of incomplete connectors, all 18 synthetic orders, horizontal
dated lab summaries, independent arterial/venous groups, complete small-font
one-page output, multi-room printing and deliberate overflow without dropped
or duplicated sentinel text. User-editable long lab values use wrapping text
rather than spilling across trees.

One inherited encryption test was made non-flaky. It previously required the
three characters WBC to be absent anywhere in random base64 ciphertext, where
that short sequence can occur by chance. It now checks a structured plaintext
JSON marker and the exact decrypted archive. Runtime encryption was not changed.

## Reproduction and layout checks

The old parser reproduced row 5's column error on the supplied PN/And/lipid
pattern. The corrected parser accepted all 18 orders. Provider and Last Admin
are not retained. The supplied medication, vitals, respiratory, laboratory and
weight pattern was exercised locally, with provider names substituted by test
sentinels. This local verification source is not bundled in the ZIP.

That verification handoff fits on one landscape Letter PDF page at 7.2 pt.
The independent synthetic 18-order fixture also fits on one page, both unmapped
and with demonstration system mappings. Its PDF preview was rendered and
visually inspected. Dates, abnormal flags, PN rates, status labels and all
included orders remain visible. The CBC/BMP trees are intact. Other lab groups
are horizontal. Very long handoffs are tested to continue without clipping.

PDF fitting uses an explicit 7.2 to 6.5 pt body-font range. It never shrinks
unboundedly to force one page. If it cannot fit, the default 7.2 pt continues
onto more pages. HTML is compact but is not guaranteed to share PDF pagination.

## Compatibility and limits

Storage remains schema 7. Models, encryption, GitHub storage and requirements
are unchanged from 6.2. The regression suite includes prior-schema migration,
round trips, editable fields, hidden medication rules and mocked save conflicts.
A separate compatibility check opens a synthetic encrypted archive generated
by the original 6.2 code with the same temporary test key and verifies exact
content equality. No user password, key or private record is used.

UI tests use a Streamlit widget stub rather than a real browser. The hosted
Streamlit deployment and authenticated private data repository were not tested.
No direct GitHub updates were made. No parsing rule is a promise that every
future Epic format will work. Unreadable rows still raise an error instead of
silently disappearing or having a guessed dose. Check output against the source.
