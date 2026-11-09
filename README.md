# PICU Handoff 6.47

Built from Version 6.46. This release adds the rolling 24-hour VANCOTROUGH
filter, brief instructions at the top of Handoff, an accessible password-protected
Delete all handoff data action, and bold labels for empty medication groups.
The separate instructions workspace is removed.

## Install

Replace matching application files with this folder's contents. Keep app.py at
the root, restart the app, and refresh the browser. Keep existing Secrets, both
passwords, the encryption key, medication mappings, categories, BMI reference
data and shared archive unchanged. Do not rerun setup generators. No new Python
dependencies or archive-schema changes are required. No re-pasting is needed.

## Daily use

In Epic, find SmartPhrase author Streamlit and subscribe to PICUHANDOFFSMARTPHRASE.
Select the correct room here, open the patient's Epic note, and enter
.PICUHANDOFFSMARTPHRASE. Paste the populated text with its dividers into the app,
click Create / update handoff, and review the preview. Move to the next room to
save automatically or press Save handoff. Check the saved time before closing.
Print all prepares the team's PDF.

## Delete the current census

Open Delete all handoff data on Handoff. Enter the separate Admin password and
press Delete all handoff data. This clears all saved handoffs and current-session
drafts, removes custom rooms, and leaves preset rooms blank. Categories, rules,
SmartPhrase settings and passwords remain. Other users must reload the archive.
Earlier archive versions, downloaded copies, backups and printouts are not erased.

See WORKFLOW_RECENT_TROUGH_UPDATE.md for exact behavior and TEST_REPORT.md for
local verification and limitations. Historical release notes describe prior
versions and are superseded by this release note where behavior has changed.
This package contains no live deployment credentials or patient archive.
