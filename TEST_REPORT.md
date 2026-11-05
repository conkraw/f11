# Validation report: version 3

## Executed checks

The 199-test suite passed again before this repository update, with no tests skipped. Command: PYTHONPATH=. python -m pytest -q --disable-warnings.

All runtime source files and tests uploaded in this update were compared by their Git blob hashes with the locally tested release. The starting main commit was 0d099a8ce99ac94d25eee1e6c45bd50586637d8a. Unrelated repository files were preserved.

Coverage includes divider parsing, diagnosis import, tab-separated medication parsing, dose/rate preservation, provider omission, unmapped medication behavior, immediate mapping persistence, rollback after failed mapping writes, Admin editing with no handoff open, exact ventilation field order, exclusion of CPAP/BiLevel labels, missing and conflicting settings, preservation of manual notes, repeated imports, room switching, schema 1/2 migration, encryption and tamper rejection, expected-SHA GitHub conflicts with mocked responses, save-all atomicity, multi-room printing, long-content pagination and HTML escaping.

Callback and page-render tests use a minimal Streamlit stub. They exercise application functions, widget keys, render branches and generated downloads. They do not implement the complete Streamlit widget or browser lifecycle.

PDF tests verify landscape Letter dimensions, separate pages for different rooms, ventilation before the respiratory medication entries, and continuation pages without dropped or duplicated sentinel text. The bundled two-room PDF and HTML are synthetic examples.

## Not tested here

The actual hosted Streamlit application, a real browser session, and the application's authenticated connection to its private handoff-data repository were not tested. The GitHub connector was used only to inspect and update the public application-code repository. Deployment secrets and saved handoff data were not accessed.

These tests do not establish clinical validity, completeness of an Epic source record, identity of a room occupant, or privacy/regulatory compliance. Mode-name matching is only a display rule. External hosting, backups, platform logs, operating-system behavior and browser behavior were not audited.

## First deployment check

Keep existing Secrets and encryption key. Sign in, select a room, load the synthetic example and click Create / update handoff. Choose a medication system, open Admin and confirm the rule is present. With GitHub enabled, sign out and sign in again to test rule persistence. Create another room and use Print all to test the combined PDF. Save handoffs explicitly to test durable content storage.
