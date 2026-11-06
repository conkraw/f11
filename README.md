# PICU Handoff 6.5: cultures and ADS medication fix

Complete web-based SmartPhrase application, delivered as a ZIP. No direct repository changes are made during this update.

## Update your working app

Save open work. Extract PICU65.zip and open PICU_Handoff_v6_5_Cultures. Upload the CONTENTS to your existing application code repository, replacing matching files. Keep app.py at the repository root. Include the new cultures.py file and all the supplied Python files.

Keep your current Streamlit Secrets, password hash, encryption key, token, medication mappings and private data repository. Do not run create_secrets.py or Generate_Secrets.ipynb again. No new dependencies are needed. Existing archives migrate to schema 8 in memory, adding an empty culture snapshot without changing previous values. The next successful save uses schema 8. Do not downgrade only some application files after saving.

The sidebar should read: Version 6.5 | Cultures and ADS medication fix

Re-paste a previously rejected SmartPhrase. To add cultures alone, paste only the complete F block. Installation does not re-parse already saved handoff text.

## Medication fix

The section parser previously stripped whitespace from both ends of a completed block. That removed meaningful empty TAB cells at the end of the final medication row. A final ADS Override Pull entry, with its expected blank cells, then appeared to have too few columns and stopped the complete import.

The section parser now trims only empty framing lines. It preserves trailing TAB cells on a real row. The medication parser also accepts an explicitly labelled name-only ADS Override Pull entry when its empty trailing cells were already removed by the clipboard. This exception applies only when every later cell is blank and the name ends in ADS Override Pull.

Each supplied row remains separate, even when the same entry repeats. Product strengths in a name are not promoted into doses. Blank dose, route, frequency and rate fields remain blank. Extra nonblank fragments or an ordinary incomplete order still fail rather than being guessed. Entries are not hidden automatically. Existing Hide from handoff / Restore controls and exact formulation rules remain available.

The reproduced medication pattern imports all 12 source rows, including eight separate ADS entries. Provider and Last Admin cells are still omitted from parsed handoff records.

## Culture import

Paste the F section using the existing paired f dividers:

```text
ffffffffffffffff
CULTURES:
Susceptibility data from last 90 days.
Collected    Specimen Info    Organism
01/06/26    Blood, Venous    No growth (Preliminary)
ffffffffffffffff
```

Copy the original Epic table so TAB boundaries remain intact. The aligned example above illustrates the columns. Ordinary single spaces are not a reliable delimiter inside specimen and organism names.

Only collection date, specimen location and organism/result are retained. Antibiotic column headers, sensitivity values and the susceptibility heading are not stored in the culture snapshot or printed. A continuation with blank date and specimen cells belongs to the immediately preceding dated specimen. All recorded organisms in that continuation are retained together.

Temperature remains first in the ID column. A six-dash separator precedes Cultures. ID notes and medications follow another separator. The same order is used by PDF, HTML, plain text and Print all.

## How the latest two are selected

The compact handoff shows two newest collection-date/specimen display groups per category. Blood sites share the Blood category. Explicit sputum, tracheal and bronchial samples share Respiratory. Urine, CSF, stool and wound categories are separate. Other named sites each have their own category, so a pericardial specimen is not lost among newer blood results. An unspecified Aspirate stays under its own site and is not assumed to be respiratory.

Repeated rows with the same collection date/time and specimen label combine for display only. Their distinct organisms and statuses remain visible. Identical repeated status text is shown once. These display groups are not asserted to be individual cultures: the pasted table does not supply accession numbers. All original dated rows remain individually retained in the culture editor. Same-date ties without times use Epic source order. No time or final status is invented.

This prevents repeated No growth (In process) / No growth (Preliminary) rows for the same date and site from using both display slots. For example, a repeated central-line group on January 6 and an older blood group on January 5 are both eligible for display. Different blood sites on the same date remain different groups and can occupy the two slots.

The Cultures tab shows the compact output and all retained rows. Edit the collection date, sample location or organism lines, or exclude a row from selection. Exclusion does not delete the row. An older group becomes visible when newer groups are excluded. Sensitivity columns cannot be recovered from this snapshot because they were deliberately not retained.

An included empty F section or a valid No results found F section clears previous imported culture output. Omitting F leaves it unchanged. Reimporting F replaces only the culture snapshot. Manual notes, medication assignments, vital signs, labs and respiratory settings are independent. Ambiguous culture rows stop the import rather than attaching an organism to an uncertain specimen.

## First test

Use a blank test room. Click Load cultures / ADS example, then Create / update handoff. The synthetic sample contains 12 medication rows, including eight ADS entries, plus cultures with multiple organisms, duplicate status rows and an older positive specimen from another site. Open Cultures, then Preview / print. The supplied examples/cultures_preview.pdf contains two synthetic room sheets.

## Existing features retained

Room-based handoffs and a free-text Other room option. App sign-in. Immediate reusable medication-to-system assignments and Admin editing without an open handoff. Unmapped orders go to Other Medications. Exact-name reversible hiding. Medication taper, held/future-order and linked PN parsing.

Respiratory support from C/D, including the existing qualified pressure/flow display rules, standard nasal cannula, separate set and observed tidal volumes, and source-specific FiO2. E-block vitals stay above support and medications. SpO2 Avg/Min/Max summaries display only the recorded range. Lactic acid stays in Cardiac. K/L/M neurologic observations stay at the top of Neuro. I-block weight and Z-score print below diagnoses, without percentiles or footnotes.

CBC and BMP show two dated per-component fishbones. Other lab groups are horizontal with one latest result per component. Gas types remain separate. Same-date results without times retain source order. Missing results are not calculated. Compact landscape PDF printing attempts one page within its existing font-size limits, then uses continuation pages rather than clipping. Each room starts on a new page in Print all.

H and J remain manual. No new interpretation of intake/output or wounds is added.

## Storage and privacy

The archive path, authentication code, encryption code and GitHub storage client are unchanged. Culture snapshots are inside the same encrypted archive. The host processes pasted text before storage encryption. The app does not save the original full SmartPhrase to the archive. Exports are unencrypted and Git history retains earlier encrypted saves. No live handoff repository or deployment Secrets were accessed to prepare this ZIP. Use only the hosting and storage arrangements approved by your institution.

The secrets-generation helpers are included for first-time deployment only. For an existing deployment, keep the original encryption key and private data repository. An app-password change is not a reason to generate a new encryption key.

## Validation

See TEST_REPORT.md. The full suite has 653 passing tests, including 65 new cases for ADS rows, cultures, import atomicity, editing, migration, encryption and export. The preview was rendered and visually checked. The hosted Streamlit browser and live private storage connection were not tested. UI checks use widget stubs. No claim of independent clinical validation or universal support for arbitrary future Epic layouts is made.
