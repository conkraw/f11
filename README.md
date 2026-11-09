# Version 6.39: medication categories and simpler printing

Built from the delivered Version 6.38 package. The Version 6.35-derived compact
layout, Version 6.37 difficult-airway feature, and Version 6.38 ventilator rules
remain. There is no Version 6.36 font picker.

## Interface changes

The routine PDF layout table (Room, PDF pages, Body text, Layout) and its explanatory
caption are removed. A warning still appears if the actual PDF exceeds the chosen
page target. The PDF renderer still fits pages and never drops clinical content.

Only PDF handoff download buttons remain in Preview / print and Print all.
The on-screen HTML preview is retained. The internal HTML/text exporters remain
for compatibility and automated tests, but no longer have handoff download buttons.
SmartPhrase and user-guide downloads are not affected.

The pictured synthetic-data/approval sidebar notice is removed. Built-in routine
status messages use shared storage instead of naming the storage provider.
Save times, unsaved-state warnings, access controls, session limits, encrypted
storage, conflict checks, setup documentation and error reporting still work.
Removing a label does not change or strengthen security. Hosting approval and
local data-handling requirements remain described in the setup documentation.
Existing published custom instructions are not silently overwritten.

## New automatic display groups

Respiratory / Antisialorrhea Agents:
scopolamine and glycopyrrolate.

Cardiovascular / Antiarrhythmics:
esmolol, amiodarone, procainamide, lidocaine (IV infusion only), mexiletine,
flecainide, propranolol, sotalol, diltiazem, verapamil and digoxin.

Cardiovascular / Antihypertensives:
enalapril, metoprolol, amlodipine, lisinopril, hydrochlorothiazide, clonidine,
atenolol, carvedilol, losartan, valsartan, captopril, labetalol, nifedipine
and isradipine. Repeated names in the request are represented once.

Cardiovascular / Inotrope Infusions:
continuous IV milrinone, dobutamine, epinephrine and dopamine.
Rescue boluses and nebulized epinephrine are not moved into this infusion group.

Cardiovascular / Vasopressors:
IV norepinephrine, vasopressin and phenylephrine. Nasal and ophthalmic products
are not automatically moved to this group.

Cardiovascular / Adrenocortical Support:
systemic hydrocortisone. Topical/rectal local preparations are not automatically
moved to this group.

Cardiovascular / Vasodilators:
nitroglycerin, nicardipine, hydralazine and enalaprilat. Enalapril and enalaprilat
are kept distinct. Nitroprusside was not added to this requested default list and
keeps its prior mapping/generic infusion grouping unless assigned manually.

FEN/GI / Endocrine Medications:
levothyroxine, insulin (including continuous infusions and Lantus), and metformin.
Synthroid and Levoxyl name prefixes are also recognized. Subcutaneous Lantus
orders remain regular medication entries, not continuous infusions.

Canonical name matching includes the requested spelling variants glycopyrollate,
nicadipine, nitroglycerine and enalapriatat. Matching does not rewrite the original
source medication/formulation name, dose, route, frequency or administration rate.

## Rendering and overrides

The cardiovascular groups appear in the order requested, after vitals, pacemaker
information and cardiac labs. An infusion stays in its category with the existing
bold medication name and emphasized Last Admin rate. It is not duplicated under
CV Infusions. Unclassified CV infusions keep that general group.

Respiratory Infusions remain available. Antisialorrhea Agents appear separately.
Endocrine Medications appear in FEN/GI after Antiemetics, before separate notes
and other FEN/GI medications. Insulin infusions use the same emphasized rate style.
Empty headings do not print. All existing hidden/excluded orders remain hidden.

Choose a medication's system and Medication group to override a default.
For Endocrine Medications use FEN/GI display. Choices are remembered in shared
settings and editable in Admin. A deliberate group override takes precedence
rather than duplicating the order. For example, select Neurologic for clonidine
when that is the intended placement. Its new automatic cardiovascular grouping
is then disabled for that formulation, route and frequency.

These categories are user-defined display labels, not inferred indications.
No new diagnosis rules, medication recommendations, dose conversions, or changes
to the Last Admin selection logic were added.

## Install

Extract PICU639.zip and open PICU_Handoff_v6_39_Medication_Categories.
Upload its contents into the existing application code repository, replacing
matching files. Keep app.py at the root. Restart the deployment and refresh.
Keep the existing Secrets, both passwords, encryption key, medication mappings,
BMI reference data and private data repository. Do not rerun setup generators.
No dependencies or new secret fields are required.

Look for: Version 6.39 | Medication categories and simpler printing

No re-pasting is needed to group already captured medications. The new defaults
are applied when the saved handoff is displayed. Explicit grouping overrides
remain authoritative. Existing archive values are not rewritten during display.
Schema remains 26, but older releases do not understand the new group choices.
Do not downgrade after saving one of those choices without restoring a compatible
backup. Back up the current code and encrypted archive before updating.

See TEST_REPORT.md for exactly what was tested. No live deployment or private
repository was modified or tested in this work.


## Features retained from Version 6.37

## Handoff screen: published SmartPhrase time

The Handoff workspace shows the date/time of the loaded, successfully published
SmartPhrase and instructions above the room selector, in Eastern time (EST/EDT).
It uses the shared guide's publication timestamp, not the app release date,
patient-save time or print time. Saving the guide in Admin republishes that guide
and its SmartPhrase. A failed save does not advance the displayed publication.
No published source means "not published yet", not an invented date.

Use Refresh SmartPhrase publication to load the current shared version. With
shared storage, Handoff also checks on the next rerun after 30 seconds. This is
not background polling. If refresh fails, the last loaded timestamp is labeled
as such. Session-only mode clearly says the time is session-only, not a shared
publication. The published guide's actual source and custom instructions are
not changed by installing this package.

## Printed layout

The Labs/Imaging column is removed. Seven columns remain: Patient, Neuro,
Respiratory, Cardiovascular, FEN/GI, Hematology and Infectious Disease.
Recurring orders and Labs notes remain stored and editable in the app but do
not print as a column. Existing medications mapped to Labs move to the printed
Other Medications band so the removed column cannot silently lose an order.
Their stored mappings are not changed.

The starting body font is 8 pt instead of 7.2 pt. The 6.35 automatic page-fitting
approach remains, including its 6.5-pt lower limit and one/two-page target.
There is no per-user numeric font control. Very long handoffs can still span
pages rather than cropping clinical content. The renderer checks the actual PDF
page count internally. The HTML preview can paginate differently.

CBC/BMP tree titles, latest/preceding captions, and the explanatory paragraph
are removed. Hgb/Hct/electrolyte labels, values, abnormal flags, dates and times
are kept. Other laboratory summaries retain their panel/specimen label and
results but omit selection commentary. The empty "Lab Results / Trends" title
and an entirely empty lab band do not consume paper.

"No results found", "No lab exists", and "No data recorded" source messages
are omitted from handoff output. Their original notes remain stored for review.
True result values and unrelated source comments are not discarded.

Lactate/theophylline/CK date-only window estimates keep the recorded date but
omit timing-unverified annotations. Selection rules and actual date cutoffs
are unchanged. No collection time is invented.

Unambiguously negative No growth results print as NGTD, including preliminary
or in-process variants. Repeated negative status variants in the same display
group print NGTD once. Dates and specimen sites remain. Positive organism names
stay emphasized. Original culture statuses remain in the editor and archive.

Import errors are displayed in the app and continue to use the existing
technical error journal. They do not print on PDF, HTML, text or Print all.
This is presentation only, not error acknowledgement. Existing rules suppress
failed feeding/diet/device/pacemaker/order snapshots, and a failed weight import
still disables mL/kg calculations. Other retained values can still be present,
so review the in-app import warnings against Epic before sharing a handoff.

## Difficult airway

A new Difficult airway tab follows Problems. It is available to normal signed-in
users and does not require the separate Admin password.

Select "This patient has a difficult airway" to enable a highlighted full-width
DIFFICULT AIRWAY section at the end of the handoff. The short form captures:
- Bag-mask ventilation: unknown/not assessed, yes, yes with difficulty, or no.
- Tracheal tube passage: unknown/not assessed, not difficult, difficult, or unable.
- Documented view/grade and technique/equipment used.
- Optional successful route/tube details, brief issue, agreed team plan/contact,
  and assessment date/time or source.

Only entered information is summarized. Unknown/unanswered responses are not
turned into normal findings. Enabling the section without answering questions
prints "Details not entered." No difficulty, equipment, view, or rescue plan is
inferred from diagnoses, devices or medication orders.

Save handoff or switch rooms to persist the information in the existing encrypted
archive. Each room/new patient has its own data. Turning the switch off omits the
entire alert while retaining that patient's answers. Start blank for new patient
and Clear all handoffs remove those answers. Normal SmartPhrase imports do not
erase manually recorded airway details. New-patient reset is therefore important
when reusing a room.

No live deployment or private repository was changed or tested. See TEST_REPORT.md.
