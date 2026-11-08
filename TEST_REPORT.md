# Version 6.31 validation report

## Automated checks

Original unchanged v6.30 baseline: 2,614 tests passed.
Updated package: 2,661 tests passed (47 added regression cases).
Full suite: python -m pytest -q

Coverage added for same-line and next-line Sex fields (Male/Female/M/F) in I/N,
under-24-month suppression, exact 24-month boundary, unknown-age suppression,
no percentile calculation/reference lookup for under-two exports, preservation
of source BMI/height/BSA, compact inline problem output, duplicate name handling,
HTML escaping, optional hidden/confirmed choices, evidence-change behavior,
Print all, PDF band-height accounting, and encrypted archive round trips.
Only previous assertions for the intentionally changed output were revised.

## Compatibility

An encrypted synthetic archive was created with the original v6.30 code.
Version 6.31 opened it with the same key and every stored field, decision,
setting and save timestamp unchanged. The archive schema remains 24.

Byte-identical original modules include models, labs, laboratory windows, CBC,
blood gases, medication parser, vital signs, feeds, devices, importing, BMI
reference formulas and installer, GitHub storage, encryption, save status and
clear-all logic. The full baseline regression suite was retained.

## PDF checks

A dense synthetic handoff with 34 numbered neurologic notes required two pages
in v6.30 and one page in v6.31, at 7.2-point body text with tightened spacing.
All 34 notes were present in the new PDF. No clipping or text deletion was used.
Longer synthetic handoffs were allowed to continue to a second page.

The public synthetic preview has one landscape page at 7.2-point body text.
It was rendered to a PNG and visually inspected. Problems is a single inline
band, with no printed evidence or review-status prefixes. An infant BMI is
retained in source data but absent from the printed demographics.

## Limits

These are software regression tests, not clinical validation.
Interface callbacks use a simulated Streamlit interface; storage uses mocks.
No live Streamlit deployment, private GitHub connection, or clinical environment
was tested. No patient source texts or deployment secrets were added to the ZIP.
