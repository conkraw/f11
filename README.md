# Version 6.35: weight and height import fix

## What caused the Weight warning

The I section includes measured weight, dosing weight, Z-score, BMI, height,
and BSA. In v6.34, a height with a parenthetical feet/inches equivalent was
rejected by the height validator. That failed the I-section import even though
the weight entries themselves were readable.

The app retains previous values when this happens. Retained does not mean
updated or verified. With no previous value, the field remains empty. Other
successfully imported sections still update. Per-kilogram fluid calculations
remain suppressed while the I section has an import warning.

## Fix

Epic height values such as `120 cm (3' 11.24")` now import as `120 cm`.
Both `Height:` and `Length:` headings work, including repeated or split headings.
The primary recorded value is kept, without calculating height from BMI or weight.
Recognized feet/inches equivalents may use straight quotes, typographic quotes,
prime symbols, or spelled-out units. Equivalent heights must agree within the
rounding precision of the stated measurements. Unknown annotations and conflicting
values are not silently removed or accepted.

The review label now says `Weight / measurements` so a failed height or BSA
import is not misleadingly described as just a weight problem. Genuine errors
still preserve previous values and show the warning. No warning is automatically
acknowledged or hidden. A successful I reimport clears only the I warning.

## Install and refresh

Save open work. Extract PICU635.zip. Upload the contents of
PICU_Handoff_v6_35_Weight_Import into the existing application code repository,
replacing matching files. Keep app.py at the root. Restart and refresh the app.
Look for `Version 6.35 | Weight and height import fix` in the sidebar.

Re-paste the complete paired I section or full SmartPhrase for the affected room.
Click Create / update handoff, check the weight, dosing weight and height against
Epic, then Save handoff. Installing the fix cannot recover previously rejected
values unless you re-paste them. No SmartPhrase wording change is required.

Keep the existing Secrets, both passwords, encryption key, mappings, private
storage and public CDC BMI reference file. Do not rerun the setup generators.
No dependency or saved-archive schema changes are required.

Until installed, shorten a copied height line to just its verified metric value,
for example `Height: 120 cm`, and reimport the complete I section. This workaround
is for the pasted copy and does not require editing the patient's Epic chart.


---

# Previous release notes

# Version 6.34: week-old age parsing and flagged blood-count rules

## Age and sex

Epic's `Age:` followed by `5 wk.o.` on the next line is now accepted.
`Sex:` followed by `male` on the next line is also recognized. The handoff
places Age and Sex directly beneath Room, not in the diagnosis text.
Same-line metadata and existing years/months/days wording remain supported.
The abbreviated wk.o., wks.o., mo.o., mos.o., yr.o. and yrs.o. forms are
interpreted without changing their displayed wording. Infant ages do not
become an invented precise age in months for a BMI calculation.
BMI and its percentile remain hidden below age two.

## Problems

The compact Problems line now prints names without an automatically added
Possible prefix. It remains comma-separated, not a multi-line explanation.
Supporting observations and limitations remain in the Problems editor.
Removing a display qualifier does not change an item's review status, mark
it clinically confirmed, modify imported Diagnoses, or validate the diagnosis.
Saved hide and confirm choices and clinician-entered custom wording remain.

Two clinician-requested default rules were added:

- Asterisk-flagged hemoglobin below 11.5 g/dL produces Anemia.
- Asterisk-flagged platelets below 175 K/uL produces Thrombocytopenia.

Equality does not trigger either rule. A value without an asterisk does not
trigger the new asterisk-based rule. Existing L / LL / LOW handling remains.
The latest eligible CBC data are used, not the lowest historical value.
Standard hemoglobin still takes precedence over ISTAT, with ISTAT used only
when standard hemoglobin is unavailable. CBC trees are unchanged.

Matching source units are required. Numerically equivalent platelet units
such as 10^9/L are supported. Missing or unrelated units are not guessed or
silently converted. Patient-specific low-result limits, when explicitly set
in the Problems editor, take precedence over these defaults for that component.
These are configured workflow thresholds, not universal pediatric diagnostic
reference ranges. Check generated labels against the patient's clinical context.

## Install

Save open work. Extract PICU634.zip and upload the contents of
PICU_Handoff_v6_34_Age_Problems to the existing application code repository.
Replace matching files and keep app.py at the root. Restart the deployment
and refresh your browser. Re-paste the complete A section or full SmartPhrase,
click Create / update handoff, then Save handoff to repair a previously failed
age/sex import. The Problems display and thresholds apply to existing saved
eligible results without re-pasting.

Keep existing Streamlit Secrets, both passwords, encryption key, medication
mappings, private storage, and the public BMI reference file. Do not rerun the
setup generators. No new dependencies or archive schema changes are required.
No direct changes to a live GitHub repository are made by this package.


---

# Previous release notes

# Version 6.33: Last Admin infusion rates and Antiemetics

## Infusion rates

A continuous infusion with one explicit numeric rate in Last Admin now uses
that value as its emphasized dose-rate. This includes nitroprusside,
nicardipine and norepinephrine, as well as other continuous orders with an
explicit documented rate. The time from that field is displayed with it.

Synthetic illustration using the supplied nitroprusside row pattern:

    Last Admin rate: 6 mcg/kg/min [11/08/26 1016]
    Recorded rate: 2.52 mL/hr

The ordered Dose range 0.1-6 mcg/kg/min is retained in the editor and archive.
It is not printed as though it were the administered rate. The separate
Last Rate pump value is not converted into a weight-based dose. Units and
source numbers are copied, not calculated or compared to dosing limits.

The three named drugs, their supported name variants, and continuous orders
with explicit numeric dose-rate ranges show UNK if Last Admin has no usable
numeric rate. Other continuous orders retain the existing dose/pump display
when Last Admin contains only a quantity or an event such as Rate Verify.
PN total volume and lipid mass are not rates. Scheduled and PRN bolus doses
are not replaced with administration values.

Zero is a valid documented rate. An explicit Stopped, Paused, Held, Not given,
Not administered, or Discontinued event is labeled with its own wording.
The order stays in the handoff, while its older pump rate remains in the
editor rather than printing beside that non-running event as a current rate.
A stop event is not automatically interpreted as order discontinuation.

Multiple rate events or conflicting text in one Last Admin cell are not
silently merged or ranked. The app uses UNK for the named/range titration
orders until the source or the editable fields have been checked.

Medication details now include Last Admin rate, timestamp and status fields.
Changing a rate clears its old timestamp unless a new time is supplied.
These edits do not update Epic. Custom handoff wording continues to override
the automatic summary, so check or clear custom wording after a rate change.

## Antiemetics

Ondansetron and Zofran entries automatically appear under Antiemetics in
FEN/GI. Scheduled and PRN entries keep their dose, route and frequency. Hidden
and explicitly excluded entries remain hidden. Existing per-order grouping
choices take precedence. Other medications can be assigned using FEN/GI
display -> Antiemetics. The choice is remembered in the existing settings.

## Clipboard format

Canonical tab-separated Epic tables are unchanged. The explicit EN-space
clipboard format in the supplied sample is also supported using recognizable
route/frequency boundaries. Plain prose is never treated as a table. When a
single numerical rate cannot be assigned to Last Rate versus Last Admin,
it is not guessed, and a static warning explains the missing boundary.

## Existing handoffs and installation

Save open work. Extract PICU633.zip and upload the contents of
PICU_Handoff_v6_33_Infusion_Rates to the existing application code repository.
Keep app.py at the root. Replace matching files and include infusion_rates.py
and medication_columns.py. Restart and refresh the browser.

Keep current Secrets, both passwords, encryption key, GitHub token, mappings,
private data repository, and public CDC BMI reference data. Do not rerun any
key/password generators. No new Python dependencies are required.

The archive upgrades from schema 24 to 25 without changing existing room
fields or timestamps. New optional medication fields store only sanitized
Last Admin rate/status/time, not raw text or provider names. After saving
with v6.33, do not downgrade to an older application package.

Re-paste the full B medication section or the complete SmartPhrase, then
Create / update handoff and Save handoff. Old versions did not retain the
Last Admin value, so installation alone cannot recover it. A new B replaces
all medication rows and their administration snapshot. Omitting B preserves
existing medication information. No doses are carried between separate orders.

The infusion values are a chart snapshot, not a live pump connection.
See TEST_REPORT.md for verification and remaining limits.


---
Historical release notes follow.

# Version 6.32: age and sex below Room

Save open work. Extract PICU632.zip and upload the contents of
PICU_Handoff_v6_32_Age_Sex to the existing application code repository.
Replace matching files and keep app.py at the root. Restart and refresh.
Keep all current Streamlit Secrets, both passwords, the encryption key,
GitHub token, medication mappings, private data repository, and public BMI
reference data unchanged. Do not run setup generators. No new dependencies
or archive schema changes are needed.

The exact Epic line Age: 6 y.o. Sex: female is accepted in A, I, or N.
It prints as:

    Room: P4201
    Age: 6 y.o.
    Sex: Female

Admission and Diagnoses follow below. Explicit Age/Sex metadata is removed
from A before diagnoses are assembled, including a combined suffix appended
to a diagnosis. Clinical wording and codes are preserved.

After installing, re-paste the affected complete SmartPhrase or the complete
A section and click Create / update handoff, then Save handoff. This updates
the previously imported raw text as well as the structured demographics.
Installing alone does not rewrite old diagnosis text or guess missing age.
The same-line format works in I / NUTRITION and N / admission as well.

Supported Epic age abbreviations include y.o., m.o., w.o., and d.o.
A whole-year age remains a whole-year age for the BMI rules. Do not assume an
exact month for a BMI percentile. The prior under-two/unknown-age BMI display
restriction remains. No patient identifiers or date of birth are added.

Malformed or conflicting age/sex values do not overwrite the affected source
section. Other valid sections still import under the existing recovery rules.

Sidebar: Version 6.32 | Age and sex below Room

See TEST_REPORT.md for what was tested.

The following notes describe historical releases.

---

# Version 6.31: compact Problems and age-aware BMI

Save open work. Extract PICU631.zip and upload the contents of
PICU_Handoff_v6_31_Compact_Problems into the existing application code repository.
Replace matching files and keep app.py at the root. Keep the current Streamlit
Secrets, both passwords, encryption key, GitHub token, medication mappings,
private data repository, and public BMI reference file unchanged.
Do not run the setup generators. No new dependencies or archive schema change.

Problems now prints as a single comma-separated paragraph with an inline label.
It wraps only when needed. No supporting evidence, one-item-per-line list,
review-required heading or review status is printed. Details and optional edits
remain in the Problems tab. Unconfirmed inference-based conditions retain a
names-only label in v6.34. Existing source diagnoses and saved decisions are not
rewritten, and dismissed entries remain hidden.

BMI and BMI percentile do not print below 24 months or without an established
age. Height/BSA and the weight Z-score are unchanged. The original BMI remains
stored and editable. At/above age 2 the BMI can print, with a percentile only
when age in months, explicit sex and the reference data permit calculation.

Sex: Male / Female / M / F is read in I or N, on the same or following line.
Read COMPACT_PROBLEMS_UPDATE.md and TEST_REPORT.md for details.
Sidebar: Version 6.31 | Compact problems and age-aware BMI

The following release notes are historical.

---

# Version 6.30: laboratory windows and suggested-problem review

Save current work. Extract PICU630.zip and upload the contents of
PICU_Handoff_v6_30_Problem_Review to the application code repository, replacing
matching files. Keep app.py at the root. Include lab_windows.py and
problem_review.py. Keep all existing Secrets, both passwords, encryption key,
token, medication mappings, public BMI reference data and private repository.
Do not run the generators. No new dependencies are required.

Read LAB_WINDOWS_PROBLEMS_UPDATE.md first. Lactate, theophylline and CK use a
24-hour display window. CRP/procalcitonin are limited to admission onward.
NT-proBNP is the latest from all supplied dates. The new highlighted review band
never modifies the source Diagnoses field. It is not a diagnostic classifier.

The sidebar reads Version 6.30 | Lab windows and suggested problem review.
Schema 23 migrates to 24. Existing fields and save times are retained.
Do not downgrade after saving new review settings.

The following notes describe historical releases, not current installation.

---

# Version 6.29: demographics, fluid totals, latest vitals and Antiepileptic

## Update your existing app
Save open work, extract PICU629.zip and upload the contents of
PICU_Handoff_v6_29_Demographics_Vitals to your application code repository.
Keep app.py at the repository root. Include anthropometrics.py, bmi_reference.py
and the data folder. Keep all existing Secrets, both passwords, encryption key,
token, medication rules and private data repository unchanged. Do not run the
setup or password generators. No new Python packages are required.

The sidebar reads Version 6.29 | Demographics, latest vitals and Antiepileptic.
Schema 22 migrates to 23 without changing existing room fields or settings.
Do not downgrade after saving new demographic fields or Antiepileptic rules.

Read DEMOGRAPHICS_VITALS_UPDATE.md and BMI_REFERENCE.md for the new features.

The notes below are historical.

---

# PICU Handoff 6.27: Pacemaker mode and rate

Complete ZIP update. Read PACEMAKER_UPDATE.md or START_HERE.html first.

W adds the documented pacer mode and rate to Cardiovascular, below vital signs and above CV Infusions. Example: Pacemaker: AAI at 140 bpm. Blank or negative W clears the snapshot. An omitted W preserves it. No heartbeat or output-current value is used as a pacing rate.

Existing credentials and dependencies stay unchanged. Schema 20 migrates to 21 with all prior data preserved. Do not downgrade after saving. The following notes describe earlier releases.

---

# PICU Handoff 6.26: Devices and EVD status

Complete ZIP update. Read DEVICES_UPDATE.md or START_HERE.html first.

U adds a compact device inventory at the bottom. V adds EVD drain status to Neurologic.
Removed non-ETT devices are excluded. Removed ETTs remain clearly labeled airway history.
All new entries are editable, encrypted with the existing archive, and included in room autosave and Print all.

This release uses schema 20 with migration from schemas 1-19. No dependencies or credentials change.
Do not downgrade after saving with this version. Installing the update does not clear handoffs.

The notes below describe earlier releases. Use the 6.26 update guide for current installation instructions.

---

# PICU Handoff 6.25: ETCO2 and CVP in vital signs

Complete ZIP update. Start with ETCO2_CVP_UPDATE.md or START_HERE.html.

ETCO2 goes to respiratory vitals. CVP goes to cardiovascular vitals. Epic
Avg/Min/Max summaries show the recorded Min-to-Max range with supplied units.
No data recorded is ignored without blocking the remaining vital signs.
Single labeled values remain supported. Missing and extreme values are not
invented or corrected.

Upload the complete folder contents with app.py at the root. Keep all current
Secrets and both passwords. No new dependencies or storage migration are needed.
Re-paste the full SmartPhrase or complete E block to import the new values.
The existing clinical parsers outside vitals.py are unchanged.

See TEST_REPORT.md for executed checks. Previously published team guides and
SmartPhrase text stay in the existing encrypted store.

# Earlier release notes

The installation and behavior notes below are historical. Use the Version 6.25
instructions above for this package.

# PICU Handoff 6.24: feeds in FEN/GI

This is a complete ZIP update. Read FEEDS_UPDATE.md or START_HERE.html first.

T-section feeding method, formula and hourly rate appear directly below
intake/output in FEN/GI. Removed tube entries are ignored. Missing rates use a
same-device backup hourly rate when available, otherwise UNK. Intake volume in
mL is not converted to mL/hr. Multiple devices remain separate and editable.

Upload the complete folder contents with app.py at the root, including feeds.py.
Keep all existing Secrets and both passwords. No new dependencies are needed.
Schema 18 migrates to 19 without changing prior fields or settings. Do not
downgrade after saving with this version. Installing the update clears no data.

See TEST_REPORT.md for the checks and limits of this release.

# Historical update notes

The material below describes earlier versions. Use the Version 6.24 installation
instructions above for this package. Previously published team instructions and
SmartPhrase text remain in their existing encrypted store and are not replaced.

# PICU Handoff 6.23: auto-fit printing and clear all

This is the complete app update. Start with PRINT_RESET_UPDATE.md.

- PDF preflight reports the rendered page count for every selected room.
- The default target is one page, with a two-page target available.
- Tighter spacing and bounded column widths help crowded handoffs fit, without clipping data.
- Admin has a one-click shared reset that clears handoffs and deletes custom rooms.
- Medication rules, hidden choices, instructions, SmartPhrase, passwords and error reports are preserved.

Upload the full folder contents with app.py at the root. Preserve all existing Secrets. No new dependencies. Installing the update does not clear data. Schema 18 adds a reset generation to protect against old drafts being restored after a shared reset.

# Earlier setup reference: the user guide and protected Admin

Complete ZIP update based on 6.21. No direct repository changes are made.

## Update an existing deployment

Save open work. Extract PICU622.zip and open PICU_Handoff_v6_22_User_Guide.
Copy all application contents into the current code repository, replacing
matching files. Keep app.py at the root. Keep all current Secrets, encryption
key, app-password hash, GitHub token, medication settings and private data
repository. Do not run create_secrets.py or Generate_Secrets.ipynb again.

No new dependencies or clinical archive schema changes are required. Room
records, save timestamps and every clinical parser keep their previous format.
The sidebar reads: Version 6.22 | User guide and protected Admin.

## Set the second password once

Read ADMIN_SETUP.txt. Run Generate_Admin_Password.ipynb in local JupyterLab, or
run python set_admin_password.py locally. The helper prints exactly one new
admin_password_hash setting, without writing a file or generating an encryption
key. Add the generated line to your existing [app] section in deployment Secrets.
Choose a password different from the app login. Keep the output private.

Admin stays locked until this setting is configured. Routine Handoff, Print all,
Instructions / SmartPhrase and Import errors continue to use the normal app login.
The second password is not individual identity or multifactor authentication.

## Publish team instructions and the Epic source

Open Admin and unlock it with the second password. At the top, edit User
instructions and Epic SmartPhrase. Fill in the exact Epic name/shortcut, the
actual reusable source definition, optional local Epic setup notes, and the
learner guide. Click Save instructions and SmartPhrase.

Only the teaching guide is prefilled. The supplied samples were expanded patient
results, not the actual reusable SmartLinks, so the name and source deliberately
start empty. SMARTPHRASE_TEMPLATE.txt remains a placeholder scaffold. Do not
publish patient results as a reusable source template.

Saving here does not install or change the phrase in Epic. Test a changed source
using your local Epic workflow and synthetic information before using it.

## What users see

Instructions / SmartPhrase in the sidebar provides the eight-step guide and a
read-only source block with copy support and a text download. It also provides
HTML and text downloads of the guide. Handoff has a collapsed Instructions and
Epic SmartPhrase panel above the room selector. No example-loading buttons return.

The steps are: open/sign in, choose Handoff, choose the correct room, run the
phrase in Epic, paste generated text, create/update, review/preview, and save.
The guide also explains new room occupants, partial-section updates, errors,
saved timestamps, shared-session conflicts and Print all.

## Admin access

The whole Admin workspace and its write callbacks recheck the separate unlock.
It expires on leaving Admin, Lock Admin, logout, 15 minutes without Admin activity,
or one hour after unlocking. Changed password hashes revoke a grant on its next
check. There is a per-session password-attempt delay. An expired or absent grant
cannot publish guide text, change Admin mappings/settings, or activate Admin
restore/remove callbacks.

Existing medication mapping, hiding and custom-room controls within Handoff
remain available with the app login, as requested in the earlier workflow. This
is an Admin-screen gate, not a new per-user role/permissions system.

## Separate encrypted content

The guide is stored at encrypted-data/user-guide.enc in the same existing private
data repository, with the same encryption key. It contains reusable teaching
content only. It does not contain the Admin password, app password, or hashes.
Guide publishing does not rewrite handoff-v1.enc, room timestamps, error reports
or medication rules. Ordinary users may refresh the guide independently.

A stale guide save is refused using its expected GitHub file version. The local
editor draft remains available for comparison. Refreshing the read-only guide
does not silently rebase an unsaved Admin draft. Reload published guide into
editor explicitly replaces that draft. A failed read or write does not claim a
publish or change handoffs. Session-only mode is labeled and is not persistent.

Existing encryption and app login do not establish clinical approval. A room
number does not make clinical text anonymous. The existing hosting, access,
retention, and data-handling requirements remain. No live repository was used
while building this update.

## Tests and files

Read TEST_REPORT.md for exact checks and limitations. New modules: user_guide.py,
guide_store.py and admin_access.py. New setup helper: set_admin_password.py and
Generate_Admin_Password.ipynb. USER_GUIDE.html and USER_INSTRUCTIONS.txt are
standalone copies of the default learner guide.
