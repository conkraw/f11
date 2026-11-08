# Validation report: Version 6.23

## Executed checks

The original Version 6.22 ZIP passed all 1,843 tests before modification. The updated package passed 1,892 tests in the build environment. Existing legacy fixtures and schema assertions were updated for schema 18. A legacy long-text assertion now permits a one-page result because adaptive columns fit that example without data loss. Clinical content assertions remain in place.

New checks cover actual PDF page counts for one/two-page targets, long-content continuation, unique-text retention, coordinate bounds, fixed column order, heading widths, no below-limit body font, per-room batch boundaries, unchanged laboratory and medication data, malformed targets, Admin authorization, failed and conflicting resets, preservation of shared rules and instructions, clearing all local widget/draft/selection state, token generation, stale writer rejection, remote reset reconciliation, old download revocation, logout revocation, and schema-17 encrypted migration.

A separate migration check used the unmodified Version 6.22 code to generate an encrypted archive. The updated code opened it with the same key. All old settings, room contents, IDs and timestamps were identical. Round-trip encryption and a subsequent reset were also checked.

Synthetic visual comparisons: one dense handoff rendered as 2 pages under Version 6.22 and 1 page under this version. A deliberately lengthy handoff rendered as 6 pages before and 2 afterward. Every numbered observation was retained exactly once. Both continuation pages and the single-page example were rendered with PyMuPDF and visually inspected. The examples are synthetic, not user patient records.

The new PDF preflight and downloads use the same ReportLab rendering functions. The page target is not a hard content limit. Longer handoffs may still exceed it rather than be truncated.

## Unchanged clinical logic

Clinical parser modules, CBC/gas selection, lab tree drawing, medication routing/grouping, data encryption functions, storage API operations, guide storage and the separate Admin password mechanism were not altered. The models module adds only archive reset metadata and migration, not clinical field changes.

## Limitations

Streamlit is not installed in this build environment. Interface/callback tests use widget stubs, and GitHub operations use mock stores. The hosted browser, authenticated private data repository and physical printer have not been tested. No real shared handoffs were cleared and no direct GitHub edits were made.

Automatic fitting applies to PDF, not browser-specific HTML pagination. Clear all changes the current encrypted archive, not prior Git history or downloaded copies. Other sessions must reload to see a reset. Simulated stale writes are rejected, and reset detection discards their previous drafts on reload. The tests do not establish clinical validity, identity, privacy compliance or data completeness.
