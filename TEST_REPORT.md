# Version 6.9 validation

## Executed checks

The original PICU68.zip passed all 841 tests before editing. The updated suite
passes 863 tests with `python -m pytest -q --disable-warnings`. No tests were
skipped. The 22 new cases are in tests/test_lab_routing_placement.py.

New coverage includes coagulation immediately after Hepatic in the laboratory
band, coagulation without a hepatic result, inflammatory aliases routed to ID,
source-specific dates and flags, latest-value selection, exclusion/restoration,
Anti-Xa (HEPLMW) display, no duplicated automatic results, shared editor preview,
PDF/HTML/text exports, multi-room Print all, unchanged stored snapshots, encrypted
round trips, and PDF coordinates for horizontal coags below the hepatic line.

Existing tests are retained. Assertions in test_compact_pn.py and
 test_demographics_expanded_labs.py were updated only for the requested new
placement. The existing tests for parsing, preservation, migration, encryption,
field conflicts and save protection remain active.

## Runtime and storage scope

Runtime changes are limited to labs.py, lab_layout.py and version/help wording
in app.py. The shared lab-card selector now keeps coagulation in the laboratory
band. The ID formatter retains inflammatory markers but not coags. HEPLMW is
still displayed as Anti-Xa (HEPLMW), now in the coagulation line. No units or
clinical interpretations are added.

Storage schema remains 10. models.py, security.py, github_store.py, all source
parsers other than the display helpers in labs.py, configuration and dependency
files are unchanged. No saved handoff content, credentials, medication mapping
or repository was altered. Existing structured lab snapshots get the new
placement when exported, without requiring a reimport. Manual notes are not
rewritten.

## Print and package verification

The synthetic demographics/labs example was exported using the actual application
export functions. The resulting preview has one landscape Letter page, using
7.2-point main text. The page was rendered with pdftoppm and visually inspected.
It shows Hepatic, Coagulation and Arterial gas in that order in the lower lab
band, and CRP/PROCAL under temperature in ID, with no clipped content.

The full application ZIP is checked for archive integrity, required files and
exact member bytes. SHA256SUMS.txt is regenerated from the delivered files.
The full 863-test suite is rerun from a fresh extraction of the delivery ZIP.
No generated credentials, interpreter caches or patient source files are added.
Old bundled previews are retained as historical references. The current preview
is examples/lab_placement_preview.pdf.

## Limits

Callback and screen-render tests use a Streamlit widget stub. The live hosted
Streamlit browser and authenticated private handoff repository were not tested.
No regulatory, clinical-validity or universal formatting guarantee is made.
