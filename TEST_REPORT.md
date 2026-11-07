# Validation report: Version 6.21

## Executed checks

The unmodified supplied Version 6.20 archive passed 1,756 automated tests
before editing. Version 6.21 passes 1,777 tests, including 21 new regression
cases. The complete suite is also rerun from a separate extraction of the
final ZIP. No tests were skipped or disabled.

Command: PYTHONPATH=. python -m pytest -q --disable-warnings

One existing version 6.20 test was revised for the requested change: DVT
infusions and injections now share one top-level category instead of a
separate infusion subgroup. Other existing assertions remain.

## Coverage of the change

Tests cover a single DVT heading, all six order permutations of heparin,
cangrelor and enoxaparin, preservation of original order, no duplicate entries,
bold infusion names and doses, compact injection wording, recorded pump rates,
custom wording, HTML escaping, hidden and excluded orders, manual group choices,
manual infusion-display overrides and unrelated hematology infusions.

PDF, HTML, text and Print all output are checked. PDF text/font inspection
checks name/dose emphasis and one occurrence per medication. A 30-order
synthetic DVT list continues onto additional pages without losing entries.
The existing test suite covers the room editor, save conflicts, encrypted
storage, diagnostics, parsers, mappings, autosave and save-status timestamps.

The single-page synthetic preview was generated with the application and
rendered to PNG at 160 dpi. It was visually inspected. It shows one DVT
Prophylaxis heading with emphasized heparin and cangrelor infusions followed
by enoxaparin, with no extra Heme Infusions heading for these orders.

## Compatibility and package checks

Compared against the supplied 6.20 archive, only three runtime modules change:
infusions.py changes display block ordering, app.py changes only its version
label/docstring, and error_store.py changes only the app-version identifier.
Every other runtime Python module and dependency file is byte-for-byte
unchanged. In particular, models.py, all clinical parsers, exports.py,
github_store.py, security.py and save_status.py are unchanged. Schema 17,
medication data, saved group/display choices and storage paths are unchanged.

Tests also seal/open a synthetic saved archive with the same key and verify
that rendering does not alter any stored field, setting or save timestamp.
The final ZIP is checked using ZipFile.testzip, a complete file comparison and
a regenerated SHA-256 manifest. Only synthetic examples are added. No actual
patient records, production credentials, caches or keys are included.

## Limitations

Streamlit is not installed in this execution environment. Interface tests use
widget stubs, not a browser session. Repository calls use mocked responses.
The user's live deployment and authenticated private handoff repository have
not been tested or modified. The grouping is a user-selected presentation
category, not an assessment of prophylactic indication or dose suitability.
