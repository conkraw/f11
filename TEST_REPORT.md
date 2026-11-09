# Version 6.45 local validation

Base: the supplied PICU644.zip. The original baseline passed 3,709 tests here.
The updated suite has 3,803 tests, including 92 focused synthetic cases in
`tests/test_neuro_id_tpn.py`.

The full suite passed all 3,803 tests from a clean extraction of the delivery
ZIP. The run result is recorded in DELIVERY_VERIFICATION.txt. All delivered
Python files are byte-identical to those tested in that extracted run.

Coverage includes repeated and wrapped ICP/CPP summaries, full-width colons,
zero values, independent last readings, source failure isolation, source targets
versus observed SBS, observed-score validation, explicit date/time formats,
24-hour boundaries, future and missing times, daylight-saving ambiguity, manual
editing callbacks, encrypted round trips, single-destination medication groups,
TPN rates and distinct bags, antiplatelet/DVT separation, existing mapping
priority, route exclusions, dated vancomycin results, culture formatting,
empty-versus-hidden cultures, Print all, and non-mutating exports.

Older assertions were updated only for intentional changes: schema 30,
cangrelor's new group, culture None statements, the Antibiotics heading, and
keeping SBS targets off measured-score output. Ordering tests that need a
measured SBS now use an explicitly timestamped synthetic observation instead
of treating a target as observed. No existing tests were removed or skipped.

An encrypted synthetic archive was created by the original 6.44 modules and
opened with this release using the same generated test key. Every old room
field, custom room, prior setting, mapping, and saved timestamp remained
unchanged. Schema 30 and three missing built-in category definitions were
added. A subsequent encrypted round trip retained the resulting data exactly.

The supplied exact M block was accepted by original 6.44 in local testing.
No claim is made that the user's live failure was reproduced. Its full
import-to-PDF path is covered in this release, along with additional wrapping
variants. The supplied K snippets have targets or blanks, not timestamped
measured SBS values. Measured-score formats were tested with synthetic input.
Relevant supplied trough and medication patterns were tested without copying
raw patient charts into this release.

The preview contains two synthetic rooms. Each fits on one landscape page at
8-point body text without extra compression. Both pages were rendered and
visually checked. Longer real handoffs can still require additional pages.

UI and storage tests use local simulations. No live Streamlit deployment,
private repository, clinical data archive, or deployment credentials were
accessed or modified. No clinical validation is claimed.
