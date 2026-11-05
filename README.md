# PICU Handoff SmartPhrase: medications and landscape layout

Version 2 updates the working web-based SmartPhrase foundation. It is not one of the older local PDF/OCR apps.

## Update your existing deployment

Save any open work first. Keep your existing deployment Secrets, especially the encryption key, password hash, GitHub token, and private data repository. Do not run the secrets generator again for this update.

Upload the contents of this folder to the existing application code repository. Replace matching application files and add medications.py. Include the updated requirements.txt, which adds ReportLab for PDF export. Keep app.py as the entry point. Restart/reboot the app after the host installs the requirements.

Do not upload clinical source text, downloaded clinical handoffs, or .streamlit/secrets.toml. The included examples are synthetic.

The encrypted archive path stays encrypted-data/handoff-v1.enc. The application reads the previous diagnosis-only schema and upgrades it in memory without discarding existing fields. The next explicit handoff/Admin save writes schema 2 with the same encryption key. Do not downgrade only part of the app after saving schema 2. The older version will not understand the new archive schema.

## Daily workflow

1. Sign in with your existing app password and open a room.
2. Paste the complete separated SmartPhrase, or only the A and/or B blocks. Copy directly from Epic so the medication table keeps its tab-separated columns.
3. Click Read Diagnoses + Medications. Review and apply diagnoses in Paste / import. Open Medications to review and apply the medication list.
4. In Admin, select a detected medication or type a name prefix. Choose its default system and save the mapping. By default, the saved rules are reapplied to the current room's draft and import preview. This resets any per-order destination overrides in that room, but does not save its clinical handoff.
5. Review the landscape preview. Save the handoff explicitly to the encrypted GitHub archive. Download the PDF, HTML, or text only to an approved location.

Unmapped medications always go to Other Medications. No default medication-to-system mappings are supplied. Examples of rules you may choose are acetaminophen to Neurologic and sodium acetate to FEN / GI.

## Medication behavior

Each bullet starts an order. The parser reads Medication, Dose, Route, Frequency, and Last Rate from their original columns. Provider and Last Admin are discarded from the parsed records. The original pasted text can remain in session memory until both imports are applied, Clear pasted text is clicked, or the session ends.

The name/formulation is preserved. A dose already printed at the end of the medication name is not printed twice. If the formulation amount differs from the ordered Dose column, the ordered dose is shown explicitly as Dose: instead of being inferred from the product label. Units, weight-based qualifiers, route, and frequency are not clinically converted or calculated.

Continuous infusions can show both an ordered weight-based dose and a different recorded pump rate. If Dose is blank, a valid continuous Last Rate is shown as @ rate. Its timestamp is retained in the order editor rather than repeated in the compact handoff. Verify that it is current. A recorded zero rate is not interpreted as a discontinued order. Last Rate on an intermittent medication does not replace its Dose.

Scheduled and PRN orders remain separate, even with the same drug name and dose. Identical source rows are not silently merged. Reimporting replaces the previous imported medication list only after confirmation. System notes are kept separately and are never erased by a medication reimport or remapping.

Orders can be excluded, corrected, reassigned for one patient, or given custom handoff wording in the Medications tab. Excluded entries are kept in the draft but omitted from exports. Custom wording overrides generated wording, so review it again after changing a dose or rate.

Missing internal column separators, missing required columns, or an unreadable row block the whole medication import. The app does not apply a partial list while silently dropping unreadable orders. Copy the table again with tabs, or add verified clinical text manually to the appropriate system notes. Never infer a dose from a failed parse.

## Admin mappings

Mappings contain only a name/name prefix, a match type, and a destination. Matching is case-insensitive. Name-prefix rules start at the beginning of the medication name and require a word boundary. They do not match a word buried elsewhere in the formulation. No fuzzy drug-name matching is used.

The longest matching prefix wins. An exact complete-name rule wins over prefix rules. This permits separate rules for heparin and heparin flush. Confirm the rule's scope before applying it. A mapping moves the complete order with that patient's dose and instructions. It never supplies or reuses a dose.

Changing a mapping does not silently rewrite every saved patient. It can update the current draft and pending import, or take effect on the next import. Use Reapply saved mappings to this room when needed, then review and save that handoff explicitly. Room/diagnosis settings changes preserve medication mappings.

## Landscape handoff

The PDF is US Letter landscape with eight columns: PATIENT, NEURO, RESP, CARDIAC, FEN / GI, HEME, ID, and LABS. The left column contains room, manually entered demographics/weight, and diagnoses. No patient-name or MRN field is added.

The lower bands are Other Medications, Lab Results / Trends, optional Additional notes, and Goals / Follow-up. The final row contains Airway, Last Intubation, Access, and Drains / Tubes. Long content continues on additional landscape pages with repeated headings instead of being clipped. The PDF is the preferred print export. HTML uses the same layout but browser pagination may differ.

Only Diagnoses and Medications are automatically imported in this version. Ventilation, vitals, cultures, labs, intake/output, nutrition, and wounds are still boundary-detected only. They can be entered manually. The lab trend area is editable text, not an automatically populated fishbone diagram.

## Storage and privacy

The password gate, private-repository check, Fernet encryption, fixed archive filename, generic commit message, and conflict protection remain. Rooms, handoff text, medication rows, and Admin mappings are encrypted before being sent to the data repository. The encryption key is kept in deployment Secrets, not the repository.

The host still receives and processes pasted clinical text before storage encryption. A shared app password and encryption do not establish clinical approval or HIPAA compliance. Use synthetic records until your institution approves both hosting and storage, access controls, agreements, and retention. Use an approved identity/access layer for clinical deployment.

The app does not intentionally write plaintext patient files, raw source text, or clinical logs. It does not use a cloud OCR/AI service. This does not control platform logs, memory, backups, browser artifacts, or operating-system behavior. Exports are unencrypted. Git history retains older encrypted saves. Replacing a room's current sheet is not a purge of that history.

Use Start blank for new patient when a room changes occupants. A room is not a patient identifier. Confirm the patient and all medication details in Epic before relying on the handoff.

## First-time deployment only

The existing create_secrets.py and Generate_Secrets.ipynb helpers remain included for a new deployment. They are not needed to update a working app. See START_HERE.html. Never regenerate or replace the encryption key of an existing archive without a deliberate re-encryption plan.

## Validation

See TEST_REPORT.md. Run the tests with python -m pytest -q after installing requirements-dev.txt in a test environment. All examples and bundled test fixtures are synthetic. No live GitHub connection or full Streamlit browser session was available in the build environment.
