# Validation: Version 6.12

## Executed checks

The unmodified Version 6.11 ZIP passed all 996 tests before changes. Version 6.12
passes 1,103 tests on Python 3.13 with python -m pytest -q --disable-warnings.
No tests are skipped. This includes 107 new P-block gas tests. The delivery ZIP
is also extracted into a new directory and the entire suite is rerun there.

Existing regression fixtures were adjusted for schema 12 and the requested change
from separate arterial/venous gas summaries to one latest specimen. Legacy
fixtures explicitly omit the new blood_gas field, matching real older archives.
The test suite still checks the other parsers, medication taper/ADS/PN handling,
room autosave/removal, infusion emphasis, hidden medications, lab layouts, culture
and viral summaries, export pagination, storage conflicts and encryption.

New checks cover wrapped and horizontal date/time headers, ART/VEN/CAP aliases,
chronological selection across specimen types, unsorted columns, source flags,
blank and hidden cells, partial latest gases, no cross-time/specimen backfilling,
explicit-time and date-only ties, empty P clearing, omitted P preservation,
P precedence over legacy G, malformed-input rollback, old gas fallback labels,
PDF/HTML/text exports, Print all room separation, editing, pending gas edits at
room switch, schema-11 migration, nonempty infusion-rule preservation, and
ciphertext round trips. UI tests use a small Streamlit widget stub.

The user-supplied P-table pattern was tested separately outside the deliverable.
It selects ART at 11/06/26 08:04 with pH 7.48*, PCO2 42, PO2 61* and base excess
7*. The older VEN values and unspecified corrected/ISTAT rows are not printed.
The source snapshot itself is not included as a clinical example in this ZIP.

## Original-version migration

An encrypted synthetic schema-11 archive was generated in a separate process
using the unchanged code extracted from the original PICU611.zip. The new code
opened it using the same generated test key. All prior sheet fields, identifiers,
notes, medication records and settings were unchanged. Only schema=12 and
blood_gas=None were added. A second encrypted round trip preserved the migrated
archive. No user encryption key or real handoff-store record was accessed.

## Printed layout

The synthetic preview has one landscape Letter page at 7.2-point body text.
It was rendered with Poppler and visually inspected. The single ART gas line
appears in Lab Results / Trends below the hepatic/coagulation summaries. CBC/BMP
trees, demographic fields, neurologic observations and infusion emphasis remain.
Tests additionally verify three specimen labels, a one-gas-per-room rule, single
and multi-room PDFs, HTML escaping, and preserving all eligible source values.

## Limitations

Streamlit is not installed in this build environment. The complete running
Streamlit/browser lifecycle, hosted deployment and authenticated private storage
connection were not tested. Callback and widget-stub tests are not browser tests.
No direct GitHub operations were performed.

Missing or equal collection times cannot establish a true chronological winner.
The source-order fallback is qualified in the printed gas title and editor.
Legacy G rows lack matrix-column identity and therefore retain a same-draw
unverified label. A P snapshot is authoritative even when empty. An omitted P
preserves the last imported snapshot, so include P when updating gas results.

Tests do not establish clinical accuracy of the Epic source, privacy compliance,
current patient identity or actual support status. The host processes pasted
content before encryption. Exported files are not encrypted. No new dependencies
or credential/storage-path changes are part of this update.
