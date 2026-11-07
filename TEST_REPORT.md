# Version 6.15 validation report

## Executed

- The unmodified Version 6.14 package passed its 1,286-test baseline in this build environment.
- The updated suite passed 1,363 tests using Python 3.13. This includes 77 new FEN/GI tests. Existing migration test fixtures were updated only to omit newly introduced fields when constructing a historical schema and to expect schema 15 after migration.
- Coverage: S totals, missing/zero/negative values, exact unit/precision preservation, no Net calculation, conflicting totals, S-only and omitted/empty updates, H not counted twice, requested generic-name grouping, held and dated orders, topical glycerin exclusion, hidden/excluded rows, distinct schedules, exact-formulation overrides, escaping, rollback on failed saves, editing and pending-widget room autosave, existing rule preservation, encrypted round trips, session-only operation, PDF/HTML/text/batch export and one-page synthetic output.
- Independently executed original Version 6.14 code to generate an encrypted synthetic archive. Version 6.15 opened it with the same key and preserved every old setting and every old saved field. New defaults are an empty GI-display-override list and null intake/output snapshots.
- Privately checked the supplied complete SmartPhrase: all 24 medication rows imported, recorded S totals preserved, two separate sennosides orders retained. Previous parsed fields matched Version 6.14 after excluding generated IDs/timestamps. The supplied source file is not included in the ZIP.
- CBC, blood-gas, laboratory, lab-tree, respiratory, recurring-order, culture, security, GitHub-storage and dependency files were byte-compared against the original baseline. Their parsers/logic are unchanged.
- Rendered the synthetic landscape PDF at 160 dpi and visually inspected its one-page output. FEN/GI totals precede bold GI prophylaxis and Bowel Regimen headings without overlap or clipping.

## Not established

The automated interface checks use a Streamlit widget stub. They do not exercise a live browser lifecycle. Streamlit is not installed in this build environment. No hosted application or authenticated private handoff repository was accessed or tested. No direct GitHub changes were made. Tests do not establish clinical accuracy, source currency or institutional privacy compliance.

## Reproduce

Install requirements-dev.txt in an isolated test environment and run:

    python -m pytest -q --disable-warnings

Begin deployment testing with examples/synthetic_fen_gi.txt before using clinical records. Preserve the original encryption key.
