# Validation report: Version 6.19

## Executed checks

The original unmodified Version 6.18 package passed all 1,621 tests before edits.
The updated package passed 1,679 tests, adding 58 save-status checks.
No existing test was modified, skipped or disabled.

Command: PYTHONPATH=. python -m pytest -q --disable-warnings

The delivery ZIP is checked with ZipFile.testzip and a SHA-256 file manifest.
It is extracted into a separate directory, and the full suite is rerun there.

## Added coverage

Tests cover Eastern dates, seconds, AM/PM, EST/EDT, the repeated fall hour,
spring transition and cross-year conversion. Missing, invalid and naive times
never default to the present time. Display data and stored records are immutable.

Manual saves, save-all and custom-room autosaves update displayed save times only
after storage acknowledgement. Failed writes and conflicts keep previous times.
An unchanged room switch does not claim a new save. Save-all leaves unopened
rooms' timestamps untouched. New handoff IDs do not borrow prior occupant saves.
Imports, edits, Admin-only saves and downloads do not advance room-save times.
Loaded-archive conflicts, newly loaded saves and session-only mode are covered.

Widget-stub tests verify the timestamp just below the room heading, all-room
status listing, selected-room status table before download buttons, custom rooms,
unsaved warnings, no hidden storage writes during rendering and session-only labels.
HTML escaping is checked, without a DataFrame/PyArrow dependency.

A synthetic archive generated using the original Version 6.18 source was opened
with the updated source and the same key. Every stored field and setting remained
identical. Existing preset and custom room timestamps displayed correctly.

## Scope and limitations

Runtime changes: app.py, new save_status.py and the error_store.py version stamp.
models.py, schema 17, github_store.py, clinical parsers, display routing, exports.py,
print_time.py and dependency requirements are byte-for-byte unchanged from 6.18.

The example HTML is illustrative and uses synthetic room-save metadata. It is not
a screenshot of a live Streamlit deployment. UI tests use a widget stub and GitHub
calls are mocked. Streamlit was not installed in this build environment and the
available package source did not provide it, so a full live Streamlit browser test
could not be run. No authenticated private archive or production Secrets were used.

Save times are the successful writes/loaded archive known to the current session,
not real-time cross-session monitoring. No clinical behavior or printed layout was
changed. These software checks do not establish clinical or institutional approval.
