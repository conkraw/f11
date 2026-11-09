# Version 6.44 local validation

Base: delivered PICU643.zip. The complete updated suite passed 3,709 tests.
There are 85 focused synthetic regression cases in
`tests/test_empty_groups_icp_cpp.py`.

The new cases cover the five empty medication groups, correct system placement,
hidden/excluded order safeguards, failed medication-import safeguards, heparin
flush exclusion from DVT grouping, custom names/locations/subcategories, parent
occupancy, single-destination rendering, no mutation by exports, saved layout
validation, encrypted round trips, empty-room exclusion, Print all, and refresh
of changed shared categories in open and saved rooms.

ICP/CPP cases cover direct ranges, Avg/Min/Max summaries, repeated Epic labels,
labels and values on separate lines, brackets, reordered statistics, upper/lower
case, whitespace, decimals, zero/negative values, missing fields, single values,
explicit last readings outside the given range, no average substitution,
conflicting duplicates, invalid units and values, section failure isolation,
retained-data suppression after failure, successful recovery, partial imports,
manual edits, per-room isolation, autosave callbacks, and PDF/HTML/text output.

The previous suite's current-schema assertions were advanced from 28 to 29.
Two historical output assertions were updated for the newly requested empty
Fever Control line and for section-scoped PDF separator ordering. No tests
were removed or skipped to obtain a passing result. A new PDF text assertion
normalizes wrapping whitespace before checking category labels, because narrow
columns may legitimately wrap a label without changing its content.

A synthetic encrypted archive was created using the original delivered 6.43
code and opened by 6.44 with the same generated test key. All original room
fields, custom rooms, medication/category settings and saved timestamps remained
identical. Only the schema number changed. A renamed empty category rendered
correctly when the updated shared settings were applied. No real patient
archive or deployment credential was used in that test.

The two-page preview contains two synthetic rooms. Each fits on one landscape
page with 8-point body text, without tighter spacing or rebalanced columns.
One example has all five empty groups. The other has populated groups and a
zero ICP. Both final pages were rendered and visually inspected. Longer real
handoffs may still require additional pages rather than clipping content.

Production medication selection rules, laboratory/CBC/blood-gas parsers,
ventilator and other vital parsers, feeding/device parsers, CAPD handling,
encryption and storage implementations are unchanged. Rendering now adds empty
group labels, and the M importer adds explicitly labelled range/last support.
Optional empty-group layout snapshots follow shared custom category definitions.

The release ZIP is checked with CRC and per-file SHA-256 hashes. The complete
suite is also run from a clean extraction of the delivery ZIP.

UI tests use local Streamlit stubs and storage tests use local simulations.
No live deployment, private storage connection, or Epic integration was tested
or modified. These tests are not clinical validation.
