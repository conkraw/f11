# Validation: Version 6.11

## Executed checks

The original Version 6.10 archive passed 927 tests before changes. The updated
code passes 996 tests under Python 3.13 using PYTHONPATH=. pytest -q
--disable-warnings. The final delivery ZIP is extracted and the full suite is
rerun before delivery. No tests are skipped in the suite.

The 927 retained tests were adjusted where the requested preset-room labels and
schema number intentionally changed. Fabricated legacy fixtures were corrected
to omit the new infusion-rule setting, as a real old archive would. Existing
clinical parsers, export and encryption regressions remain in the suite.

There are 69 new tests covering preset aliases, room-key/session migration,
no-silent-merge protection, custom-room deletion and Undo, failed storage writes,
conflicts, keeping other drafts and medication rules, preventing removed rooms
from reappearing in Print all, expired callbacks, infusion/PRN classification,
explicit display overrides, dose/rate separation, exact formulation/route/frequency
matching, future reimports with different doses, pending widget edits on room
switches, Admin editing without a handoff, HTML escaping, bold PDF font spans,
heading order, hidden rows, and long-content pagination.

A synthetic schema-10 encrypted archive was generated in a separate Python
process with the unmodified Version 6.10 code from PICU610.zip. Version 6.11 opened
it with the same generated test key. All previous sheet fields, medication rows,
IDs, timestamps and rules were preserved. The room key and embedded label changed
from 4201 to P4201, as requested. The migrated vault encrypted/decrypted unchanged
under schema 11. No real private data repository or user encryption key was used.

The new synthetic preview has one landscape Letter page at 7.2-point body text.
It was rendered and visually checked. Neuro observations are first, then two
infusions with bold names and bold-underlined explicit doses. Recorded rates are
separate. A PRN product containing the word infusion remains in Other Medications.
The room is P4201. PDF text and font tests verify the content and emphasis.
Compact infusion entries stay together across page boundaries. Oversized entries
remain splittable and continue without clipping or endless pagination.

## Limits

UI and callback tests use a widget stub, not the full Streamlit browser lifecycle.
Installing Streamlit 1.52 into an isolated test directory was attempted, but the
available package source returned no matching distribution. The real Streamlit
interface, hosted deployment, and authenticated private GitHub saves were not run.
The fake-store tests do not verify live connectivity, token permissions or hosting
behavior. No direct GitHub operations were made.

Autosave requires imported handoff data and a live session. Unsubmitted paste-form
text is not saved as an imported handoff. Deletion removes the current room record
from the active archive, not historical encrypted commits. Undo is session-only
and retains just the most recent removal. It will not overwrite a re-added room.

Automatic infusion classification is only a display rule based on explicit source
frequency and route. It is not a pump-status check. Held/future order labels are
retained. Doses, concentrations and recorded rates are not recalculated. Existing
custom wording remains authoritative. These checks do not establish clinical
validity, identity of a room occupant, institutional approval or privacy compliance.
