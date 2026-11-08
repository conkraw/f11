# Version 6.35 validation report

The full suite passed: 2,924 tests in the updated working directory, including
40 new synthetic regression cases. The 40 new cases were also rerun from the
extracted delivery ZIP. Existing test assertions were not changed.

Coverage includes:
- Metric height followed by feet/inches, with straight, typographic and prime quotes.
- Repeated Height headings, Length aliases, explicit units and normalization.
- Malformed annotations, contradictory equivalents and invalid values still fail.
- Measured and dosing weights remain distinct, including their Z-score and BMI/BSA.
- A successful I import replaces retained values and clears only the I warning.
- Failed imports keep the previous I data and suppress mL/kg calculations.
- Normalized values in text, HTML, single-page PDF and encrypted round trips.

The complete I-section wording retrieved from the current supplied attachment
was transcribed outside the delivery package and exercised against the original
v6.34 and updated v6.35 import functions. The original reproduces the height error
and retains previous weights. The update imports the weight, dosing weight,
Z-score, height, BMI and BSA and clears the I warning. The entire patient file
was not exercised end to end in this update. No patient fixture is bundled.

A synthetic encrypted archive created with the unmodified original v6.34 code
was opened by v6.35 using the same key. All previous fields, settings, custom
room entries and timestamps compared equal. No schema migration is required.

The synthetic one-page landscape preview was generated with the app's own PDF
exporter and rendered to an image for visual inspection. Normalized height,
weight and dosing weight appear in the demographic column. The mL/kg totals
appear in FEN/GI. There is no import warning for the supported height format.

Runtime changes are limited to anthropometrics.py, import_review.py and the
version label in app.py. Other clinical parsers, the CBC and blood-gas trees,
exports, storage and autosave modules are byte-identical to v6.34.

Tests run under Python 3.13. UI and GitHub tests use existing simulated interfaces
and mock responses. No live Streamlit deployment, Epic connection or private
repository was tested or changed. This is a formatting/import fix, not clinical
validation of the application.
