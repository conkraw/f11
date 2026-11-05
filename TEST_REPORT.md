# Validation report

## Completed

147 automated tests passed in the final regression run.

Coverage includes the previous diagnosis parser, password hashing, encryption, room handling, save conflicts, medication parsing and formatting, provider/Last Admin exclusion, blank-dose infusion rate fallback, separate scheduled and PRN orders, no silent duplicate-order removal, case-insensitive mapping, specific-prefix priority, explicit medication replacement, room isolation, schema-1 encrypted archive migration, and schema-2 encrypted save/load round trips.

A separate acceptance check used the nine medication rows supplied for this change. It detected all nine orders, preserved both albuterol frequencies, retained the ordered ceftriaxone Dose column, kept the topical dose blank, omitted the intermittent zero pump rate from its handoff wording, and used 40 mL/hr for the continuous fluid with a blank Dose. The clinical input and provider names are not bundled in this package.

PDF tests verified landscape Letter dimensions, required headings, long-column continuation, long lower-band and access-field continuation, retention of every unique test text token exactly once, and page-bound geometry for the long-column case. The synthetic landscape PDF was rendered to an image and visually inspected for overlaps and clipping.

Full handoff and Admin page-render code was exercised using a widget stub, including both draft and pending medication editors on one page. Callback tests cover applying diagnoses/medications in either order, confirmation before replacement, review gating, mapping changes, and new-patient resets.

## Not completed

The actual Streamlit package could not be installed in this build environment because network package retrieval was unavailable. Stub tests do not reproduce the browser's full widget lifecycle and are not a substitute for a real Streamlit browser test.

No live deployment, live GitHub read/write, institution-specific Epic clipboard behavior, clinical validation, or privacy/compliance assessment was performed. GitHub calls were simulated in tests. The sample PDF is a layout check, not proof of clinical correctness.

## Deployment check

Use Load synthetic example first. Expect two synthetic diagnosis lines and nine medication orders. All medications begin in Other Medications with an empty mapping dictionary. Save a test mapping for acetaminophen to Neurologic and for sodium acetate to FEN / GI, apply/review/save the room, then reopen it to check persistence. Confirm that your existing deployment's encrypted archive and Secrets are preserved before entering clinical information.
