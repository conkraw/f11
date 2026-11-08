# Version 6.27 validation

The complete suite contains 2,229 automated checks: 2,164 inherited checks and 65 new pacemaker checks. Historical migration fixtures and expected current-schema assertions were adjusted for the added pacemaker snapshot. No inherited tests were removed. The full suite is rerun from the extracted delivery ZIP.

The new tests cover the supplied tab-separated W pattern, AAI/AAIR/AOO and VVI/VVIR/VOO mode-to-rate pairing, colon/space variants, missing modes or rates, generic-rate fallback, conflicting rates, distinct dual-chamber rates, explicit No/Off/Standby values, and the distinction between pacing rate, heart rate and output in milliamps. Missing required values remain UNK. No capture or clinical-indication inference is made.

Integration checks cover independent W updates, empty-W clearing, omission preserving prior settings, failed-W hiding without cancelling unrelated sections, patient-free error reports, manual editing, include/exclude, pending widget edits during room autosave, session migration, new-patient clearing, encrypted round trips and single/batch export. HTML is escaped, and mode/rate are verified in PDF text.

The supplied W excerpt produces Pacemaker: AAI at 140 bpm. With a synthetic full-handoff baseline, every other imported snapshot was compared against actual Version 6.26 output and remained unchanged.

A synthetic encrypted archive was generated using the actual original Version 6.26 code, then decrypted with Version 6.27 and the same key. Every prior field, setting, reset generation and saved timestamp remained unchanged. The new pacemaker field initialized to null. A second encrypted round trip passed.

The synthetic landscape PDF was rendered and visually checked. It fits on one page. The pacing line is bold under cardiovascular vitals and above lactate/CV Infusions. The numeric rate and bpm stay together on a printed line. The original auto-fit and overflow behavior remains.

The following prior runtime modules are byte-for-byte unchanged:

admin_access.py, blood_gases.py, cbc.py, create_secrets.py, cultures.py, demographics.py, devices.py, feeds.py, fen_gi.py, fluid_balance.py, github_store.py, guide_store.py, handoff_reset.py, infusions.py, lab_layout.py, labs.py, medication_groups.py, medications.py, microbiology_display.py, noninvasive.py, observations.py, output_text.py, print_time.py, recurring_orders.py, save_status.py, security.py, set_admin_password.py, user_guide.py, ventilation.py, viral.py, vitals.py.

Each packaged file is listed in SHA256SUMS.txt. The archive is checked for corruption and read back against its source files. Neither real patient source files nor deployment secrets are packaged in this update.

Limits: UI tests use Streamlit widget stubs, not the live hosted app. GitHub tests use synthetic data and mocked requests. No live deployment, authenticated private storage, or real bedside pacemaker was tested. The parser copies documented fields and cannot determine whether pacing is currently capturing or whether the pasted settings are current.
