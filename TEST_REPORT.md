# Version 6.42 local validation report

Base: delivered PICU641.zip. The package includes 93 new regression tests in
`tests/test_dynamic_categories.py`. Historical tests were updated only for the
new schema number, explicitly requested medication placement, the linked
laboratory location, the consolidated picker, and layout changes from new labels.

The full test suite contains 3,548 cases. The final delivery is checked by running
that suite from a fresh extraction of the ZIP. The release is delivered only
after all cases pass.

New coverage includes default drug grouping, route exclusions, one-destination
selection, category and subcategory creation, renaming and moving, retained
source fields, exact/prefix matching and specificity, hidden/excluded orders,
custom-label HTML escaping, infusion emphasis, old archive migration, encrypted
round trips, inline mapping persistence, shared-write failures and conflicts,
Admin authorization, and one theophylline result directly under aminophylline.

A synthetic encrypted archive was created by the original delivered 6.41 code,
then opened with the new code using the same test key. Apart from schema 26 to
27, all previous fields, settings, custom rooms and save timestamps matched
exactly. No real private archive or deployment key was accessed.

Two synthetic preview rooms were exported as a single PDF. Each fits on one
landscape page at 8-point body text. One shows the default Respiratory groups.
The other moves the existing Beta-Agonist and Anticholinergic groups beneath
Bronchodilators and adds FEN/GI / Electrolyte Replacement / Enteral. No order or
linked theophylline result appears twice. Both pages were rendered and inspected.
The preview is not a treatment plan. Longer real handoffs can still paginate.

UI and storage tests use local stubs and mocked writes. A live Streamlit browser
session could not be tested here because Streamlit is not installed in the test
environment and package-network access was unavailable. No live deployment,
Epic connection or shared-storage connection was tested or modified. No clinical
validation is claimed. The existing production dependency list is unchanged.
