# PICU Handoff 6.21: One DVT Prophylaxis group

Complete ZIP update. No direct repository changes were made.

## Installation

Save open work, extract PICU621.zip, and open
PICU_Handoff_v6_21_DVT_Grouping. Copy all contents to the existing
app-code repository, replacing matching files. Keep app.py at the root.
Restart the deployment and refresh the browser.

Keep the current Streamlit Secrets, password, encryption key, token, private
data repository, mappings and hidden-medication rules. Do not run the secrets
generator. No new dependencies or storage-format changes are required.
Schema 17 remains unchanged.

Sidebar: Version 6.21 | Unified DVT Prophylaxis group

## DVT medications stay together

Respiratory Infusions and Heme Infusions use the same emphasis as neurologic
Infusions and CV Infusions: bold heading, bold medication/formulation name,
bold and underlined explicit Dose, and a separate recorded pump rate when it
differs. With a blank Dose, an available recorded rate is emphasized instead.
No dose, route, rate, frequency, unit or medication instruction is inferred.

Respiratory vital signs, device settings and the Theophylline level retain their
existing priority above medications. Continuous IV orders mapped to Respiratory
and continuous nebulized/inhaled orders in that section enter Respiratory
Infusions automatically. Scheduled and PRN nebulized treatments stay separate.
This is a display grouping, not a change to the recorded route.

All medications assigned to DVT Prophylaxis now remain under one top-level
DVT Prophylaxis heading. This includes qualifying heparin and cangrelor infusions,
enoxaparin injections, and any other orders explicitly assigned to that category.
The infusion name and ordered dose stay emphasized within this group, while
non-infusion entries use the usual compact medication format. The source order
within the group is retained. No extra Heme Infusions heading is printed for
these DVT medications and no order is duplicated.

Unrelated hematology infusions still use Heme Infusions only when such orders
are present. Existing DVT eligibility and manual override rules are unchanged.
The heading does not establish a clinical indication or prophylactic dose.

Product names containing infusion or infusion syringe do not by themselves
establish continuous delivery. The automatic rule requires a continuous
frequency and supported delivery route. PRN and one-time orders are not
classified automatically. Unknown delivery patterns retain their ordinary
medication display unless the user explicitly chooses Infusion.

The Medications screen has Respiratory display and Heme display controls using
Automatic / Infusion / Other medication. Exact formulation, route and frequency
choices are remembered through the existing encrypted infusion settings.
Admin > Infusion display choices remains available without a handoff open.
No new medication-to-system mapping is invented by the new display logic.

Held/start labels, sequence prefixes, hidden/excluded status and custom handoff
wording are preserved. Dosing Weight parentheticals remain hidden only in handoff
output, not erased from the stored medication records. Existing saved handoffs
receive the new layout on reopening or printing without re-pasting.

The new groups are used in the editor, preview, PDF, HTML, text and Print all.
Plain text keeps the headings but cannot display font emphasis. Long content
continues on another page instead of being clipped. The rest of the compact
layout, save times, room-switch autosave and error-review workflow is retained.

See DVT_GROUPING_UPDATE.txt and TEST_REPORT.md. The current synthetic preview is
examples/dvt_grouping_preview.pdf. No real patient example is bundled.

## Last saved date and time (retained)

The room heading shows the last confirmed save date and time for that handoff,
in Eastern time with seconds and EST/EDT. A separate status says Saved,
Unsaved changes, or Not saved yet. Custom rooms follow the same rules as presets.
The Save status for all rooms expander shows every preset and custom room.

Print all shows the most recent handoff save in the loaded archive beside
Save all open handoffs. A table above the downloads shows each selected room,
its last confirmed save, and whether that printout contains unsaved draft edits.
Downloading still does not save. Use Save all open handoffs to persist edits.

Manual Save, Save all, and room-switch autosave use the existing per-sheet
updated_at field. A new save time is displayed only after the storage operation
succeeds. Failed or conflicting writes do not advance it. Imports, edits, Admin
rule saves, and print/export timestamps do not masquerade as handoff saves.
A room switch without changes does not write a new save or advance its time.

A new patient handoff does not borrow the previous occupant's save timestamp.
A stored record with a missing/invalid/unspecified-timezone timestamp shows
Save time unavailable rather than guessing a time. Session-only testing is
explicitly labeled and does not claim a persistent GitHub save.

Times reflect the most recently loaded archive and successful writes in the
current session. They are not a live monitor of colleagues' activity. Use
Reload saved archive to see another session's saves. Existing conflict checks
and your open drafts remain in place. The timestamp does not identify a user.

Previously saved timestamps are visible immediately after update. No re-paste
or new save is needed to display a timestamp already in the archive. The
printed handoff layout and its separate Print prepared timestamp are unchanged.
The last-save controls and storage behavior are unchanged in 6.21.
Clinical parsers remain unchanged. Infusion display and export formatting changes
are described above. See SAVE_STATUS_UPDATE.txt and TEST_REPORT.md.

## Theophylline level (retained)


THEOPH in the G / LABS block is now shown once in RESP as Theophylline level,
using the latest included source result. It appears after respiratory vitals
and support settings, before notes and medications. Its date, optional time,
flags and any supplied units are retained. Missing data stays missing, without
inferred units, reference ranges or dose changes.

Older rows remain editable and excludable in Labs / Vitals. Existing stored
THEOPH rows also use this placement without reimporting. A new G block replaces
all G labs, so include the other results needed when repasting G. Omitted G
keeps the prior snapshot. Existing error-recovery warnings are unchanged.

See THEOPHYLLINE_UPDATE.md for ordering and import details. The complete prior
functionality remains included. The CBC, blood-gas, medication, vital-sign,
ventilation and recurring-order parsers are unchanged.

## Automatic display groups

| Column | Heading | Rule |
| --- | --- | --- |
| HEME | DVT Prophylaxis | Enoxaparin and cangrelor. Heparin only when its ordered Dose explicitly contains a numeric Units/kg/hr value or range. |
| FEN / GI | Diuretics | Bumetanide, chlorothiazide and furosemide. |
| NEURO | Fever Control | Acetaminophen and ibuprofen, scheduled or PRN. |
| NEURO | PRN | Fentanyl, midazolam, ketamine, morphine and hydromorphone with PRN/as-needed frequency. |
| NEURO | Paralytic PRN | Rocuronium, cisatracurium and vecuronium with PRN/as-needed frequency. |
| CARDIAC | CV Infusions | Continuous parenteral orders mapped to Cardiovascular, or an explicit infusion display choice. |

These are the user's display labels, not inferred clinical indications.
In particular, the DVT Prophylaxis heading does not determine whether an
antithrombotic is being used for prophylaxis or whether its dose is prophylactic.
The Units/kg/hr condition applies only to heparin, not enoxaparin or cangrelor.
Heparin flushes, catheter locks, irrigation mixtures and mL/hr carriers do not
qualify by their name, concentration or Last Rate. The actual Dose field is used.
No dosing values, concentrations, rates, indications or missing values are
calculated, substituted or supplied by a group.

Known held/start/sequence prefixes do not interfere with matching. Those labels
remain on the handoff. Orders remain separate, even when names repeat. Hidden
and excluded orders remain hidden/excluded. Each visible order appears once.
Custom handoff wording stays authoritative. The original medication records and
existing system mappings are kept, even when an automatic display group takes
precedence. No new broad drug-name mapping is silently written.

## Visual order and emphasis

NEURO: imported observations first, then Infusions, PRN, Paralytic PRN,
Fever Control, separate notes and remaining medications. Empty headings do not
print. Infusions replaces the old all-capitals heading.

CARDIAC: vitals remain at the top, then any lactate, then CV Infusions, separate
notes and remaining medications. CV infusion names are bold. The explicit Dose
is bold and underlined, like the neurologic infusions. A different recorded pump
rate stays on a separate line. Dose units are not confused with pump-rate units.
PRN syringes are not inferred to be continuous infusions from the product name.

FEN / GI: Intake/Output/Net remain first, followed by GI prophylaxis,
Bowel Regimen, Diuretics, separate notes and remaining medications.

HEME: one DVT Prophylaxis group contains both infusion and non-infusion members.
Infusions are emphasized without leaving that group. Unrelated Heme Infusions,
if any, follow it, then separate notes and remaining medications. No order is
duplicated.

RESP: vitals, support settings, Theophylline level when present, Respiratory
Infusions, separate notes and remaining respiratory medications.
Existing vital-sign positioning is preserved.

The same grouping drives the editor previews, PDF, HTML, text and Print all.
PDF and HTML carry the bold formatting. Plain text carries the group names.
Compact one-page fitting and safe continuation pages remain supported. Infusion
names and their doses are kept together where feasible rather than clipped.

## Overrides

In Medications, use Medication group to choose Automatic, one of the four
special groups, or No special grouping. Use FEN/GI display for the GI groups,
including Diuretics. Neuro and CV display controls share the existing infusion
setting. Changing the system away from an automatic destination disables the
conflicting group for that formulation, route and frequency.

Choices save through the existing encrypted archive. Admin now includes
Medication subgroup choices as well as FEN/GI display choices and Infusion
display choices. They remain editable when no handoff is open. Failed saves do
not claim persistence or alter the draft. Room autosave captures pending choices.
Hidden-medication controls remain separate and take precedence over all groups.

Automatic defaults apply when displaying existing saved orders. Re-pasting is
not required just for these headings. Saved overrides can still change their
presentation. Updated shared rules affect open drafts and subsequent imports,
not the historic content of closed saved handoffs without a save/reimport.

## Calcium

The existing lab parser already recognizes CA as calcium. Regression tests now
explicitly verify CA beside Mg and Phos beneath both latest and preceding BMP
trees, with the recorded dates and abnormal flags. Calcium is not calculated
from albumin and is not substituted for ionized calcium. No result is invented
when CA is absent. Paste a full G block including CA to add a newly supplied
result. The G block replaces its previous lab snapshot, so include the other
G-block results you still need.

CBC Q selection, latest gas P selection, ANC/ALC, specimen/time handling and the
lab drawing code are unchanged. Their source files compare byte-for-byte with
the original Version 6.16 package.

## Testing and example

See TEST_REPORT.md for executed checks and limitations. The synthetic example
in examples/synthetic_medication_groups.txt is a layout fixture, not a treatment
plan. It does not add example buttons back to the daily screen. The packaged
examples/medication_groups_preview.pdf is a one-page landscape preview. Its
milrinone and dexmedetomidine were mapped to Cardiovascular and Neurologic for
that illustration. Other requested name-based groups work without new mappings.

Room-change autosave, custom-room removal, P-prefixed presets, partial-import
recovery, encrypted technical error logging, timestamping, and all prior
features remain. No user handoff archive, deployment secret or live storage
connection was accessed for this update.


## Historical release notes

Earlier version-specific headings and installation instructions below are historical. The Version 6.17 instructions above take precedence.

# PICU Handoff 6.16: Partial imports and shared error review

Complete ZIP update. No direct repository changes were made for this release.

Save your current handoffs, extract PICU616.zip, and open
PICU_Handoff_v6_16_Import_Recovery. Upload all its contents to the existing
application code repository, replacing matching files. Keep app.py at the root.
Include the new import_review.py and error_store.py modules. Restart the app.
Keep deployment Secrets, password, encryption key, GitHub token, private data
repository, medication mappings and other saved settings. Do not run the secrets
generator. No new dependencies are required. The next save uses schema 16.

Sidebar: Version 6.16 | Partial imports and shared error review

## Current behavior

Ordinary order comments such as Peripheral no longer trigger malformed-divider
errors. A pipe-separated CBC cell is retained but excluded for review, not
replaced with its lowest value. Valid sections continue importing when another
section fails. Failed R orders are hidden from the handoff, and other failed
sections retain previous values with a visible not-updated warning. Review
warnings persist in saved handoffs and all print/export formats.

The Import errors workspace automatically stores sanitized, encrypted technical
reports in a separate folder of the same private repository. Teammates using the
same app can refresh the shared log, resolve or reopen reports, and download a
technical report. Failed log saves are clearly marked and retryable, without
throwing away the handoff. No clinical paste, values, room, name, MRN or staff
identity is stored in the technical journal.

Read IMPORT_RECOVERY.md for exact omission, retention, concurrency and privacy
behavior. See TEST_REPORT.md for checks actually performed. The bundled
examples/synthetic_import_recovery.txt is not a patient record. The two-page
examples/import_recovery_preview.pdf shows both partial CBC and skipped orders.

## Historical release notes below

These notes describe earlier versions. In particular, older statements that one
bad section cancels an entire import are superseded by Version 6.16 above.

# PICU Handoff 6.15: Intake/output and FEN/GI medication groups

This is a complete ZIP update to Version 6.14. No repository was changed directly.

## Update the existing app

Save open work, extract PICU615.zip, and open PICU_Handoff_v6_15_FEN_GI.
Replace the application files in your code repository with all the contents of
this folder. Keep app.py at the root and include fluid_balance.py and fen_gi.py.
No dependencies have changed. Restart your existing Streamlit deployment.

Keep Streamlit Secrets, your password, encryption key, GitHub token, private data
repository and saved medication mappings. Do not run create_secrets.py or the
secrets notebook again. The next save writes schema 15. Do not downgrade the
application after that save without restoring a compatible earlier archive.

Sidebar: Version 6.15 | Intake/output and FEN/GI medication groups

## S-section totals

Paste the complete SmartPhrase or only a complete paired S block. The S block
may begin with Intake/Output Summary rather than an extra heading. Click Create /
update handoff. Its recorded Intake, Output and Net print at the very top of FEN/GI.
Only S is imported for fluid totals. H is not used as a fallback and is not added
to S, even if both sections contain the same totals.

Zero, signed net values, decimal precision and supplied units are kept. Net is
not recalculated. A missing value displays --, not zero. The source period,
summary time and last-filed time are retained in the editor. Conflicting totals
or an unreadable nonempty S block stop the proposed import without replacing
the previous handoff. Nothing is silently dropped to make a malformed paste fit.

An omitted S keeps the old totals. An included empty S clears them. Re-pasting S
replaces only its snapshot and does not touch separate notes, medications, labs,
CBC columns, blood gases, cultures, vitals or R orders.

Edit the totals under Edit handoff > FEN / GI. The optional Show intake/output
totals control hides that snapshot from the output without deleting its values.
Room-change autosave, encrypted storage, single-sheet printing and Print all
include the edited snapshot. As before, paste text must first be imported with
Create / update handoff. Unsubmitted paste text is not an imported draft.

## Medication groups

The user-requested automatic name rules are:

- GI prophylaxis: famotidine, omeprazole, pantoprazole.
- Bowel Regimen: docusate, lactulose, polyethylene glycol, glycerin suppositories,
  and sennosides.

These are display groups chosen by the user, not inferred treatment indications.
They recognize the generic name at the start of a formulation after known held,
start-date and sequence annotations. They do not guess unlisted brand-only names,
match drug-name substrings, or classify topical glycerin as a suppository.

Matching visible entries appear automatically in FEN/GI, without requiring a new
system mapping. Existing stored system mappings and source medication fields are
retained. Each order appears once. Different doses and schedules remain separate.
Hidden and excluded entries stay omitted. Held/start/sequence labels, prescribed
doses, routes, frequencies, recorded rates and custom wording remain intact.
The existing output-only removal of (Dosing Weight) still applies.

The printed order is Intake/Output/Net, a separator, GI prophylaxis, a separator,
Bowel Regimen, separate FEN/GI notes, and remaining FEN/GI medications. Empty groups
are omitted. Group headings are bold in PDF and HTML.

The Medications tab has a FEN/GI display choice for these entries. Automatic uses
the listed defaults. GI prophylaxis or Bowel Regimen explicitly chooses a group.
No GI grouping returns the order to its saved system assignment. Selecting a
different system also disables automatic GI grouping for that formulation,
route and frequency. The choice is remembered separately from system mapping
and hiding rules. Saved overrides are editable in Admin > FEN/GI display choices,
including without an open handoff. Returning an override to Automatic removes it.

Previously saved medication rows adopt this grouping when viewed or exported.
They do not need to be re-pasted. New S totals do need a paste/import. Separate
manually typed notes are not rewritten or deduplicated.

## Practice and limits

examples/synthetic_fen_gi.txt is a practice paste with no patient record.
examples/fen_gi_preview.pdf shows a one-page synthetic handoff. No sample-loading
buttons have been reintroduced to the screen. The compact print layout still
uses continuation pages when needed rather than clipping content.

Storage/access/privacy protections and limits are unchanged. Use an approved
hosting and storage arrangement. Exports are unencrypted. The original paste
enters server memory and is not certified de-identified. Refer to the existing
security documentation and institutional policies.

See TEST_REPORT.md for checks actually executed and deployment limitations.

## Prior release details

# PICU Handoff Version 6.14: recurring orders in Labs/Imaging

This complete ZIP updates the existing web app. No local Python reinstall or new package dependencies are needed.

Save your open handoffs. Replace the application code with every file in this package, keeping app.py at the repository root. Include recurring_orders.py. Keep your existing Streamlit Secrets, password hash, encryption key, token, mappings and private data repository unchanged. Do not run the secrets generator again.

Paste the paired R section or the complete SmartPhrase and click Create / update handoff. The Labs/Imaging column shows selected scheduled tests, their intervals and their stated Number of Occurrences. The editor has a Labs/Imaging tab for reviewing candidates, duplicate choices and corrections. Room-change autosave and Print all include these orders.

Duplicate test plus schedule: keep the largest count, not the sum. One-time and STAT orders are excluded even when their Timing starts with Recurring. Counts are copied from the source and are not remaining-draw estimates. CMP is excluded from the requested BMP-only filter, not relabeled as BMP. CBC/gas/result parsing is unchanged.

See RECURRING_ORDERS_UPDATE.md, START_HERE.html and TEST_REPORT.md. examples/synthetic_recurring_orders.txt is a practice paste. No sample-load buttons were added back to the daily screen.

## Prior release details

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

