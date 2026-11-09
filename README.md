# Version 6.38: mode-specific ventilator summaries

Built directly from Version 6.37, retaining its Version 6.35-based print layout.
Read VENTILATOR_UPDATE.md for the new C-block patterns and their exact display rules.

## Install this release

Extract PICU638.zip and upload the contents of PICU_Handoff_v6_38_Ventilator
into the existing application code repository, replacing matching files.
Keep app.py at the root and include ventilator_modes.py. Restart and refresh.
Keep existing Secrets, both passwords, encryption key, mappings, BMI reference
data and private storage. Do not rerun the generators. No new dependencies.

Look for: Version 6.38 | Mode-specific ventilator summaries

Existing saved fields open unchanged. Re-paste the complete C and D sections
or full SmartPhrase to import the newly available measurements and home-vent
limits. New labels cannot be recovered from an older saved record that never
captured them. Do not downgrade after saving the expanded ventilator fields.

The source mode and raw settings stay available in Edit ventilator values.
Vt Insp is TVi, not TVe. Set PIP is not calculated from observed PIP or PEEP.
Pmin-based Home Vent identification and PRVC naming are local display rules.

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
as such. Session-only mode clearly says the time is session-only, not a GitHub
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
pages rather than cropping clinical content. Preflight reports the actual PDF
page count and chosen size. The HTML preview can paginate differently.

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
