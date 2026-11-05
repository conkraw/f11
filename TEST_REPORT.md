# Validation report

76 automated tests passed in the build environment using Python 3.13.5.

Command: `PYTHONPATH=. python -m pytest -q`

Validated:
- Variable-length, case-insensitive paired dividers and the ten-section synthetic example.
- Empty, missing, duplicate, malformed, wrong-heading, and mixed-letter divider handling.
- Diagnosis text preservation, numbered-line wrapping, code/qualifier retention, and no cross-section import.
- Password hashing/verification and invalid-hash handling.
- Encryption round trip, wrong-key refusal, ciphertext tamper refusal, and schema validation.
- Fixed room list, custom labels, normalized aliases, independent room drafts, and new-patient references.
- Private GitHub checks, branch checks, encrypted-only payloads, generic metadata, stale-save refusal, and safe network/error handling using mocked HTTP responses.
- HTML escaping and preservation of text in plain-text export.
- Import/edit/save callbacks, replacement confirmation, review gating, session cleanup, stale-room protection, and refusal of expired-session save callbacks using a minimal Streamlit stub.
- Source compilation with `python -m compileall -q .`.

Callback tests do not instantiate real Streamlit widgets. No clinical data was submitted to GitHub or another service. The supplied examples are synthetic.

Not validated here:
- An actual Streamlit browser session or Streamlit AppTest execution.
- A live GitHub token, repository, institution network, or hosting environment.
- End-to-end login, WebSocket idle refresh, widget lifecycle behavior, deployment package resolution, or browser printing on the user's computer.
- Visual browser rendering of the HTML guide or handoff. HTML structure and escaping were checked, but the available Playwright installation had no browser executable.
- Clinical accuracy, patient identity, institutional policy compliance, or HIPAA compliance.

The build environment could not install Streamlit because network name resolution was unavailable. Core modules were tested with cryptography 46.0.4 and requests 2.32.5. Dependency ranges must be reviewed, resolved and tested on the intended host.

Before clinical use: complete institutional review, deploy with synthetic data, verify the complete login/import/edit/save/reload/new-patient/export workflow, and verify required audit, identity, retention, and recovery controls. The shared app password and encrypted GitHub archive do not replace these controls.
