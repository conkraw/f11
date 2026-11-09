# PICU Handoff 6.48

Built from Version 6.47. Recent SBS stays first choice. When no recent result is
available, the last available SBS can display only with a recognized documented
ventilator mode. Historical values are labelled last available. Source-labelled
targets remain targets.

## Install

Replace matching application files with this folder's contents. Keep app.py at
the root, restart the app, and refresh your browser. Keep existing Secrets, both
passwords, the encryption key, medication mappings, categories, BMI reference
data and shared archive unchanged. Do not rerun setup generators. No new Python
dependencies are required.

Re-paste the complete C, D and K sections or the full SmartPhrase to capture the
Last SBS Ever value that earlier versions discarded. Archives upgrade to schema
32 with existing fields preserved. Do not downgrade after saving with this release.

## Daily use

In Epic, find SmartPhrase author Streamlit and subscribe to PICUHANDOFFSMARTPHRASE.
Select the correct room here, open the patient's Epic note, and enter
.PICUHANDOFFSMARTPHRASE. Paste the populated text with its dividers into the app,
click Create / update handoff, and review the preview. Move to the next room to
save automatically or press Save handoff. Check the saved time before closing.
Print all prepares the team's PDF.

The protected Delete all handoff data action and other 6.47 changes are retained.
See SBS_VENT_FALLBACK_UPDATE.md for the exact new behavior and TEST_REPORT.md for
local verification. Historical release notes describe prior versions and are
superseded by this note where behavior has changed. No live deployment credentials
or patient archive are included.
