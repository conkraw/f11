# PICU Handoff 6.13: Q-section CBC, ANC / ALC and medication display

Complete ZIP update. No direct GitHub changes. Save open work, extract PICU613.zip,
and upload the contents of PICU_Handoff_v6_13_CBC into the existing app code
repository. Replace matching files and keep app.py at the root. Include cbc.py,
output_text.py and all supplied modules. Keep deployment Secrets, the password,
encryption key, token, private data repository and medication mappings unchanged.
Do not rerun the secrets generator. No new dependencies are required.

Sidebar: Version 6.13 | Q CBC, ANC / ALC and cleaner medication output

## Q is separate from P and G

Paste the complete Epic CBC table inside paired q dividers, including Lab, Units,
all collection dates/times and every value column. Wrapped date/time headers and
an uppercase letter in a divider are supported. No extra CBC heading is needed.

The original CBC fishbone layout remains. The two latest documented CBC-containing
columns are selected by date/time. Each tree keeps results from its own column.
A gas-only Hct/ISTAT column does not displace a standard CBC column. A missing
component is shown as -- rather than filled from another time. Columns do not
prove specimen identity; they preserve the exact association Epic supplies.

Standard HEMOGLOBIN/HGB has priority over explicitly labelled ISTAT hemoglobin
across the included Q snapshot. When any included standard hemoglobin exists,
ISTAT hemoglobin is not printed, even if it is newer or the second standard value
is absent. Only when there is no included standard hemoglobin may ISTAT values
be selected, and the node is labelled Hgb (ISTAT). No method is guessed for
unlabelled legacy HGB rows. Source ISTAT entries remain editable and encrypted.

## ANC and ALC below the CBC

The latest absolute neutrophil result is selected across NEUTROS ABS, NEUTROABS,
ANC and supported explicit absolute-count aliases. The latest absolute lymphocyte
result is selected across LYMPHS ABS AUTO, LYMPHSABS, MANUAL ABSOLUTE LYMPHOCYTE CV
and supported explicit absolute-count aliases. Recency, not automatic/manual
preference, decides. Equal timestamps keep source order and differing ties produce
an editor notice. A zero result remains a zero. Percentages are never converted.

The labels are ANC and ALC. They print once, below the latest CBC tree, with their
own dates/times and supplied units. They may be older than the CBC and are not
relabeled with its date. If a count is not supplied, its line shows -- without a
fabricated date or unit. The preceding tree retains its own MCV when supplied.

Q takes precedence over CBC rows in G, including when Q is explicitly empty.
An omitted Q preserves the existing Q snapshot. An empty/no-results Q clears it.
A new Q replaces rather than appends. G updates do not erase an existing Q.
Legacy G-only CBCs still work until Q is supplied, with per-component rather than
same-column selection. The two BMP trees and other lab routing are unchanged.

Review retained source labels, results, units and dates in Labs / Vitals under
CBC / absolute counts. Changing a column's date updates that whole column.
Individual results can be excluded or restored without deletion.

## Gas compatibility

P remains a separate snapshot with the same newest-specimen/column selection.
Existing P formats and same-column protection are retained. This release also
recognizes explicit POCT PCO2, VENOUS / POCT PO2, VENOUS labels and BASE EXCESS,
VENOUS, plus their arterial/capillary equivalents. An unlabelled PH can join a
column only when that exact column has one explicitly identified gas specimen
from another supported analyte. This association is noted in the editor. PH is
not assigned when the type is ambiguous. No values are borrowed across columns.

The exact Epic message No lab exists for component is accepted as no gas data,
not as a malformed table. Unknown nonempty table layouts or conflicting values
still stop the import without altering any of the existing handoff. Date-less
or exact-time gas ties retain the existing source-order warnings.

## Medication output only

The literal parenthetical phrase (Dosing Weight) is removed from generated
medication wording in the preview, PDF, HTML, text and Print all, including
neurologic infusions and custom medication wording. Dose units such as mg/kg
and mcg/kg/hr, order-specific qualifiers, future dates, held labels, formulation,
route, frequency and rates are kept. No dose is recalculated.

The medication editor and encrypted records retain the original phrase. Mapping
and hiding keys are untouched. The separate demographic Dosing weight field is
not removed. Manual non-medication notes are not rewritten. Existing handoffs use
this output-only cleanup immediately, without re-pasting their medications.

## Checks and limits

Moving the CBC into its own timed section is reasonable, but no parser can
recover data Epic hides with < > or infer missing source details. Malformed rows,
column-count mismatches and ambiguous headers reject the entire proposed import
rather than silently mixing columns, guessing values or erasing the last handoff.
All previous fields remain available if the proposed import is rejected.

See TEST_REPORT.md for executed checks. examples/synthetic_cbc_smartphrase.txt
and examples/cbc_preview.pdf are synthetic. No user records, deployment secrets
or real encryption keys are included. The actual hosted Streamlit interface and
private GitHub store have not been exercised. Use existing institutional hosting
and storage controls. Exported files are not encrypted.

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
qualifiers are stored unchanged. Only the literal (Dosing Weight) qualifier is omitted from medication output. User-supplied custom wording remains authoritative.

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

Schema 13 adds an independent cbc snapshot. Schemas 1 through 12 migrate on load
using the existing encryption key. No medication source wording, prior gas, lab,
manual note, room ID or saved mapping is replaced. cbc is initially None, enabling
legacy G-block CBC display until a Q block is supplied. The archive path remains
encrypted-data/handoff-v1.enc. The next successful save writes schema 13.
Do not downgrade individual files after saving. Keep the complete package together.

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

