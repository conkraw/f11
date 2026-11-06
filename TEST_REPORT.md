# Version 6.6 validation

## Executed

The unmodified PICU65.zip passed 653 automated tests. The updated application passes 715 tests with `python -m pytest -q --disable-warnings`.

62 added cases cover dosing-weight parsing separate from measured weight, repeated Epic headings, missing values, no measured/dosing substitution, dated dosing weights, conflict rejection, valid/invalid admission dates, the inline N divider heading, independent I/N replacement, omitted sections, Z-score preservation, glucose, magnesium/phosphorus under both BMP trees, albumin in Hepatic, HEPLMW distinct from generic anti-Xa, latest dated CRP/PROCAL/coagulation in ID, excluded rows, old Other-lab rows, HTML/PDF/text and Print all, per-room callbacks, invalid saved fields, session upgrades and encryption.

Historical migration test fixtures were updated to remove fields that did not exist in their historical schema. Current-schema assertions were updated from 8 to 9. The compact-lab layout test now expects three bottom horizontal groups because coagulation and inflammation moved into ID. Existing data-validation restrictions were not relaxed.

The latest complete test run and another run from the freshly extracted delivery ZIP both passed all 715 tests.

## Cross-version check

A separate process using the original unmodified Version 6.5 files generated an encrypted schema-8 synthetic archive with medication mappings, notes, laboratory rows, culture rows and other fields. The new code decrypted the original ciphertext with the SAME key. Every prior field and setting matched. Only schema version 9 and the new blank admission_date/dosing_weight fields changed. These temporary test keys and archives are not included in the ZIP.

## Layout

The new synthetic example was rendered at 144 dpi and visually inspected. It is one landscape US Letter page at 7.2 pt body font. Admission appears at the top of Patient. Measured weight and dosing weight are separate below Diagnoses. Two glucose values appear in the BMP trees, and Mg/Phos appear beneath each tree with dates. Albumin is in the horizontal hepatic group. Temperature precedes the ID lab groups and cultures. The synthetic HEPLMW result retains its label and is not duplicated below. Text bounding boxes were checked against page boundaries.

## Not verified

Streamlit is not installed here. Callback and page-render checks use a widget stub, not the full Streamlit browser lifecycle. No live hosted deployment, private GitHub store or deployment secrets were accessed or tested. No direct GitHub changes were made.

The new code organizes recorded data. It does not establish current bedside support, specimen identity, de-identification, clinical accuracy or hosting approval. Per-component lab slots do not establish one shared blood draw. Unknown or conflicting inputs are not silently replaced with calculated values.
