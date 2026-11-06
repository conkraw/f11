# Version 6.5 validation

## Executed checks

The original Version 6.4 ZIP passed all 588 inherited tests before editing. The updated suite passes 653 tests, including 65 new test cases in tests/test_cultures_ads.py. Run with PYTHONPATH=. pytest -q --disable-warnings.

Inherited migration fixtures were updated to omit the new cultures field when constructing historical schemas, and current-schema assertions now expect 8. A previously unsupported culture placeholder was replaced with a valid synthetic No results found section. The test for discarding an unsupported raw block now uses H, which remains unsupported. Production validation of unknown fields was not weakened.

The medication regression reproduces a final ADS row losing empty TAB cells at a block boundary. Tests cover retained tabs, tabs already removed by the clipboard, duplicate rows with unique IDs, blank fields, separate active orders, exact hide/restore rules, and rejection of nonempty ambiguous fragments. The 12-row supplied medication pattern also passed a separate local verification, retaining eight ADS source entries without inferred doses.

Culture tests cover the first three table columns only, multi-organism continuation rows, sensitivity-column omission, category selection, two newest groups per category, exact duplicate/status consolidation for display, raw-row retention, date and time sorting, same-date ties, unspecified aspirates, older pericardial results, missing/malformed fields, atomic imports, empty and omitted F sections, manual edits, hide/restore through inclusion controls, cross-room protection, HTML escaping, compact PDF/text/HTML and batch output, encryption and migration.

Separate checks using the supplied culture patterns retained all three organisms beneath a tracheal specimen. The long pattern retained all 46 dated source rows, selecting the newest two blood groups and newest two explicit respiratory groups. The other-site pattern retained 31 dated rows with the pericardial Candida result still visible. The repeated-negative pattern retained all three source rows and produced two display groups. These raw supplied records are not bundled in the delivery ZIP.

## Cross-version archive check

A separate process running the unmodified Version 6.4 code created a synthetic encrypted schema-7 archive with labs, vitals, respiratory settings, neuro observations, nutrition, notes, medication mappings and hiding rules. Version 6.5 opened the original ciphertext with the same key. Every prior saved field and setting was compared for equality. Only the schema number and new empty cultures snapshot changed. The migrated archive also passed an encrypted round trip.

## Print check

The new synthetic two-room packet was rendered at 160 dpi. Both pages were visually inspected. Each room fits on one landscape Letter page at the existing 7.2 pt body size. Temperature is above the six-dash separator and culture list. Every organism in the three-organism tracheal result is visible. An older pericardial result is present independently of recent blood results. No clipping or overlap was found. A long arbitrary handoff may still need continuation pages.

## Limits

Streamlit is not installed in this build environment, and an attempted installation could not obtain a compatible distribution from the available package source. UI tests use widget stubs rather than a real hosted browser. No live private handoff repository or deployment Secrets were accessed. No direct GitHub changes were made.

The grouping is a display convention, not an assertion of specimen identity or final culture status. The source lacks accession numbers and often collection times. Same-date/site rows can represent multiple real samples. All retained raw rows remain available in Cultures. Older values and sensitivity data should still be reviewed in the source clinical record as needed.
