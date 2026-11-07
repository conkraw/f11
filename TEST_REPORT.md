# Validation report: Version 6.13

## Executed checks

The unmodified Version 6.12 package passed 1,103 tests before changes.
The updated package passed 1,169 tests under Python 3.13, with no skipped tests,
using PYTHONPATH=. pytest -q --disable-warnings. The delivery ZIP is also extracted
into a clean folder and its full suite is run before release.

Coverage added in this release includes independent Q boundaries, wrapped and
horizontal date/time headers, exact column counts, normal versus ISTAT hemoglobin
priority, no backfilling across CBC columns, older automatic/manual count aliases,
latest ANC/ALC with independent dates, zero counts, absent-count placeholders,
explicit ISTAT fallback labels, malformed/conflicting row rejection, legacy G
fallback, empty versus omitted Q, repeated import replacement, per-room edit and
autosave state, full-page widget-key rendering, encryption round-trips, schema 12
migration, and same-column POCT gas aliases and untyped PH handling.

All three supplied Q/P patterns were separately reproduced from their provided
text outside the delivery package. Their selected standard hemoglobin, Hct,
ANC/ALC and latest-gas results matched the expected source column/date rules.
Only synthetic examples and synthetic regression fixtures are bundled.

Output-only medication tests cover neurologic infusions, ordinary medications,
custom medication wording, other-medication bands, PDF, HTML, text and print-all
composition. Stored source rows, qualifiers, dose units, mappings and encrypted
round-trips remain unchanged by rendering.

The prior schema-version fixtures were updated to model old archives without the
new cbc field and to expect schema 13 after migration. The intentional output
change is reflected in the infusion-render assertion. One old encryption test was
corrected to check a complete plaintext field rather than the three-letter string
ART, which can occur by chance in base64 ciphertext. Decryption/tamper protection
and exact encrypted round-trip checks are retained.

## Actual previous-package compatibility

A separate process loaded the original, unchanged Version 6.12 ZIP and used its
own models, importer and seal_vault function to generate a synthetic encrypted
archive. The new application opened it using the same key. Every previous room
field, manual note, medication source value, stored gas value, rule and identifier
was identical. Only schema=13 and cbc=None were added. A new encrypted round-trip
also matched. The original source archive and synthetic test key are not packaged.

## Visual and delivery checks

The synthetic two-room PDF was rendered at 150 dpi and both pages were inspected.
Each room occupies one landscape Letter page. The CBC and BMP fishbone layouts
remain visible. Collection date and time use separate small lines in timed CBC
nodes to avoid widening the tree. Latest ANC and ALC are below the first CBC,
with their own timestamps. The second preview labels ISTAT fallback and shows
missing-count placeholders. Neurologic infusion names and doses retain emphasis,
with the Dosing Weight parenthetical absent and demographic dosing weight present.

The final ZIP is checked for CRC integrity and a SHA-256 manifest of every file.
No deployment secrets, patient inputs, generated test keys, caches or bytecode are
included. security.py, github_store.py, requirements.txt, requirements-dev.txt,
create_secrets.py, Generate_Secrets.ipynb and .streamlit/config.toml are unchanged
from Version 6.12. No direct GitHub action was performed.

## Limits

Streamlit is not installed in the build environment. Interface and callback tests
use a widget stub, not a real browser. The hosted Streamlit application, actual
clinical data entry and authenticated private GitHub storage were not tested.
No claim of clinical, regulatory or end-to-end deployment validation is made.

The parser preserves explicit supplied values. It cannot recover hidden interval
results, certify specimen identity, or determine which same-time result is truly
newer. Complete header/column alignment is required. Malformed imports are rejected
without replacing the previous handoff rather than guessed or partially applied.
