# Version 6.33 validation report

## Automated checks

The original v6.32 package was extracted and its unmodified suite passed:
2,702 tests. The v6.33 suite has 2,791 tests, including 89 new synthetic
regression cases. The full suite passed after the changes and is rerun from
the extracted delivery ZIP before delivery.

Historical assertions of the current upgraded archive schema were changed
from 24 to 25. Two parametrized expectations for a continuous dose-rate range
without Last Admin now require UNK rather than emphasizing that order range.
No existing clinical-result parser assertions were removed.

New coverage includes:

- Named nitroprusside, nicardipine and norepinephrine orders and name variants.
- Numeric Last Admin priority for other continuous orders, with original Dose
  and Last Rate fields retained unchanged.
- Distinct units, decimal precision, zero rates, unsupported values and ranges.
- Stopped, Paused, Held, Not given, Not administered, and Discontinued events.
- No interpretation of a stopped administration as order discontinuation.
- Missing rates, Rate Verify/New Bag events, PN volumes/lipid masses, invalid
  timestamps, and multiple events in one cell.
- PRN and intermittent doses remaining separate from continuous-rate handling.
- Custom handoff wording precedence and HTML escaping.
- No raw provider names or administration free text in the stored new fields.
- EN-space clipboard columns, blank topical doses, PN And connectors, and
  ambiguous single-rate boundaries that are not assigned by guesswork.
- Automatic ondansetron/Zofran Antiemetics grouping, scheduled and PRN orders,
  start/hold labels, exclusions, hidden rows, and remembered manual choices.
- Text, HTML, PDF, multi-room output, editor validation, room-switch autosave,
  optional-field preservation, encrypted round trips and archive migration.

## Supplied source check

The exact pasted medication block, with EN-space column separators, parsed
all 31 medication rows without import errors. The nitroprusside row retained
its ordered 0.1-6 mcg/kg/min (Dosing Weight), its 2.52 mL/hr Last Rate, and the
sanitized Last Admin rate 6 mcg/kg/min with timestamp 11/08/26 1016. The rendered
handoff selected the latter value, without changing any supplied number.
The source paste is outside the delivery directory and is not bundled.

## Archive compatibility

A separate process running the original v6.32 code created a synthetic
schema-24 encrypted archive. V6.33 opened it with the same key and preserved
every original room field, medication row, setting and save timestamp. Only
the schema value became 25. Re-encryption and decryption also passed. The
old row did not acquire a fabricated Last Admin rate. Historical raw Last
Admin data cannot be recovered, so affected B sections must be re-pasted.

Source schema advances to 25 to prevent an older application from treating
new medication fields/group choices as its own schema. No encryption or
storage-backend module, password generator, dependency, CBC, gas, vital-sign,
demographic, feeding, device or laboratory parser was changed.

Updated runtime files: app.py, medications.py, infusions.py, fen_gi.py,
models.py, exports.py (footer text), error_store.py (version string).
New runtime files: infusion_rates.py, medication_columns.py.

## Printed check

The application-generated synthetic landscape preview has one page with
7.2-point body text. It includes Last Admin rate emphasis in CV Infusions,
Neurologic Infusions and DVT Prophylaxis, plus Antiemetics in FEN/GI. The PDF
was rendered to an image and visually inspected. No clipped text was seen.
No medication was removed to make the example fit.

## Limits

The test interfaces simulate Streamlit callbacks and GitHub responses. The
live deployment, private repository, Epic connection and bedside pump were
not tested. These are parsing/display changes, not clinical validation or
authorization to use the handoff as a medication administration source.
A pasted Last Admin value is a chart snapshot, not a current live rate.
