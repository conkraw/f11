# Version 6.1 validation

## Tests actually run

The unmodified Version 6 package passed all 377 existing tests in this environment before changes. A minimal reproduction of the supplied taper failed on medication rows 2 and 3 with the same column-separation error shown in the screenshot.

After the fix, 432 automated tests passed using `PYTHONPATH=. pytest -q --disable-warnings`. This includes the original 377 checks and 55 additional taper-related cases. No tests were skipped. See tests/test_medication_tapers.py.

New coverage includes tab-indented/standalone/bulleted Followed by connectors, a final tab-cell connector, missing trailing empty columns, blank topical doses, wrapped medication names, Windows/Mac/Unix line endings, explicitly tabular bulletless orders, preserved start dates and order sequence, date-independent drug mapping, unchanged unknown annotations, exact dated hide/restore rules, broad Admin visibility rules, malformed/orphan connector rejection, unchanged prior drafts on errors, repeated imports, encryption round trips without a schema change, inline mapping callbacks, synthetic-example loading, PDF/HTML/text date and frequency retention, and multi-room printing.

A separate local-only reproduction checked both supplied medication lists with provider and Last Admin values replaced by sentinels. The first retained all 12 orders, including the three distinct dexamethasone steps and their dates/frequencies. The second retained all 36 orders, including blank topical doses, enteral routes, elemental doses and continuous/PRN infusions. Names, doses, routes, frequencies and Last Rate values matched their source columns. C/D patterns were checked in the same import: blank respiratory blocks in the first and documented invasive ventilation in the second. These source-pattern reproductions are not bundled clinical records.

The synthetic taper preview was generated from the same application export functions used by the app. Its landscape PDF was rendered and inspected. Start-date/sequence labels and medication frequencies were checked in PDF text as well as HTML/text exports.

## Storage compatibility

This fix retains schema 6 and does not alter security.py, github_store.py, models.py, the encrypted data filename, dependency requirements, or secrets configuration. A newly saved taper handoff opens with the same existing encryption mechanism. The previous migration, encryption/tamper and mocked GitHub conflict tests remain in the passing suite. No real handoff archive or account secret was read.

## Limits

Streamlit is not installed in this build environment. UI and callback checks use the existing test stubs, not a complete live Streamlit browser lifecycle. No deployment, real login, live GitHub save or private data-repository connection was tested. No GitHub repository was changed.

The fix addresses the documented clipboard patterns, not every possible future Epic format. Unknown/malformed medication structure still fails without applying a partial import. The app displays source scheduling labels rather than determining current treatment, doses or taper timing. Test the supplied synthetic example after deployment, then compare any clinical handoff against its source.
