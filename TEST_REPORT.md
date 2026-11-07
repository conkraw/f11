# Validation report: Version 6.18

## Executed checks

The original, unmodified Version 6.17 package passed all 1,578 tests before the
change. The updated package passed 1,621 tests, adding 43 theophylline checks.
No existing test was modified, skipped or disabled.

Command: python -m pytest -q --disable-warnings

The final archive is also extracted into a separate directory and the complete
suite is rerun from those extracted files before delivery. The archive contains
a SHA-256 manifest and is checked with ZipFile.testzip.

## Added coverage

THEOPH exact-code/case matching and explicit Theophylline aliases are tested.
Tests reject guesses involving free-theophylline or unrelated drug names.
Latest date, latest time, same-day source-order ties, raw units and abnormal
flags, inclusion/exclusion, no-value cases, and source immutability are checked.

Tests exercise G-only replacement, omitted-G preservation, invalid-G recovery,
already-stored Other labs rows, unchanged schema-17 encrypted round trips,
existing editing callbacks, full-page widget-stub rendering, single occurrence
in all export types, room-specific Print all output, HTML escaping and PDF
coordinates placing the level below support and above respiratory medications.

The one-page synthetic PDF is rendered and inspected. It contains no patient
source paste. The new module-level function is labs.theophylline_text.

## Preserved functionality and limitations

The CBC and gas parsers, lab-tree drawing code, medication parsers and grouping,
respiratory-support parsing, order parsing, storage format, dependencies and
production configuration are unchanged. New runtime changes are limited to
labs.py, models.py, app.py and error_store.py (version stamp only).

The browser tests use a Streamlit stub, not a hosted browser session. GitHub
storage tests use mocked responses. The live app and authenticated private data
repository were not accessed. These software tests do not establish clinical
validity or institutional approval.
