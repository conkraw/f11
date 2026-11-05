# PICU Handoff SmartPhrase

Version 5 adds standard nasal cannula and pressure-pair recovery when Vent Mode is absent, alongside non-invasive respiratory support combinations to the existing medication routing, invasive ventilation and landscape print-all workflow. Read NONINVASIVE_UPDATE.md for the exact rules and validation limits.

## Working web app

Keep app.py as the entry point and retain the existing deployment Secrets, app password hash, encryption key, token and private data repository. No new dependencies are required. Do not run create_secrets.py again for an existing installation.

The encrypted archive stays at encrypted-data/handoff-v1.enc. Schemas 1-4 migrate in memory to schema 5 without discarding notes, medication records, mappings or invasive settings. The next successful save uses schema 5 with the same key. Do not downgrade only part of the app after saving new data.

## Daily workflow

Sign in, choose a room, paste the separated SmartPhrase and click Create / update handoff. A imports diagnoses. B imports medication orders. C and D together import respiratory support. Other sections remain manual. Pasted Epic text is read directly without OCR or an external AI service.

The import goes directly into the editable draft without review or replacement checkboxes. Malformed or conflicting input stops the import rather than partially replacing a handoff. Paste one room at a time. Only the included sections change, with C/D treated as one respiratory snapshot. Separate system notes are preserved.

Choose a destination beside a medication to remember the rule immediately in Admin and encrypted GitHub. Admin can edit rules without an open handoff. A failed mapping save is shown as an error and rolled back. Unmapped orders remain in Other Medications. Changing rules updates open drafts but does not silently rewrite stored handoff text. Save handoff or Save all open handoffs persists the draft contents.

## Medications

Every bullet starts a separate order. Medication/formulation, Dose, Route, Frequency and applicable Last Rate are read from the tab-separated columns. Provider and Last Admin are not retained in the parsed record. The original paste is not archived.

The formulation and actual Dose column stay distinct when they differ. A dose already present at the end of the name is not printed twice. There is no dose calculation, unit conversion or reuse of another patient's dose. Continuous infusions can show a weight-based dose and recorded pump rate. With a blank Dose, a continuous Last Rate is shown as @ rate. Rate timestamps remain available in the editor. A zero rate is not interpreted as a discontinued order.

Scheduled and PRN orders remain separate. Missing columns or unreadable rows block the medication import. Reimporting replaces the imported medication list without erasing separate system notes. Custom wording overrides the generated wording and must be updated separately when needed.

Rules use case-insensitive complete-name or word-boundary prefix matching, not fuzzy drug-name guesses. The longest prefix wins, while an exact rule has priority. A specific heparin flush rule can differ from a heparin rule. Rules move the complete order with its own dose and instructions.

## Respiratory support

Invasive modes retain the requested C-block settings, in order: mode, set rate, set tidal volume, PEEP, mean airway pressure, inspiratory time, observed PIP, pressure support, flow trigger and FiO2. Billing, heater and equipment fields are excluded. Missing invasive values are not substituted from other fields or blocks.

A named BiLevel/BiPAP mode in C requires both D-block IPAP and EPAP. When Vent Mode is absent, the same documented pair is retained as BiPAP (pressure-based), not as a verified current mode. Missing Vent Mode no longer blocks the whole import. An explicit unknown or invasive mode, an invasive airway label, or Ventilator On: No prevents the missing-mode fallback. A mode label left behind without those pressures is not reported as BiPAP. CPAP requires a CPAP mode and EPAP or PEEP. Explicit HFNC or standard nasal cannula can be reported alone or alongside either pressure device. Nasal cannula, including the humidified Other (Comment) label, is not relabeled as HFNC based on flow. The recorded FiO2 is preserved, including 21%, without calling the device room air.

For the requested CPAP/Bi-PAP mask plus positive-flow pattern, the app also adds HFNC, explicitly labeled flow-based. That inference is not proof that HFNC is in use. The entry can be removed in the editor when the flow belongs only to the mask. Read NONINVASIVE_UPDATE.md for details on FiO2 sources, conflicting pressure fields and stale settings.

Paste C and D together. Pasting either is a new respiratory snapshot from that paste only. Old automatic entries are removed rather than reusing earlier pressures. A/B-only pastes leave respiratory support unchanged. Automatic support prints first in RESP, followed by ----- and the separate notes and medications. Each device is editable and removable without confirmation dialogs.

## Landscape printing

The Letter-landscape sheet retains PATIENT, NEURO, RESP, CARDIAC, FEN / GI, HEME, ID and LABS columns. Other Medications spans the width below. Lower bands include lab trends, goals/follow-up, airway, last intubation, access and drains/tubes. No patient-name or MRN field is supplied. Long content continues on additional pages rather than being cut off.

Print all combines saved rooms and latest open drafts. Each room appears once on a new landscape page. Blank sheets are omitted. Downloads are available as PDF or printable HTML. Printing does not save changes to GitHub. Save all open handoffs stores the drafts. Downloaded exports are unencrypted.

Use Start blank for new patient when a room changes occupants. A room number does not replace your clinical patient-identification process.

## Storage and deployment

The password gate, private-data-repository check, Fernet encryption, fixed archive filename, generic commit message and expected-SHA conflict protection remain. Only application code and synthetic examples belong in a public code repository. Keep .streamlit/secrets.toml, credentials and clinical records out of it.

The application host receives pasted text before encryption. Shared-password access and encrypted GitHub storage alone do not establish clinical approval or privacy compliance. Use synthetic examples until the institution approves hosting, storage, identity/access controls, required agreements, retention and auditing. Earlier encrypted saves remain in Git history. Replacing a room's sheet is not a secure purge of that history.

Raw source text is not intentionally written to the encrypted archive or diagnostic files. Clearing it from session state is not secure erasure of server/browser memory. This app cannot control hosting logs, backups, browser artifacts or operating-system behavior.

For a new deployment only, create_secrets.py or Generate_Secrets.ipynb creates the app password hash and independent encryption key. Use the example configuration to configure a separate private data repository and a token limited to Contents read/write access there. Add credentials in the host's private Secrets settings, never in code. Keep a secure backup of the encryption key. Losing it prevents recovery of encrypted data.

## Validation

Run PYTHONPATH=. pytest -q after installing requirements-dev.txt. The current local run passed 313 tests. The suite uses synthetic records, mocked GitHub responses and widget stubs. It does not prove live browser compatibility, source-record accuracy, simultaneous device use or privacy compliance. The two-page synthetic nasal-cannula regression export was rendered and visually checked. Deployment and the live private data-repository connection were not tested.
