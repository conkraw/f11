# PICU Handoff 6.11: custom rooms and neurologic infusions

Complete web-app package. Delivered as a ZIP only. No direct repository changes.

## Update your existing application

Save open work before replacing files. Extract PICU611.zip, open the
PICU_Handoff_v6_11_Rooms_Infusions folder, and upload its contents into your existing
application code repository. Replace matching files and keep app.py at the root.
Include the new infusions.py module and all other supplied Python files.

Keep your existing Streamlit Secrets, password hash, encryption key, GitHub token,
and private data repository unchanged. Do not rerun create_secrets.py or the
secrets-generation notebook. No new dependencies relative to Version 6.10.
Restart the deployment and look for:

    Version 6.11 | Custom rooms and neurologic infusions

## Custom rooms and preset labels

All preset rooms use a capital P, including P4201, P4203, P4209 and P4211 through
P4223. Entering a preset number without P opens the same room rather than a new
bed. Custom labels outside the preset list are not automatically rewritten.

Old numeric preset labels are migrated in the encrypted archive and in an open
session. IDs, dates, notes, source values and saved medication mappings are kept.
Conflicting room aliases are rejected rather than merged or overwritten.

To remove an added room, open it and expand Custom room options, then choose
Remove custom room. Or open Admin > Custom rooms and remove a selected custom
room without opening its handoff. Preset rooms are not listed for removal.

Removal deletes that room's current saved handoff and open draft from the active
archive/session and from Print all. It does not change medication mappings or
other rooms. A failed or conflicting save leaves the room and draft in place.
Undo last room removal is available during the same signed-in session, restoring
the prior saved handoff and any separate unsaved draft. It will not overwrite a
room that has since been added again. Only the last removal is available to undo.
Older encrypted Git history is not securely erased by this action.

## Neurologic infusion display

Neurologic vitals, target arousal, WAT and ICP/CPP remain at the top. Visible
medications mapped to Neurologic are grouped as:

    Neurologic observations
    -----
    INFUSIONS
    Medication / complete formulation
    Dose: explicit ordered dose
    Recorded rate: source pump rate, when different and present
    Route | Frequency
    -----
    Separate notes
    -----
    OTHER MEDICATIONS
    Remaining scheduled, once and PRN entries

Infusion names are bold. Their explicit Dose line is bold and underlined. A
recorded rate is separate so a weight-based dose is not confused with mL/hr. If
Dose is blank, the recorded rate is emphasized instead. No dose is calculated,
reused from another patient, or inferred from a product concentration. Blank dose
and rate stay blank. The complete formulation, held/start labels and source
qualifiers stay visible. User-supplied custom wording remains authoritative.

Continuous parenteral orders are recognized automatically from their route and
frequency. An infusion product name or a historical pump rate alone is not enough.
A q30 min PRN infusion-syringe order remains separate as a non-infusion unless you
explicitly change its display choice. This is display grouping, not a determination
of current pump use or a treatment recommendation.

In Medications, each Neurologic order has a Neuro display dropdown: Automatic,
Infusion, or Other medication. A change is saved as a reusable encrypted rule keyed
to that complete formulation, route and frequency. It does not remap the medication
to a system or copy its dose. It applies to matching open drafts and future imports.
Previously saved handoffs are not silently rewritten. Their stored choices remain
until they are imported or edited and saved again. Old handoffs with no choice use
Automatic when rendered, without needing a new paste.

Admin > Infusion display choices allows changing or clearing an override even
when no handoff is open. Automatic removes the override. Medication system mapping
and hiding/restoration continue to work independently.

All print formats retain the grouping. PDF and HTML provide the bold/underlined
emphasis. Plain text has headings and explicit Dose/Recorded rate labels but no
font styling. Compact PDF entries stay together at page boundaries when they fit.
Extremely long entries or handoffs continue instead of being clipped.

## Saved-data migration

Schema 11 adds saved infusion display preferences and canonical preset-room labels.
Schemas 1 through 10 migrate on load with the existing encryption key. The next
successful save writes schema 11 to the same encrypted-data/handoff-v1.enc path.
Do not downgrade individual application files after saving in the new schema.
Keep the full update together. No raw pasted SmartPhrase is added to storage.

## Existing features retained

Room-switch autosave, manual Save/Save all, no example-loading buttons, Eastern
print-preparation timestamps, Rapid Viral Panel heading, bold positive organisms,
compact landscape printing, CBC/BMP trees with dates, hepatic/coagulation summaries,
CRP/procalcitonin in ID, separated cultures, SpO2 ranges, neurologic observations,
weight/Z-score/dosing-weight order, admission date, respiratory settings, medication
taper/PN/ADS handling, remembered system assignments and hidden medications remain.

Click Create / update handoff after pasting. Unsubmitted pasted text is not an
imported draft and is not automatically saved. A failed room-switch save keeps the
current room open. Save before logout or closing the browser. Session-only mode
is not durable storage. Print all uses each room's latest draft when present.

## Printing and privacy

PDFs receive an America/New_York timestamp when prepared for download (EST or EDT
as applicable). Download a fresh PDF to print later with a fresh timestamp. The
saved PDF cannot detect physical printing. HTML updates its timestamp when browser
print preview opens. Exports are unencrypted.

The app host processes pasted content before storage encryption. Private archive
checks and encryption remain, but shared-password access and removing name/MRN
fields do not establish clinical approval. Use institution-approved hosting and
storage for patient information. No deployment secrets or private records were
accessed while building this ZIP. Source examples are synthetic.

## Testing

See TEST_REPORT.md. For a synthetic visual example, open
examples/rooms_infusions_preview.pdf or paste examples/synthetic_neuro_infusions.txt.
The installed app starts with your existing mappings, not the example's illustrative
mappings. Assign the example medications to Neurologic to see infusion grouping.

Implementation references:
- https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox
- https://docs.streamlit.io/1.52.0/develop/api-reference/widgets/st.download_button
