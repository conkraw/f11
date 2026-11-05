# Version 6 validation

## Executed

377 automated tests passed in this build, using Python 3.13 and the installed ReportLab library. The run was `PYTHONPATH=. pytest -q --disable-warnings`. No tests were skipped in that run.

The existing respiratory, medication, encryption, migration, parser and print tests were retained. Historical schema fixtures were updated to construct genuine old structures without new fields. An old test that verified unimplemented lab text was not saved now uses the still-unimplemented culture block instead.

New coverage includes per-component latest/preceding results, date sorting, same-date source-order preservation, optional times, missing/invalid dates, flag/unit preservation, no invented glucose, separate arterial and venous gases, lactate routing, unknown analyte retention, blank G replacement, independent E/G updates, all-or-nothing malformed imports, K/L/M boundaries, vital routing/priority, ADS Override Pull retention, exact-formulation hide/restore, future import persistence, failed visibility-write rollback, no-handoff Admin restore, editing callbacks, schema 5 migration, encrypted round trips, HTML escaping, lab-only rooms, multi-room PDF printing and long-result pagination.

A separate integration check generated a synthetic encrypted archive using the unmodified Version 5 package. Version 6 opened it with the same key and preserved manual notes, medication mappings, BiPAP and nasal cannula entries, then saved/reopened schema 6 successfully. The supplied same-date hemoglobin/potassium and mixed-date preceding-result pattern was checked separately without including the complete source clinical record in the package.

The two-page synthetic PDF was rendered to PNG and visually inspected. CBC/BMP values, component dates, abnormal flags, graph labels, branch panels, vital-sign order, hidden-medication exclusion and page continuation were checked. PDF tests also verify landscape Letter dimensions, retention of long sentinel text and text within page bounds.

## Not executed

The complete real Streamlit browser lifecycle, deployment startup, live app sign-in and authenticated private GitHub storage were not tested. Streamlit installation was attempted but failed because the build environment could not resolve the package host. UI tests therefore use widget stubs and callbacks, not a real browser. GitHub write tests use simulated responses, not a live repository. No GitHub repository was modified for this task.

These checks do not establish completeness or clinical correctness of Epic source records, device status, specimen pairing, reference intervals, de-identification or institutional approval. The application formats documented information rather than making treatment decisions.
