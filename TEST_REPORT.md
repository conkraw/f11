# Validation report: version 3

## Executed checks

199 automated tests passed in the build environment using Python 3.13. Tests were run with PYTHONPATH=. pytest -q --disable-warnings. No tests were skipped in that run.

Coverage includes divider parsing, diagnosis import, tab-separated medication parsing, dose/rate preservation, provider omission, unmapped medication behavior, immediate mapping persistence, rollback after failed mapping writes, Admin editing with no handoff open, exact ventilation field order, exclusion of CPAP/BiLevel labels, missing and conflicting settings, preservation of manual notes, repeated imports, room switching, schema 1/2 migration, encryption and tamper rejection, expected-SHA GitHub conflicts with mocked responses, save-all atomicity, multi-room printing, long-content pagination and HTML escaping.

Callback and page-render tests use a minimal Streamlit stub. They exercise application functions, widget keys, render branches and generated downloads. They do not implement the complete Streamlit widget or browser lifecycle.

The two-room synthetic PDF packet was rendered at 140 dpi and both pages were visually inspected. It has two landscape Letter pages. The first includes the requested ventilation fields before the separator and respiratory medications. The second uses an excluded mode and has no automatic ventilation block. Long-content tests verify continuation pages without dropped or duplicated sentinel text.

## Not tested here

A live Streamlit browser session and an authenticated live GitHub repository connection were not available. Installing Streamlit was attempted, but the build environment could not resolve the package host. No claim of end-to-end live deployment testing is made.

These tests do not establish clinical validity, completeness of an Epic source record, identity of a room occupant, or privacy/regulatory compliance. Mode-name matching is only a display rule. External hosting, backups, platform logs, operating-system behavior and browser behavior were not audited.

## First deployment check

Keep existing Secrets and encryption key. Upload the complete code update, reboot the app, sign in and select a room. Load synthetic example and click Create / update handoff. Choose a medication system, open Admin and confirm the rule is present. With GitHub enabled, sign out and sign in again to test rule persistence. Create another room and use Print all to test the combined PDF. Save handoffs explicitly to test durable content storage.
