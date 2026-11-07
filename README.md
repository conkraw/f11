# PICU Handoff 6.12: one latest blood gas

Complete web-app package, delivered as a ZIP. No direct repository changes.

## Update your existing app

Save open work, extract PICU612.zip, then upload the contents of
PICU_Handoff_v6_12_Latest_Gas into the existing code repository. Replace matching
files and keep app.py at the root. Include the new blood_gases.py and every
updated Python module. Do not mix versions of the model, importer and renderer.

Keep your Streamlit Secrets, password hash, encryption key, token and private
storage repository unchanged. Do not rerun either secrets generator. No new
packages are required. Restart and look for:

    Version 6.12 | Latest gas: VEN / ART / CAP

Existing schemas 1 through 11 migrate to schema 12 with the same key and all
existing fields and settings preserved. The new blood_gas field initially is
None. The next successful save writes schema 12. Do not downgrade partial files.

## P-block gas table

Paste the paired p dividers around the Epic table headed Results from last 7
days, including Lab, Units, dates and times. No additional heading is required.
The application reads wrapped date/time headers as in your new SmartPhrase.

The printed lab area shows one horizontal gas summary with VEN, ART or CAP,
its collection date/time, and only the supplied values from that specimen in
that column. It chooses the newest explicitly displayed gas by source timestamp,
not the order of the specimen types and not a preference for arterial results.
Supported specimen-qualified rows include pH, PCO2, PO2, HCO3, base excess and
oxygen saturation. Units and source flags remain unchanged. No dose, lab value,
time, specimen label or missing component is calculated.

Empty cells, -- and < > are not measurements. A newer incomplete gas remains
incomplete, without borrowing pH, PO2 or another value from an older column.
Untyped corrected PO2 and the example ISTAT deficit percentage fields are not
substituted for specimen-specific PO2 or base excess. Their omission is noted
in the import screen. Hidden interval results cannot be recovered from < >.

If the latest date has missing collection times or different specimens tie at
the exact timestamp, source order is the explicit fallback. A notice appears
in the editor and a qualifier remains in the printed gas title. This is not a
claim that the source proves which tied result is newest.

## Re-pasting and review

P alone updates gas results without replacing medications, other labs, vitals,
room information, or notes. A successful P replaces the prior automatic gas
snapshot. An included empty or no-results P clears the automatic gas display.
Omitting P preserves that room's previous P snapshot. Always include P again
when you need the gas to reflect the new source report.

Once P is supplied, it takes precedence over any old G-block gas rows, even
when the P result is empty. Old G values never fill a missing P field. For a
saved handoff that has never received P, one legacy gas may be shown using the
latest dated specimen group. Its label says legacy G, same-draw unverified,
because dates alone cannot prove a common draw or exact collection order.
Re-paste P to use the timestamped matrix instead.

Labs / Vitals now includes Latest blood gas and an expandable list of retained
gas columns. Edit their dates, values or source units, or exclude a gas from
selection. Older columns stay in the encrypted snapshot for review but do not
print. The editor's latest selection, PDF, HTML, plain text and Print all use
one shared selection rule. Room autosave includes pending gas edits.

The supplied examples/synthetic_latest_gas.txt is a synthetic practice paste.
examples/latest_gas_preview.pdf shows the new layout. Sample-loading buttons
have not been added back to the app.

## Validation and privacy

See TEST_REPORT.md for actual checks. The printed preview is synthetic. No
user keys, patient records or deployment secrets are included. This update does
not change the host, encrypted archive path, access requirements, logging or
Git history retention. Downloads remain unencrypted. Use institution-approved
hosting and storage for clinical information. No live deployment or private
handoff-store connection was tested here.

## Existing features retained

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

Schema 12 adds the independent P-block blood-gas snapshot. Existing infusion
display preferences and canonical room labels are preserved. Schemas 1 through
11 migrate on load with the existing key. The next successful save writes
schema 12 to the same encrypted-data/handoff-v1.enc path.
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

