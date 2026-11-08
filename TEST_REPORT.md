# Version 6.32 validation report

## Automated checks

2,702 tests passed with python -m pytest -q.
The 2,661-case preceding suite was retained and 41 regression cases were added.
One existing UI expectation was updated because the room caption intentionally
now contains Sex as well as Age. Save timestamps and status positions remain
unchanged. One older CBC assertion was narrowed to WBC: 999 rather than the
substring 999 anywhere in the output, which could match a randomly generated
record ID. No CBC implementation was changed. The full suite is rerun from
an extracted delivery ZIP.

New coverage includes the exact combined Age: 6 y.o. Sex: female format,
separate lines, next-line values, tabs, nonbreaking spaces, reversed label order,
metadata appended to a diagnosis, custom diagnosis destinations, preservation
of actual diagnosis text and wrapping, partial imports, conflicting/invalid
values, absence of demographic inference from prose, archive round trips,
old embedded-text correction on reimport, and all printed/exported header paths.

Epic y.o./m.o./w.o./d.o. abbreviations are validated without manufacturing an
exact month from a whole-year age. Existing BMI age gates are tested for these
forms, including the 24-month boundary.

## Compatibility

Archive schema remains 24. Storage, encryption, clinical result parsers,
medication mapping logic, saves, and clear-all behavior are unchanged.
Existing records are not automatically rewritten at load. Re-paste affected
text and use Create / update handoff to replace the older embedded Age/Sex
wording with structured demographics. Save only through the existing controls.

Runtime modules changed: app.py, anthropometrics.py, parser.py, importing.py,
exports.py, error_store.py, user_guide.py. No dependencies were added.

## Printed check

The synthetic preview has one landscape page using 7.2-point body text.
Its actual application-generated PDF was rendered to an image and inspected.
The patient column begins with Room: P4201, Age: 6 y.o., Sex: Female, followed
by Admission and Diagnoses. Age and Sex each print once. No clipping was seen.

## Limits

Tests use synthetic data and simulated Streamlit/GitHub interfaces.
No live Streamlit deployment, private repository, or clinical environment was
tested. No live GitHub changes were made. This is a parsing/layout change,
not clinical validation. No patient source text, keys, or secrets are bundled.
