# PICU Handoff 6.43

CAPD from the new Y section, a bold Vent Settings heading, Respiratory
Allergy/Immunology, and FEN/GI Prokinetic Agents. Built from Version 6.42.

Read CAPD_CATEGORIES_UPDATE.md for behavior, import details and installation.
TEST_REPORT.md documents local testing. Existing clinical selection rules,
infusion rates and numeric fields remain unchanged.

## Upgrade

Upload this folder's contents into the existing application code directory,
replacing matching files. Keep app.py at the root. Include capd.py and all existing
modules. Restart the app and refresh your browser.

Keep current private Secrets, both passwords, encryption key, medication mappings,
BMI reference data and shared storage unchanged. Do not rerun setup generators.
No new dependencies are needed. Saved archives advance to schema 28. Do not
downgrade after saving with this version.

## Use

Create or update a handoff with the generated Epic SmartPhrase. The Y section
holds the documented CAPD total. CAPD always appears between the arousal target
and WAT-1, with None when unavailable. A zero score remains zero. This does not
add a delirium diagnosis. Read in-app import warnings before sharing the handoff.

The existing category selector assigns one medication to one destination.
Custom category definitions, subcategories and assignments stay editable in
Admin. Each visible order still appears once, and hidden orders stay hidden.

No live deployment, patient archive or storage connection was tested or changed.
Use the synthetic examples to check the deployed display before routine use.
