# PICU Handoff 6.49

Built directly from the supplied Version 6.48 package.

The opening Handoff page no longer shows the SmartPhrase source/sample panel.
Short instructions, publication date/time and refresh remain. Source text and
instructions remain editable in the existing protected Admin area.

A leading Epic (S) annotation no longer prevents a supported ventilator mode
from being recognized. The same handling applies to supported numeric setting
fields and known nested labels. The source mode and values stay in the retained
record, while the marker is omitted from the formatted ventilator summary.
Unknown modes and genuinely conflicting values are still not guessed.

An empty Back Up Feed Intake or Back Up Feed Rate placeholder is treated as
an empty T section instead of raising a feeding import error. No feed rate is
inferred from an intake volume.

## Install

Replace matching application files with this folder's contents. Keep app.py at
the root, restart the app, and refresh your browser. Keep existing Secrets, both
passwords, the encryption key, medication mappings, categories, BMI reference
data and shared archive unchanged. Do not rerun setup generators. No new Python
dependencies or archive-schema changes are required. Schema remains 32.

Re-paste complete C and D sections together, or the full SmartPhrase, then select
Create / update handoff and Save handoff. Previously omitted settings cannot be
recovered without re-pasting. The updated format applies to valid stored fields.

## Daily use

In Epic, find SmartPhrase author Streamlit and subscribe to PICUHANDOFFSMARTPHRASE.
Select the correct room here, open the patient's Epic note, and enter
.PICUHANDOFFSMARTPHRASE. Paste the populated text with its dividers into the app,
click Create / update handoff, and review the preview. Move to the next room to
save automatically or press Save handoff. Check the saved time before closing.
Print all prepares the team's PDF.

Read VENT_MARKERS_UPDATE.md for details and TEST_REPORT.md for local verification.
Historical release notes describe prior versions, not additional changes here.
The existing recent-SBS and mode-gated historical-fallback rules are unchanged.
