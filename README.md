# PICU Handoff 6.46

Built from the supplied Version 6.45 package. Adds direct support for the user's
SBS Last 24 Hours field and a Hematology / G-CSF Stimulator category for filgrastim.
The compact handoff layout and all other clinical parsers are unchanged.

Read SBS_WINDOW_GCSF_UPDATE.md for import behavior and installation.
TEST_REPORT.md records verification and limitations.

## Install

Upload the contents of this complete folder into your existing application code
folder, replacing matching files. Keep app.py at the root, restart the app, and
refresh your browser. Keep Secrets, both passwords, the encryption key, medication
mappings, category settings, BMI reference data, and your shared archive unchanged.
Do not rerun setup generators. No new Python dependencies are required.

Archive schema 30 upgrades to 31. Avoid downgrading after saving.
Re-paste the K section or full SmartPhrase to replace old SBS data.

## Your SBS structure

    Target Arousal Level:
    SBS Last 24 Hours:
    Last SBS Ever: Target Arousal Level (SBS): SBS -1

The empty recent field above produces SBS: None. Last SBS Ever is not a fallback.
A populated prefiltered field uses only that value. An explicit target remains
labelled as a target. Timestamped observed readings keep the rolling 24-hour
filter. Missing recording times are never fabricated.

A source-filtered untimed value is a snapshot of Epic's 24-hour output. Its report
or import time is stored separately from observation times and is never renewed
by saving or room changes. See the release note for timing limitations.

## Category

Filgrastim defaults to G-CSF Stimulator in Hematology. The label uses G-CSF rather
than GM-CSF because those are different factors. Existing explicit assignments
remain authoritative. The heading can be renamed or nested in Admin.

This package includes source, synthetic examples, and tests. It does not contain
live deployment credentials or a private handoff archive.
