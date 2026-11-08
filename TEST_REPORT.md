# Version 6.26 validation

The working package passes 2,164 automated tests: 2,061 existing tests and 103 new device tests. Historical migration fixtures and current-schema assertions were updated for the two added snapshots. No previous test was removed.

The device checks cover ETT and removed-ETT history, device identification independent of surrounding headings, removed non-ETT exclusion, dated vascular lines, tracheostomies, feeding tubes, urinary catheters, drains, EVD drain status, non-EVD ICP monitors, empty and conflicting fields, HTML escaping, omission/restoration, independent U/V updates, partial recovery and patient-free error diagnostics. Tests also cover editor callbacks, room autosave snapshots, encrypted round trips, new-patient and shared reset behavior, single and batch export, and overflow without clipping.

All nine supplied U/V excerpts were checked separately against their expected device inventories. The excerpts are not included in the distribution. No real patient source is included in new examples or tests.

An encrypted synthetic schema-19 archive was created with the actual original Version 6.25 code, then opened with Version 6.26 using the same key. Every original field, setting, reset generation and save timestamp remained unchanged. The new snapshots initialize to null until imported.

Twenty-two existing clinical parser, layout-helper, security and storage modules were compared byte-for-byte with Version 6.25 and remain unchanged. The generic section divider parser now recognizes U/V, the import pipeline handles their independent snapshots, and the export path adds the device band and EVD prefix. Runtime file changes are listed in UPDATE_FILES.txt.

The three-room synthetic PDF was rendered at 145 dpi and each page was visually inspected. Each room occupies one landscape page in this example. The device inventory is at the bottom, and the first page shows EVD status among the neurologic observations. Longer content continues according to the existing auto-fit limits.

The delivery ZIP is integrity-checked and every packaged file has a SHA-256 digest in SHA256SUMS.txt. The full suite is also rerun from an extracted delivery copy.

Limits: Streamlit page tests use widget stubs, not a real deployed browser session. Storage tests use synthetic data and mocked requests. No live app or authenticated private handoff repository was accessed or tested. Tests cannot guarantee every future Epic format. The inventory reflects the pasted documentation, not verified bedside device placement.
