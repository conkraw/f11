# Version 6.14 validation report

## Executed checks

The unmodified Version 6.13 baseline passed 1,169 tests in this environment. The Version 6.14 suite passed 1,286 tests with no failures or skips. The command was PYTHONPATH=. pytest -q --disable-warnings.

The added tests cover selected order aliases, excluded tests, repeating interval normalization, one-time and STAT filtering, missing/invalid counts, duplicate selection by maximum count, preserving different schedules/specimens/panels, keeping notes separate, R boundaries, R-only imports, clear-versus-omit behavior, all-or-nothing import failure, callbacks, pending widget edits during room autosave, encryption, migration, HTML/text/PDF export, orders-only rooms and Print all. Migration fixtures in older tests were updated only to omit the newly introduced field and assert the new current schema. Existing CBC, gas and medication parsing tests were retained.

The three supplied complete SmartPhrase examples were imported separately. Their R sections yielded 6, 8 and 5 displayed schedules, respectively. The duplicate chest-X-ray orders with counts of 3 and 7 selected 7. The source examples and their clinical details are not included in the delivered ZIP.

For each supplied example, the unchanged Version 6.13 source was run separately. After excluding only generated IDs/timestamps and the new recurring_orders field, all pre-existing parsed handoff fields matched the Version 6.14 results exactly. The original CBC, blood-gas, lab and medication parser files, lab layout, encryption, GitHub storage implementation and dependency list were verified byte-for-byte unchanged.

An encrypted synthetic archive was created by the original Version 6.13 code in a separate process. Version 6.14 opened it with the same encryption key, retained every previous field and setting, added recurring_orders=None, and successfully encrypted/decrypted the upgraded archive. No user deployment key or private store was accessed.

The supplied synthetic preview has one landscape Letter page at the existing 7.2-point body size. It was rendered with pdftoppm and visually checked for the new column title, schedule list, CBC/BMP trees, latest gas, and preservation of the other columns. Existing long-content pagination tests passed.

## Limitations

Streamlit is not installed in the build environment. Interface tests use a Streamlit widget stub, not a real browser session. The hosted app and authenticated private storage connection were not tested. No direct GitHub changes were made.

These tests establish the checked parsing and display behavior, not clinical validity or the active/completed status of an Epic order. Number of Occurrences is the source field, not draws remaining. Unrequested tests are deliberately excluded. Different frequencies and specimen types remain separate. Existing platform/privacy limitations still apply.
