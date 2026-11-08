# Version 6.29 verification

Baseline Version 6.28 suite: 2,324 tests passed.
Updated suite: 2,420 tests passed.
New feature module tests: 95 cases passed.

Executed checks cover explicit age/sex/BMI/height/BSA parsing, missing input gates,
latest SpO2/ETCO2/CVP brackets, zero and flagged values, unit mismatches, independent
section updates, dosing-weight-only mL/kg totals, immutable source totals,
Antiepileptic defaults and saved additional-name rules, exact-rule precedence,
hidden medications, continuous infusion emphasis, editor callbacks and exports.

The BMI formula was checked against both published CDC examples below and above
P95. Public-reference validation, completeness, atomic installation and a mocked
fixed-URL download were tested using artificial structure fixtures. Those fixtures
are never installed as reference data. A complete official CDC table was not
available in this build environment. Load it in Admin or place the official CSV
at data/cdc_bmi_age_2022.csv. No real patient percentile was calculated.

An archive was generated and encrypted by the original Version 6.28 code, then
opened by this version with the same synthetic key. Every previous room field,
setting and save timestamp compared equal. Schema 22 becomes 23. New demographics
and Antiepileptic prefix rules also survive encrypted round-trip tests.

Four supplied E/I example patterns were checked, including last-value alert flags,
missing last readings, measured weights in grams and kg, and BMI prose. Their
age and sex were not invented. User source files are excluded from the package.

Two synthetic room PDFs rendered on two landscape pages. Both were visually
inspected after rendering. Age is directly below Room. Intake/output include the
recorded dosing-weight denominator. Antiepileptic infusion emphasis is retained.
The preview intentionally shows the under-2 percentile restriction and missing
reference-data state. The HTML is a corresponding synthetic preview.

The following runtime parsers are byte-for-byte unchanged from Version 6.28:
cbc.py, blood_gases.py, labs.py, lab_layout.py, feeds.py, diet.py, devices.py,
pacemaker.py, cultures.py, recurring_orders.py, ventilation.py, noninvasive.py.

Tests use interface stubs and mocked network calls where needed. Streamlit was
not installed in this build environment. This is not a live Streamlit deployment,
authenticated private-GitHub integration test, or clinical validation. No direct
changes were made to the user's GitHub repositories. No credentials or reference
font files are included. The complete ZIP is integrity checked and its extracted
application is tested separately before delivery.
