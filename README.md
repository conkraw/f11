# PICU Handoff, Version 6.2

Dated lab trees, routed vital signs, and reversible medication hiding. This is the complete web-based application. It retains the Version 5 respiratory-support handling, remembered system mappings, encrypted GitHub storage, editable landscape handoffs and Print all.

## New in 6.2: neurologic observations, weight and observed tidal volume

K (Target Arousal Level), L (WAT Score) and M (ICP Trends) import as independent neurologic vital-sign groups. Their nonblank values appear at the top of NEURO, in K/L/M order, before manual notes and medications. Original labels and values are retained, including WAT-1 zero, SBS -1, pressure units and source ranges. CPP stays beside ICP. Blank labels and numerical ranges in headings do not become scores. No clinical value is calculated.

The I (NUTRITION) block imports only the recorded weight and Z-score. These print below Diagnoses in the PATIENT column, after ----. For example: Weight: 15.3 kg and Z-score: 0.41. Dates, percentiles, asterisks and growth-chart footnotes are excluded from the new nutrition record and output. A missing Z-score stays blank. Multiple dated weights use the newest date, retaining source order for equal-date readings with a notice. Without complete dates, the first source row is used with a notice.

The C-block parser now reads Vt (observed, mL). It prints immediately after Vt (Set, mL). Neither the set nor target volume is substituted for a missing observed volume. The existing invasive-mode display rule remains unchanged.

Use Labs / Vitals to edit or exclude neurologic observations and weight/Z-score. Use the existing respiratory editor to edit observed Vt. Include controls change the output without deleting retained values. No new approval or confirmation steps are required.

Only included sections are replaced. A present empty K, L, M or I clears that section's previous automatic values. An omitted section stays unchanged. Updating E alone does not clear K/L/M. Updating A alone does not clear weight. Manual notes stay separate. Start blank for new patient clears all these values with the rest of the draft.

Load neuro / weight example demonstrates WAT-1 zero, ICP/CPP and weight. Load observed-Vt example demonstrates SBS -1 and separate set/observed volumes. Bundled examples are synthetic. No new runtime dependencies are required.

## Medication taper fix

Version 6.1 fixes the Epic `Followed by` rows that previously added an eighth column to the preceding medication and stopped the full import. The connector is now preserved as `Followed by:` on the next, separate medication entry. It is not interpreted as a new medication or attached to a discarded Provider/Last Admin cell.

`[START ON ...]` annotations remain in the editable name, encrypted handoff and printed output exactly as supplied. Each taper step keeps its own dose, route and frequency. The app does not combine steps, calculate a schedule, infer an end date, or decide which step is current from the server date.

Saved drug-to-system mappings now match scheduled orders without being blocked by start-date prefixes. Known hold/discontinued labels also remain visible. Mapping suggestions omit these annotations and the sequence marker. An unknown bracket annotation is not silently removed for drug-name matching.

Hiding a dated step is specific to its complete name and start-date annotation. It does not hide another dated step with the same formulation. An explicit broad prefix rule in Admin can still cover a drug family. The saved rule ignores the `Followed by:` display prefix but keeps the start date for exact hiding.

Standalone connectors, tab-indented connectors, a connector in an extra final tab cell, normal Windows line endings, and clearly tabular rows without bullets are supported. Ambiguous or incomplete sequences, missing medication columns and unrelated extra columns still stop the import without changing the existing draft. Arbitrary future Epic formats are not guaranteed to work.

Use `Load medication-taper example`, then `Create / update handoff`, for a synthetic test. The example includes three separate steroid steps, an infusion, blank respiratory blocks, vitals and laboratory results. An empty C/D section is valid: it supplies no respiratory device. The blue respiratory and lab notices are informational, not medication-import failures.

Version 6.1 retained schema 6. Version 6.2 migrates to schema 7 for the new independent observations. No password reset, key replacement, settings reset or new runtime dependency is needed. Existing lab trees, vital routing, hidden medications, respiratory support and Print all remain included.

## Update a working deployment

Save open handoffs. Extract the complete ZIP and copy the contents of the PICU_Handoff_v6_2_Neuro_Weight folder into your existing application code repository, replacing matching files. Keep app.py at the repository root. Include observations.py and every supplied application module. Do not replace only app.py. Restart the deployment after the upload.

Keep your current Streamlit Secrets, app password, encryption key, GitHub token and private data repository unchanged. Do not run create_secrets.py or Generate_Secrets.ipynb again for an update. No new runtime dependencies are needed beyond the existing ReportLab/Streamlit requirements. The notebook and secrets helper are only for a first-time deployment.

The sidebar should say: Version 6.2 | Neuro observations, weight and observed Vt.

This package does not upload or change your repository for you. It does not reset stored medication assignments or saved handoffs. Schema 1-6 archives migrate in memory to schema 7, and the next successful save writes schema 7 with the same key. Version 6.1 used schema 6. Existing rooms, notes, labs, vitals, hidden-medication rules and mapping rules are preserved. Update all application files together. Do not downgrade after saving with the new schema.

## Everyday use

Select a room, paste the SmartPhrase, and click Create / update handoff. You can paste the entire phrase or only the paired sections being updated. Imported snapshots replace their previous corresponding snapshot, not your separate manually entered system notes. An omitted section is left unchanged. Save handoff stores the editable draft. Print all includes saved sheets and the latest open drafts, with each room starting on a new landscape page.

There are no added approval or confirmation steps. Malformed supported sections still stop an import rather than applying a partial, potentially misleading handoff.

## Laboratory results: G block

CBC and BMP each have two dated result trees: latest per component and preceding per component. The CBC tree positions are WBC, hemoglobin, hematocrit and platelets. MCV and absolute neutrophil/lymphocyte counts remain underneath when supplied. BMP positions are sodium, potassium, chloride, CO2, BUN, creatinine and glucose, with calcium below when supplied. A missing result is shown as --, never zero or a calculated value.

The source provides individual component rows, not verified panel/specimen identifiers. Therefore these trees are not claimed to be results from one blood draw. Every value has its own source date. Dates are sorted newest first. When multiple rows have the same date and no collection times, their source order is retained, assuming the Epic table is newest-first within that date. When every result for a component on a date includes a time, those times are used. Mixed timed/untimed rows on one date keep source order because their exact relative timing cannot be determined. Identical rows are retained because the paste does not establish whether they are duplicates or separate observations.

Hepatic, coagulation, inflammatory and other components show one latest result each in labelled branch diagrams. Arterial, venous and capillary blood gases remain separate. No bicarbonate, reference range, unit, calcium, glucose or missing lab is calculated. Original flags such as (H), (L), (LL) and inequalities are preserved.

Recognized lactate/lactic-acid components go to Cardiovascular, below its vitals and before notes/medications. Lactate is not repeated in the lab-tree band. If no lactate is in the paste, none is added. Distinct source-specimen labels remain distinct.

All imported lab rows remain available under Labs / Vitals > Edit retained laboratory rows. You can correct a value or its source date and include/exclude a result. Display selection is recalculated. Older rows not selected for the compact output are not deleted from the current snapshot. Re-pasting G replaces the snapshot, using only that paste. A valid empty G block clears it. Source 'No results found' statements are retained as source notes, not normal results.

Trees print in Lab Results / Trends below the main system columns. Longer sheets continue onto landscape pages without truncation. HTML includes the same SVG diagrams, but PDF is preferred for predictable pagination. All supplied preview data is synthetic.

## Vital signs: E block

Resp/respiratory rate, SpO2 and FiO2 go to Respiratory. Heart rate, blood pressure, arterial pressure, mean arterial pressure and central venous pressure go to Cardiovascular. Temperature goes to Infectious Disease. Unrecognized labels remain in Other with a notice instead of being silently discarded.

Vital signs always come first within their system, above respiratory support, lactate, notes and medications. The displayed ranges, most recent recorded values and supplied units are kept as text. No mean pressure, unit or range is calculated. Vital-sign FiO2 remains a vital-sign line and does not overwrite device-specific FiO2.

Use Labs / Vitals to edit or exclude a vital-sign line. Re-pasting E replaces the previous automatic vitals, preserving separate notes and support settings.

## Hide medications without deleting them

Use Hide from handoff next to a medication. It moves to the Hidden medications list and is omitted from PDF, HTML, text and Print all exports. Its complete current order remains retained and editable. Use Restore to handoff to bring it back. Admin also has Hidden medication rules, usable without an open handoff.

Hiding is remembered as an exact formulation/name rule, separately from the system mapping. This prevents hiding an ADS Override Pull entry from accidentally hiding an active albuterol order. Different formulations or product amounts are not silently hidden by a broad drug-name guess. A future import of the same exact formulation stays hidden. Changing its mapped system does not unhide it. Restore saves the reversed rule and updates matching open drafts. Already saved closed room sheets are not silently rewritten. Open/reimport and save those handoffs when their saved content needs changing.

An explicit ADS Override Pull row with blank dose, route and frequency is now retained with a review note instead of blocking the entire medication import. Its missing order fields are not filled or inferred, and it is not hidden unless you choose to hide it. Other malformed medication rows still block an import.

Include order, inside an order's detail editor, remains a one-handoff inclusion setting. Hide/Restore is the remembered rule. Hidden entries that disappear entirely from a later source medication list are not revived as current orders by a new import. Their visibility rule remains available in Admin.

## Sections currently imported

A: Diagnoses. B: Medications. C/D: respiratory support. E: VITALS. G: LABS. I: weight and Z-score. K: target arousal. L: WAT-1. M: ICP/CPP.

F cultures, H intake/output and J wound review have recognized boundaries but are not automatically imported. Nutrition content beyond weight/Z-score is not imported. Manual fields remain available. No clinical value is inferred from an empty field.

## Storage and deployment

The app password gate and encrypted private GitHub archive are unchanged. Structured labs, vitals, medication details and visibility rules are inside the encrypted archive. The full raw SmartPhrase is not stored there. Source text still enters the app host and browser memory before encryption. Omitting names or MRNs does not establish de-identification or clinical hosting approval. Use institution-approved hosting, storage and access controls for clinical use. Start with synthetic data.

Exports are unencrypted. Earlier encrypted saves remain in Git history. Removing a current sheet is not a purge of previous history. A room is not a substitute for patient identification in Epic. The app has not been validated as a medical device or as a source of clinical decisions.

## Validation

See TEST_REPORT.md. Tests use synthetic fixtures, in-memory encrypted archives, mocked storage requests and Streamlit widget stubs. A separate compatibility check opened a synthetic archive generated by the unmodified Version 6.1 package with the new code and the same key. Every original saved field and Admin setting matched. Streamlit was not installed in the build environment, so a real Streamlit browser session and your hosted private storage connection remain untested.

## Technical references

Streamlit session state and callbacks: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state

ReportLab graphics: https://www.reportlab.com/chartgallery/

Fernet encryption: https://cryptography.io/en/latest/fernet/
