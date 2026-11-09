# Version 6.43 local validation

Base: delivered PICU642.zip. Its unmodified baseline suite passed 3,548 tests.
The updated suite passed 3,624 tests. There are 75 focused new regression cases
in tests/test_capd_categories_heading.py, plus coverage added automatically by
an existing parameterized category test.

New tests cover CAPD total parsing (including the supplied wrapped-label format),
zero and missing totals, conflicting or invalid totals, independent section
failure recovery, missing dividers and duplicate pairs, omission versus clearing,
SBS/CAPD/WAT order, PDF/HTML/text output, per-room editing/autosave, encrypted
round trips, Print all and empty-room exclusion, new category defaults, route
exclusions, one-destination overrides, hidden orders, custom subcategories,
category-catalog migration, and an actually bold PDF Vent Settings heading.

Historical assertions were updated for the schema number and the requested new
CAPD placeholder and Vent Settings heading. A regression exposed that a synthetic
CAPD: None display row could make empty rooms appear in Print all. Production
batch selection was corrected to inspect stored observations rather than the
render-only placeholder. Empty-room tests were kept unchanged.

A synthetic encrypted archive was created using the original delivered 6.42
code, then opened with 6.43 using the same test key. Every prior room field,
custom room, saved timestamp, category definition and assignment rule remained
unchanged. The schema advanced from 27 to 28 and the customized catalog gained
only the two missing built-in category definitions. No real shared archive or
deployment credential was accessed.

The PDF preview has two synthetic rooms, one with CAPD 24 and one without a
recorded CAPD. Each fits on one landscape page at 8-point body text. Both pages
were rendered and visually inspected. Settings and new medication categories
appear once in the requested columns. Longer real handoffs may need extra pages.

The complete release is integrity-checked with ZIP CRC and per-file SHA-256
hashes. Tests are rerun from a fresh extraction of the final ZIP before delivery.

UI callback tests use a Streamlit stub and storage tests use local simulations.
The deployed app, live Epic connection and private storage connection were not
tested or modified. No clinical validation is claimed. The production dependency
list is unchanged. CAPD is displayed as a recorded screening total only, not
converted into a diagnosis or treatment recommendation.
