# Validation report: Version 6.20

## Executed checks

The original unmodified Version 6.19 package passed 1,679 automated tests before
editing. The updated package passes 1,756 tests, including 77 added regression
cases. Two existing test assertions were updated for the intentional display
order change: Respiratory Infusions now precede separate respiratory notes.
No test was skipped or disabled.

Command: PYTHONPATH=. python -m pytest -q --disable-warnings

The delivery ZIP is validated with ZipFile.testzip and a SHA-256 file manifest.
It is extracted into a separate directory and the full suite is rerun there.

## Added coverage

Continuous respiratory parenteral, nebulized and inhaled orders, supported route
aliases, excluded intermittent and PRN schedules, unmapped orders, manual display
overrides, and preservation of Neuro/CV classification behavior are tested.

Heme tests cover DVT infusion subgroups, separate scheduled injections, other
hematology infusions, no duplicate orders, hidden/excluded entries, custom text,
held/start labels, blank doses, recorded zero rates and unchanged source values.

Text/HTML/PDF share the same headings, contents and ordering. All 16 combinations
of respiratory vitals, support, theophylline results and body content are checked
for plain/rich consistency. PDF text extraction and font spans verify content and
bold medication names. Long respiratory/heme lists paginate without dropping
sentinel entries. Print all includes both rooms with separate starting pages.

Widget-stub tests verify new display controls, callback persistence, failed-save
rollback, and Admin edits without an open handoff. GitHub writes are mocked.
All pre-existing save-status, autosave, parser, privacy and encryption tests pass.

A synthetic archive was generated with the original Version 6.19 modules, then
opened with the updated modules using the same key. Every saved field, setting,
room ID and timestamp remained identical before and after rendering and an
encrypted round trip. Schema 17 and existing infusion-rule storage are unchanged.

The single-page synthetic preview was generated with the updated PDF renderer
and visually inspected after rasterization. It shows Neuro/CV emphasis alongside
the matching Respiratory and Heme emphasis and a separate enoxaparin entry.

## Scope and limitations

Runtime changes are limited to infusions.py, models.py display composition,
exports.py grouped rendering, app.py display controls/version, and error_store.py
version identification. Clinical parsers, laboratory tree rendering, save-status
logic, storage implementation, encryption and dependency requirements are
unchanged. No production patient records or Secrets are in the added examples.

UI tests use a widget stub, not a full browser or Streamlit lifecycle. Streamlit
is not installed in this environment. No live deployment or authenticated private
GitHub archive was tested or modified. Tests do not establish clinical validity,
current bedside treatment, or institutional approval. Verify the deployed output.
