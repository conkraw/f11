# Validation report: Version 6.22

## Executed automated checks

The unmodified supplied Version 6.21 ZIP passed 1,777 tests before editing.
The update passes 1,843 tests, including 66 new tests. No tests were skipped.
The same suite is rerun from a separate extraction of the final delivery ZIP.
Command: PYTHONPATH=. python -m pytest -q --disable-warnings

The existing callback-test fixture now models an already unlocked administrator
rather than only a signed-in app user. Existing clinical, print and storage
assertions remain. The new security tests explicitly remove/revoke grants and
exercise refusal paths. The UI stub supports the new code-text display and a
cached guide for render tests not concerned with storage.

## New coverage

Missing/invalid Admin hashes, wrong passwords, separate credentials, identical
underlying app/Admin passwords with different salts, per-session cooldown,
plaintext widget clearing, absolute and idle expiry, logout, changed credentials,
leaving Admin, and direct callback denial are tested. Daily Handoff, save and
read-only guide access remain available without an Admin grant.

Guide validation checks field sizes, control characters, timestamps and source
whitespace preservation. HTML escapes all published fields. Storage tests use
mocked HTTP responses to check encrypted round trips, private storage checks,
fixed filenames, generic commit text, stale-save conflicts, tampering, wrong
keys and malformed responses. Guide saves are verified not to change rooms,
mappings, saved timestamps or the clinical archive SHA. Failed saves retain the
editor draft. Refreshing a read-only guide cannot silently rebase an unsaved
Admin edit. Returning after widget cleanup rehydrates the saved guide fields.
The Admin-password helper writes no files and prints no plaintext password.

Only app.py and the error-report version label changed among existing production
Python files. The clinical parsers, models.py, encryption routines, printed
handoff layout, medication groups, and save_status.py are byte-identical to the
supplied Version 6.21 files. Schema 17 and the clinical archive path are unchanged.

The standalone HTML user guide was opened and inspected in local Chromium. This
checks the static guide, not the complete Streamlit application.

## Limits

Streamlit is not installed in this build environment. Installing it was attempted
but package-host name resolution failed. Callback and UI tests use Streamlit
stubs, not a live Streamlit browser lifecycle. A live hosted app, authenticated
private GitHub writes, real Epic SmartLinks, and real clipboard operation inside
Epic were not tested. The published source starts blank because no actual Epic
SmartPhrase name or source definition was supplied.

The secondary password is a shared Admin gate, not individual accounts, MFA, or
institutional approval. Normal Handoff mapping/hiding/custom-room actions retain
their existing permissions. No deployment Secrets or private patient archive
was accessed or modified during this build.
