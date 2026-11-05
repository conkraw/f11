# PICU Handoff SmartPhrase, version 3

This is a complete update to the working web-based SmartPhrase app. It adds immediate medication-mapping persistence, the requested invasive-ventilation display, and printing of multiple room handoffs. It is not a local PDF/OCR package.

## Update an existing deployment

Save open work, then upload all files from this folder to the existing application code repository, replacing matching files. Add the new ventilation.py, importing.py and batching.py modules. Keep app.py as the entry point. Include requirements.txt and the examples and .streamlit folders.

Keep your current deployment Secrets, password hash, encryption key, GitHub token, repository and branch unchanged. Do not run the secrets generator again. Do not upload .streamlit/secrets.toml or clinical records. Reboot the web app after replacing the code.

The archive filename remains encrypted-data/handoff-v1.enc. Schema 1 and 2 archives are migrated in memory to schema 3. Existing handoff notes, medications, IDs, rooms and mappings are retained. The next successful save, including an automatic medication-mapping save, writes schema 3 using the same encryption key. Do not partially roll back the code after that save. Maintain an approved backup of the encrypted archive and its key.

## Daily workflow

Select a room. Paste the SmartPhrase with paired A, B and/or C separators. Click Create / update handoff. Imported sections go directly into the editable draft. There is no review checkbox, separate Apply step, or replacement-confirmation checkbox.

Only sections present in the paste are updated. An A block replaces the configured diagnosis destination. A B block replaces the imported medication list, without accumulating duplicate copies. A C block replaces the automatic ventilation block. Separate manual system notes are preserved. A malformed supported block stops the whole import, with no partial application. Other sections remain manual at this stage.

Save handoff stores the current draft in the encrypted archive. Save all open handoffs is on the Print all page. These actions do not require confirmation checkboxes. The app still rejects malformed input, expired sessions, encryption failures and conflicting GitHub writes. Errors are not hidden to simulate a successful save.

Use Start blank for new patient whenever a room changes occupants. It immediately replaces the open draft. The saved room changes only when you save. A room number is not a patient identifier.

## Medication destinations are remembered immediately

Choose the system beside an order in Medications. The app automatically creates or updates a medication-name rule in the encrypted archive. The rule appears in Admin without a separate save there. No dose, route, frequency or rate is reused from a different patient.

An unmapped medication remains in Other Medications. Scheduled and PRN orders stay separate. The existing parser retains the source name/formulation, Dose, Route, Frequency and appropriate Last Rate. It omits Provider and Last Admin. A continuous fluid with a blank Dose and a valid Last Rate is displayed with @ rate. No dose or rate is calculated.

The automatic rule is a stable name prefix, for example acetaminophen or sodium acetate. Matching ignores capitalization and requires a complete prefix boundary. Existing exact or more-specific rules are respected. Heparin flush can have a different rule from heparin. There is no fuzzy drug-name matching. Review the suggested scope under Edit details for order, and refine it in Admin as needed.

A changed rule is reapplied to the open drafts. Saved handoff content is not silently rewritten. Save each changed draft, or use Save all open handoffs, to persist its content. Future imports use the remembered mappings. If GitHub rejects a mapping save, the app shows an error and restores the previous dropdown value rather than claiming it was remembered.

Admin works without any room or handoff open. Select a saved rule to edit its name, destination or matching style, or delete it. Admin has no separate password, but remains behind the app sign-in. There is no second confirmation checkbox for saving a rule.

## Invasive ventilation display rule

The C block must contain Vent Mode. The supplied Volume Targeted Pressure Control - PS mode is supported, as are the implemented volume-targeted pressure-control variants and explicit conventional mode labels listed in ventilation.py. BiLevel, BiPAP, CPAP, NIV and high-flow labels are excluded. An unfamiliar mode is not guessed.

This is a requested mode-based display rule, not a clinical determination of the airway. The heading Invasive Ventilation alone is never enough. A skipped mode does not establish that the patient is not invasively ventilated.

The automatic RESP block includes only these fields, in this order, when present:

```text
Vent Mode
Resp Rate (Set)
Vt (Set, mL)
PEEP (cm H2O)
Mean Airway Pressure
Insp Time (sec)
PIP Observed (cm H2O)
Pressure Support (cm H2O)
Trigger Sensitivity Flow (L/min)
FiO2 (%)
```

Values and units are retained from the source, without calculations or clinical interpretation. Missing fields are omitted and noted in the import status. Observed respiratory rate does not substitute for the set rate. Vt Set/Target does not substitute for Vt (Set, mL). Values from D or E are never used to fill a missing C value. Conflicting repeated fields produce an error instead of selecting a value arbitrarily.

The block prints at the top of RESP, followed by a literal ----- separator, then respiratory notes and medications. Vent ID, equipment ownership, verification, bedside equipment, charges, rise time, humidifier, heater temperature, minute ventilation and other unrequested fields are not imported.

A complete C block with an excluded or unknown mode removes the previous automatic ventilation block and explains the omission. An explicitly empty C block also clears it. A paste with no C block leaves the existing ventilation unchanged. A malformed C block does not apply changes. Manual Respiratory notes are never cleared by these operations.

Edit ventilator values is available under Paste / create. Clearing the automatic block does not remove respiratory medications or notes.

## Print all handoffs

Open Print all in the sidebar. All nonblank saved rooms and open drafts are selected by default. A current open draft takes precedence over that room's saved sheet, so a room never appears twice. A blank new-patient draft suppresses the old saved occupant's sheet in the current session's print packet. Deselect rooms you do not need.

Download all selected handoffs (PDF) produces one Letter-landscape PDF. Each room starts on a new page. Long handoffs continue onto additional pages, with the room and handoff reference repeated. Open the PDF and print it with your usual PDF viewer. Printing does not itself save a draft to GitHub.

The printable HTML download also contains all selected sheets and a Print all handoffs button. Open the downloaded HTML in a browser and use that button. PDF has the most predictable pagination. Downloads are unencrypted.

The layout retains the PATIENT, NEURO, RESP, CARDIAC, FEN / GI, HEME, ID and LABS columns, the full-width Other Medications band, and the lower notes/access rows. The synthetic example PDFs demonstrate the layout. Demonstration mapping choices in those PDFs are not installed as defaults.

## Storage and data handling

The existing app-password gate, private-data-repository check, Fernet encryption and GitHub SHA conflict protection remain. There is no separate Admin password. Hand-offs and mapping rules are encrypted before transmission to GitHub. The key stays in deployment Secrets. Fixed filenames and generic commit messages contain no room labels or clinical text.

The original pasted SmartPhrase is not saved in the archive. Successful import clears the paste widget. That is not secure erasure of browser or server memory. The Streamlit host necessarily receives the pasted text before storage encryption. No external OCR or AI service is called. Export PDFs are generated in memory, not as server-side patient files.

Use synthetic information unless your institution has approved both hosting and storage and their access, agreement and retention arrangements. Omitting names and MRNs does not make room-linked clinical information automatically de-identified. Git history retains earlier encrypted versions. Replacing a handoff is not deletion of that history. A shared-password prototype is not a compliance certification.

## First-time deployment only

For a new deployment, the included create_secrets.py and Generate_Secrets.ipynb helpers generate the app password hash and an independent encryption key. secrets.example.toml contains placeholders. Configure a separate private GitHub data repository and its restricted token. Existing users should not regenerate the key.

## Testing

Run python -m pytest -q with requirements-dev.txt installed in a test environment. TEST_REPORT.md describes the executed checks and their limitations. All bundled examples and tests are synthetic.
