# PICU Handoff 6.45

Built from the supplied Version 6.44 package. Adds observed SBS selection,
TPN, Antiplatelet Therapy, Antibiotics, ID Drug Levels, and culture headings.
The M parser accepts the supplied repeated-label ICP/CPP format and wrapped
Avg/Min/Max lines. The compact landscape layout is retained.

Read NEURO_ID_UPDATE.md for behavior, source requirements, and installation.
TEST_REPORT.md records local verification and its limits.

## Upgrade

Upload all files inside this folder into the existing application code folder,
replacing matching files. Keep app.py at the root. Include the new sbs.py.
Restart the app and refresh the browser.

Keep existing private Secrets, both passwords, encryption key, medication
mappings, category definitions, BMI reference data, and shared data archive.
Do not rerun generators. There are no new Python dependencies.
The archive upgrades from schema 29 to 30. Do not downgrade after saving.

Re-paste complete B, F, G, K, and M blocks, or the full SmartPhrase, to load
new source values and replace previously failed sections. Omitted sections
keep their previous snapshots. Included empty sections clear their own data.

## Recorded SBS is not an SBS target

Only the most recent observed score with an explicit source date and time,
within the preceding 24 hours, prints. An upload timestamp is never substituted
for the observation time. Targets remain editable but do not print as readings.

A supported K format is:

    SBS observations:
    SBS: -1 [11/09/2026 10:00]

Use the actual observation date and time. The template does not provide or
invent an institution-specific Epic SmartLink. Ask your local Epic team for
an observed-score output that includes its source recording time.

All bundled examples are synthetic. Review in-app import warnings before
sharing handoffs. No live deployment or clinical validation is claimed.
