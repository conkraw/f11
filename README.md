# PICU Handoff 6.6: dosing weight, admission date and expanded labs

Complete web-based Streamlit application, delivered as a ZIP. No direct GitHub changes were made.

## Update the existing app

Save open work. Extract PICU66.zip and open PICU_Handoff_v6_6_Demographics_Labs. Upload the folder CONTENTS into the existing application code repository, replacing matching files. Keep app.py at the repository root. Include the new demographics.py and all supplied Python files. No new packages are required.

Keep the existing Streamlit Secrets, password hash, encryption key, token, medication mappings and private data repository. Do not run create_secrets.py or Generate_Secrets.ipynb for this update. The helpers are for first-time deployment only.

Restart the deployment. The sidebar reads:

    Version 6.6 | Dosing weight, admission and expanded labs

Use Load demographics / labs example, then Create / update handoff in a test room. The example is synthetic, including its anti-Xa result. Re-paste the full SmartPhrase or only complete I, N and G sections to add the new information. Installation does not reconstruct fields that were never saved.

## Measured weight, dosing weight and admission

The I / NUTRITION block keeps measured weight and dosing weight separate. It recognizes the repeated Dosing Weight / Dosing headings, an explicit weight on the following line, and the relative age of the entry. Relative text such as 8 days ago is not displayed or converted into a date. Dose units, pump rates and medication '(Dosing Weight)' qualifiers never supply a dosing-weight value.

Below Diagnoses, the order is:

    ----
    Weight: 73.1 kg
    Dosing weight: 66.8 kg
    Z-score: [only when supplied for the measured weight]

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
| PT, INR, PTT, FIB and anti-Xa | Latest coagulation results in ID |

Names are matched case-insensitively. HEPLMW and generic ANTI-XA stay distinct, with no conversion of assay units, dosing, targets or reference ranges. There was no HEPLMW result in the supplied sample, so no value is fabricated. The demonstration includes a clearly synthetic result to exercise this field.

The request said to put 'CRP and coags' in Infectious Disease. This release follows that literally: both the coagulation group, including HEPLMW, and inflammatory markers print in ID. PROCAL from the sample is included there as well. They are not duplicated in the bottom lab band.

ID order is temperature first, then a separator, inflammatory/coagulation results, then the existing separated Cultures block, followed by notes and mapped medications. Lactic acid remains in Cardiovascular.

Latest/preceding means per component, not a confirmed common specimen. Dates and flags stay attached to the original results. Same-date results without collection times retain Epic's order. The latest supplied CRP can be older than the latest PROCAL. Matching dates may be shared in a group heading, but mixed dates are displayed separately. Missing values remain missing. No patient-level laboratory interpretation is performed.

Existing saved laboratory rows also use these display rules on export, including Mg/Phos that were previously saved under Other labs. Raw source values are not altered. All retained rows remain editable or excludable in Labs / Vitals.

## Existing features retained

Room selection and Other room. App sign-in. Encrypted private GitHub archive. Medication recognition, remembered system mappings, Admin editing without an open handoff, reversible hiding, held/future orders, taper connectors, linked PN orders, and repeated ADS entries with intentionally blank fields.

C/D respiratory support and qualified pressure/flow display rules. Observed tidal volume. E vitals and SpO2 range. F cultures with the latest two date/specimen display groups per category, continuation organisms and no sensitivities. K/L/M neurologic observations. CBC/BMP fishbones and horizontal other labs. Compact landscape output and Print all with a new page for each room. Very long handoffs continue onto extra pages instead of being cut off. H and J remain manual.

## Saved data and privacy

Schema 9 adds only dosing_weight and admission_date fields to each handoff. Schemas 1-8 migrate in memory. Missing new fields start blank. Existing room IDs, measured weights, cultures, notes, lab values, hidden orders, mappings, passwords, key and archive path are preserved. The next successful save writes schema 9. Do not roll back only some app files after that save.

The source SmartPhrase is not archived as a raw block. The host still receives and processes pasted text before encryption. Saved clinical fields are in the existing encrypted archive. Downloads are not encrypted. Earlier encrypted versions can remain in Git history. Continue using institution-approved hosting and storage. No live private archive or deployment Secrets were accessed in preparing this update.

## Validation

715 automated tests passed. The original 6.5 package passed all 653 inherited tests before changes. New tests cover the exact supplied weight pattern, inline N heading, partial/empty section updates, date validation, glucose/Mg/phosphorus/albumin, HEPLMW, source-specific result dates, ID routing, callbacks, independent rooms, encryption and migration. An encrypted schema-8 archive generated by the unmodified 6.5 code was opened with the same key and every prior field was compared for equality.

The one-page synthetic landscape preview was rendered and visually inspected. Streamlit is not installed in the build environment. UI checks use widget stubs, not a live browser. The hosted app and authenticated private storage were not tested. See TEST_REPORT.md.

Implementation reference: Streamlit Session State documentation describes callbacks running before the next script rendering, with widget state accessed using keys. Official documentation: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
