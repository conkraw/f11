# PICU Handoff 6.9: coagulation below Hepatic, CRP and procalcitonin in ID

This is the complete web application, delivered as a ZIP. No direct repository
changes are made by distributing this package.

## Corrected lab placement

The lower Lab Results / Trends band shows CBC/BMP trees, then the horizontal
Hepatic summary, then the horizontal Coagulation summary, followed by blood gases
and other lab groups. Coagulation includes the latest supplied PT, INR, PTT, FIB
and anti-Xa results. HEPLMW remains labelled Anti-Xa (HEPLMW), separate from a
generic ANTI-XA component. Missing tests are not invented.

CRP and procalcitonin (PROCAL) stay in Infectious Disease. Temperature stays first,
then inflammatory results, the separate Cultures block, and ID notes/medications.
Other previously supported inflammatory markers retain their existing routing.
Coagulation no longer appears in the automatic ID block. Inflammatory markers
are not duplicated in the lower laboratory band.

Source values, dates, abnormal flags, per-component latest-result selection,
exclusions, and all retained rows are unchanged. Where a group contains different
dates, each value keeps its own date. No units or clinical interpretation are added.

## Existing saved handoffs

Reopen/print an existing saved sheet to use the corrected layout. No re-paste is
needed for results already in its structured laboratory snapshot. Text you typed
manually into notes is not removed or rewritten.

This is display-only. Storage schema remains 10 and existing data, passwords,
keys, medication mappings and hidden-medication rules are preserved. Weight,
Z-score, dosing weight (or none), admission date, viral results, vitals, cultures,
respiratory support and compact Print all behavior are unchanged.

## Update the existing app

1. Save any open work. Extract PICU69.zip.
2. Open PICU_Handoff_v6_9_Lab_Placement and upload its contents to the existing
   application code repository, replacing matching files. Keep app.py at the root.
3. Keep Streamlit Secrets, password, encryption key, token and private data
   repository unchanged. Do not rerun the secrets generator.
4. Restart the deployment. The sidebar should show:

    Version 6.9 | Coags below hepatic, CRP/procalcitonin in ID

No new dependencies or storage-format changes are required. Use Load demographics /
labs example for a synthetic check. The current preview is
examples/lab_placement_preview.pdf. Other bundled previews are historical references.

See TEST_REPORT.md for executed tests and deployment limitations.

---

The following feature reference describes the earlier additions. For installation
and lab routing, follow the Version 6.9 instructions above.

## Earlier feature reference (Version 6.7)

# PICU Handoff 6.7: positive respiratory viral results

Complete web-based Streamlit application, delivered as a ZIP. No direct GitHub changes were made.

## Update your existing app

Save open work. Extract PICU67.zip and open PICU_Handoff_v6_7_Viral_Positives. Upload the folder contents to your existing application code repository, replacing matching files. Keep app.py at the repository root and include the new viral.py. Keep every supplied Python module together.

Keep your existing Streamlit Secrets, password hash, encryption key, token, medication mappings and private data repository unchanged. Do not run create_secrets.py or Generate_Secrets.ipynb for this update. Those helpers are for first-time setup only. No new Python packages are required.

Restart the deployment. The sidebar should read:

    Version 6.7 | Positive respiratory viral panel

Choose a test room, click Load viral-positive example, then Create / update handoff. The included example is synthetic. Use your full SmartPhrase or just one complete O block to import the new results. Existing records are not reinterpreted without a new paste.

## O section and positive-only demographics

    oooooooooooooooooooooooooooooooo
    Respiratory Viral Panel:
    Lab Results
    Component    Value           Date
    HUMRHINENRNA Detected (A)    01/01/2026
    ADENOVIRDNA  Not Detected    01/01/2026
    oooooooooooooooooooooooooooooooo

Copy directly from Epic with tabs between columns. The parser also supports double-spaced columns and simple one-token component rows with collapsed spacing. Each divider needs at least eight copies of the same letter on a separate line.

The Patient/demographics column gains a block below Diagnoses and the weight/dosing-weight/Z-score lines:

    ----
    Positive: Rhinovirus/enterovirus

Only explicit Detected or Positive results, optionally followed by a recognized flag such as (A), qualify. Not Detected, Negative, pending, inconclusive and indeterminate values do not print as positive. The summary prints names only, without negative results, dates, abnormal flags or the whole panel. Multiple positives are comma-separated and duplicate names print once.

An included O block replaces the previous O snapshot. A negative-only, empty or no-results O block removes the prior automatic positive display. Omitting O leaves it unchanged. Reimport does not accumulate duplicate positives. No values are inferred from the diagnoses, cultures, medications or other source sections.

## Display names and review

The raw component, result and date are retained in the encrypted handoff snapshot for review in Labs / Vitals > Respiratory viral panel. The original pasted text is not added to the archive. Display names are editable for that handoff, and inclusion can be switched off and back on without deleting the underlying row.

HUMRHINENRNA is assigned the combined display label Rhinovirus/enterovirus. This is an explicit application alias based on the supplied code, not an independently verified local Epic test dictionary. It does not report separate rhinovirus and enterovirus infections or claim rhinovirus alone. Review the original component and change the display name if your local laboratory label differs. Common respiratory panel catalogs use a combined human rhinovirus/enterovirus target. Other known labels from the supplied format have literal aliases. Unfamiliar components remain visible under their original code rather than being silently discarded or assigned a guessed species. SARSRNA remains a source code unless you edit its display name.

If multiple dates are supplied for the same component, only the newest supplied result is eligible for the compact summary. A newer negative, pending or unresolved row does not reuse an older positive. When latest same-day positive/nonpositive results conflict without complete ordering information, the import stops and asks for verified times or corrected source text. No current date, collection time or active-infection status is inferred. All parsed source rows remain in the editor, but only qualifying current-snapshot positives print.

## Storage compatibility

Schema 10 adds viral_panel. Schemas 1-9 migrate in memory with the same encryption key, keeping every previous field and setting. Admission date, dosing weight, medication mappings, hidden-medication rules, notes, cultures, lab rows, respiratory support and room references are preserved. The next successful save writes schema 10. Do not mix older source files into this package or partially downgrade after saving.

The new block appears in PDF, HTML, plain text and Print all. It uses the existing compact landscape layout. Very long sheets still continue onto another page rather than clipping content. Existing behavior outside the O section is unchanged.

## Validation and limits

The 715-test unmodified Version 6.6 suite passed before editing. The updated suite has 815 passing automated cases, including 100 new O-block cases. Tests cover status negation, combined labels, unknown codes, current/older dates, duplicates, conflicts, incremental imports, edits, clearing, migration, encryption, callbacks, page-render stubs and PDF/HTML/text/Print all. The complete delivery ZIP is checked for integrity and the suite is rerun from an extracted copy. See TEST_REPORT.md for exact runs and limitations.

This build environment does not have Streamlit installed. Callback/page-render tests use a widget stub, not a real Streamlit browser lifecycle. No live deployment, private GitHub store or deployment Secrets were accessed. A PDF preview is rendered and visually checked using synthetic information. This feature organizes supplied results and does not diagnose current infection or certify clinical/privacy suitability.

## Primary technical references

- Streamlit session state and callback lifecycle: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- Mayo Clinic Laboratories respiratory panel catalog, including the combined human rhinovirus/enterovirus target: https://www.mayocliniclabs.com/test-catalog/overview/609409

The catalog does not establish the meaning of a local Epic abbreviation. Display aliases remain visible and editable as described above.

## Existing functions retained

The following is the prior release's workflow reference. Its fields and routing remain supported.

## Measured weight, dosing weight and admission

The I / NUTRITION block keeps measured weight and dosing weight separate. It recognizes the repeated Dosing Weight / Dosing headings, an explicit weight on the following line, and the relative age of the entry. Relative text such as 8 days ago is not displayed or converted into a date. Dose units, pump rates and medication '(Dosing Weight)' qualifiers never supply a dosing-weight value.

Below Diagnoses, the order is:

    ----
    Weight: 73.1 kg
    Z-score: [only when supplied for the measured weight]
    Dosing weight: 66.8 kg [none when no dosing weight is supplied]

No dosing weight is inferred from measured weight. A dosing-only source does not create a measured weight. Percentiles, growth-chart notes and measurement dates are omitted from this compact demographic output, as in the previous release.

The new N block uses either an inline or separate-line admission date:

    nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
    Date of Admission: 10/11/2026
    nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn

Admission prints near the top of the Patient column. The recorded date is kept separately from nutrition and imported notes. Invalid or conflicting dates stop that import rather than being guessed. No date is calculated from a hospital-day count, dosing-weight age or other section.

Labs / Vitals now has a Demographics / Weight editor for the measured weight, Z-score, dosing weight and admission date. Dosing weight and admission can be cleared individually. Inclusion of measured weight/Z-score remains independent of dosing weight.

An included I block replaces measured weight, Z-score and dosing weight together. If the new I block has no dosing weight, the old imported dosing weight clears. An empty N block clears the old imported admission date. Omitted sections remain unchanged. Reimporting G or ordinary E vitals never erases demographic fields.

## Lab selection and placement

| Source label | Output |
| --- | --- |
| GLUCOSE, GLU or GLUC | Glucose node in latest and preceding BMP trees |
| MG or MAGNESIUM | Dated Mg line below each BMP tree |
| PHOS, PHOSPHORUS or PHOSPHATE | Dated Phos line below each BMP tree |
| ALBUMIN or ALB | Latest albumin in the horizontal hepatic panel |
| HEPLMW | Latest Anti-Xa (HEPLMW) with the coagulation group |
| CRP, PROCAL / PROCALCITONIN | Latest results in ID |
| PT, INR, PTT, FIB and anti-Xa | Latest coagulation results below Hepatic in the laboratory band |

Names are matched case-insensitively. HEPLMW and generic ANTI-XA stay distinct, with no conversion of assay units, dosing, targets or reference ranges. There was no HEPLMW result in the supplied sample, so no value is fabricated. The demonstration includes a clearly synthetic result to exercise this field.

Version 6.9 changes the earlier routing: coagulation, including HEPLMW, prints below Hepatic in the laboratory band. Inflammatory markers, including CRP and PROCAL, stay in ID. Neither group is duplicated in another automatic section.

ID order is temperature first, then a separator, inflammatory results, then the existing separated Cultures block, followed by notes and mapped medications. Coagulation follows Hepatic in the laboratory band. Lactic acid remains in Cardiovascular.

Latest/preceding means per component, not a confirmed common specimen. Dates and flags stay attached to the original results. Same-date results without collection times retain Epic's order. The latest supplied CRP can be older than the latest PROCAL. Matching dates may be shared in a group heading, but mixed dates are displayed separately. Missing values remain missing. No patient-level laboratory interpretation is performed.

Existing saved laboratory rows also use these display rules on export, including Mg/Phos that were previously saved under Other labs. Raw source values are not altered. All retained rows remain editable or excludable in Labs / Vitals.

## Existing features retained

Room selection and Other room. App sign-in. Encrypted private GitHub archive. Medication recognition, remembered system mappings, Admin editing without an open handoff, reversible hiding, held/future orders, taper connectors, linked PN orders, and repeated ADS entries with intentionally blank fields.

C/D respiratory support and qualified pressure/flow display rules. Observed tidal volume. E vitals and SpO2 range. F cultures with the latest two date/specimen display groups per category, continuation organisms and no sensitivities. K/L/M neurologic observations. CBC/BMP fishbones and horizontal other labs. Compact landscape output and Print all with a new page for each room. Very long handoffs continue onto extra pages instead of being cut off. H and J remain manual.

## Saved data and privacy

The earlier dosing_weight and admission_date fields are preserved. Schema 10 adds only viral_panel to the preceding schema-9 handoff. Schemas 1-9 migrate in memory, initializing only fields that did not exist in the old schema. Existing room IDs, measured weights, cultures, notes, lab values, hidden orders, mappings, passwords, key and archive path are preserved. The next successful save writes schema 10. Do not roll back only some app files after that save.

The source SmartPhrase is not archived as a raw block. The host still receives and processes pasted text before encryption. Saved clinical fields are in the existing encrypted archive. Downloads are not encrypted. Earlier encrypted versions can remain in Git history. Continue using institution-approved hosting and storage. No live private archive or deployment Secrets were accessed in preparing this update.

