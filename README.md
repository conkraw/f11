# PICU Handoff: SmartPhrase foundation

Version 1.0.0. A new web-hosted Streamlit project, not a patch for the prior PDF/OCR apps.

Read START_HERE.html before deployment. Start with synthetic information only.

## Included now

Password-protected app, preset and custom rooms, editable system handoffs, explicit encrypted GitHub saves, Admin diagnosis routing, printable HTML and text exports, and strict repeated-letter divider checks. Only the Diagnoses section is imported automatically. B through J are boundary-detected but are not parsed or saved as raw source. Manual handoff fields are editable.

No OCR, PDF upload, PDF password, local Windows installer, Jupyter server, external AI API, or automatic medication parsing is part of this foundation. Pasted text is already text. create_secrets.py optionally runs once on an existing local Python installation.

## Deployment overview

1. Obtain institutional approval before using clinical information. A private repo and encryption do not establish HIPAA compliance. Hosting and storage services must be assessed, with required agreements and security controls. A room number is not de-identification.
2. Create a new private code repository and upload this folder's contents, including `.streamlit/config.toml`. Do not upload generated `.streamlit/secrets.toml` or clinical samples.
3. For persistence, create a second private DATA repository initialized with a README on `main`. This avoids changing the code repository on every handoff save. Use a fine-grained token scoped only to this repository with Contents read/write and metadata access. Organization approval may be required.
4. Run `python create_secrets.py` locally, or open `Generate_Secrets.ipynb` in your existing JupyterLab. This helper only uses the Python standard library. Create the app password and supply the data repo/token. It writes a private secrets file locally and does not print its values.
5. Set the hosting entry point to `app.py`, choose Python 3.11 or newer, and copy the generated secrets into the host's private Secrets settings. Streamlit Community Cloud is a possible SYNTHETIC demo host, not a recommendation for clinical hosting. For clinical use, deploy to the environment approved by your institution.
6. Keep the encryption key in an approved password manager or secrets store. The app password can change independently. Losing the encryption key loses access to existing encrypted data.
7. Sign in, open a room, and use Load synthetic example. Read Diagnoses, review them, Apply diagnoses to handoff, review the editable sheet, and explicitly save. Reload from a new session to verify persistence.

For session-only tests, set `github_enabled = false`. No archive persists in this mode.

## Room list

P4102, P4104, P4106, P4108, P4110, P4112, P4114, P4116, 4201, 4203, 4209, 4211, 4213, 4215, 4217, 4219, 4221, 4223.

This interprets the ranges as even numbers for P4102 through P4116 and odd numbers for 4211 through 4223. Admin can edit the list. Other room allows an additional number or short room label. An optional P is normalized to the existing preset rather than creating a duplicate.

## Separator contract

One repeated-letter divider at each end. At least 8 copies of the same letter, on its own line. The opening and closing lengths may differ. Each block begins with the corresponding heading. Single or full SmartPhrase pastes work. Duplicate Diagnoses blocks are rejected to avoid mixing patients.

A Diagnoses / B Medications / C Invasive Ventilation / D Non-invasive Ventilation / E VITALS / F CULTURES / G LABS / H INTAKE/OUTPUT / I NUTRITION / J Wound Review.

The mixed `ceeeee...` closing VITALS line is invalid. Use all e characters. Malformed other sections generate warnings without corrupting a valid, complete Diagnoses block. The app does not silently repair a divider.

Numbering and bullet markers are removed from diagnoses. Medical wording, case, codes, qualifiers, and duplicate diagnoses are otherwise preserved. Wrapped numbered items are joined. No clinical inference is performed.

## Storage behavior

The only data file written by the app is `encrypted-data/handoff-v1.enc` in the configured data repository. Its JSON contents, including rooms and Admin settings, are encrypted on the app server before the GitHub request. GitHub receives ciphertext, a generic path and commit message, commit metadata, and ciphertext length. Fernet also exposes a token creation timestamp. This is not browser-side end-to-end encryption. The app host has the key and plaintext during use.

The whole current vault is saved as one file. SHA-based compare-and-swap rejects stale saves rather than silently overwriting concurrent edits. Reload keeps in-memory drafts. If the same room changed, compare the saved version, load it, and reapply edits. Git is not a clinical transactional database. This is a small, single-workspace prototype, not a multi-clinician EHR replacement.

A new-patient control starts a fresh handoff with a new random reference. Only explicit Save replaces that room's current sheet. Earlier encrypted revisions remain in Git history. There is no secure erase, retention policy enforcement, or independent audit trail in this prototype.

Only the reviewed handoff fields and Admin settings are saved. The complete pasted SmartPhrase and unimplemented sections are not put in the archive. They still reach the host and remain in session memory until cleared or the session ends. The application cannot guarantee deletion from operating-system memory, logs controlled by the host, browser state, backups, or Git history.

## Authentication and privacy boundaries

No public default password. Login is verified with salted PBKDF2-SHA256. The encryption key is separate from the login password. A server-side idle check signs out active sessions after 15 minutes without a submitted interaction, checked about every 30 seconds while connected. Typing inside an unsubmitted form does not reset that timer. Sessions have an 8-hour maximum. Disconnected browsers cannot be forcibly erased.

This app uses a shared app password, not individual institutional identities. All signed-in users can access Admin and all rooms. The per-session failed-login delay is not distributed rate limiting and can be reset by opening another session. Clinical deployment needs institution-managed access control, HTTPS, appropriate identity and audit controls, and endpoint/rate-limit protections outside this prototype. No claim of HIPAA compliance is made.

Expected errors use static messages without patient text. There is no application logging of pasted text. Do not paste production traceback contents into chat. Host infrastructure remains outside this code's control.

HTML/text downloads are plaintext. Open the HTML in a browser and use Print to print or save as PDF. A room label is not a substitute for the institution's patient-identification process. Blank or unimplemented sections do not imply normal findings or absence of treatment.

## Development / validation

`python -m pip install -r requirements-dev.txt`

`python -m pytest -q`

`streamlit run app.py`

See TEST_REPORT.md for actual validation and limitations. Dependency ranges are not a reviewed production lockfile. IT should lock and audit the resolved environment during deployment.
