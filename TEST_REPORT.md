# Validation: Version 6.10

## Executed checks

The original Version 6.9 ZIP passed 863 tests before changes. The updated package
passes 927 tests (863 retained/updated regressions and 64 new workflow/print tests)
under Python 3.13. The complete suite is run with PYTHONPATH=. pytest -q
--disable-warnings. The delivery ZIP is extracted and the same full suite is run
again before delivery.

Existing tests were updated only where expected behavior intentionally changed:
the Rapid Viral Panel heading, click-time download generators, and saved timestamps
created by room-switch autosave. All clinical parsing/storage regression tests remain.

New coverage includes outgoing-room save order, expected-SHA forwarding, keeping
the current room after network/conflict/unexpected failures, retry behavior,
pending field values, pending medication mappings, stale-base conflicts,
unchanged-room optimization, custom/Other room navigation, expired callbacks,
late old-room callback isolation, no sample buttons, actual store arguments,
EST/EDT date conversion and the repeated fall-back hour, identical print stamps
across packet/continuation pages, deferred download generation, immutable private
download snapshots, expired download callbacks, positive-only bold font spans,
negative/pending/normal-flora exclusions, HTML escaping, and unchanged archive data.

A synthetic encrypted archive was generated using the original Version 6.9 code
in an isolated process, then opened with Version 6.10 and the same generated test
key. The decrypted archive was exactly equal. Schema remains 10, with no migration
or key replacement required. Its original viral results render with the new label
and bold names without changing the stored record.

The generated ReportLab preview is one Letter landscape page. It was rendered
and visually inspected. Its timestamp is at upper left. Positive viral names and
Candida parapsilosis use bold font spans. Negative culture text stays unbolded.

A separate generated-HTML check ran in headless Chromium using Playwright. With
the browser timezone set to Asia/Tokyo and a controlled instant, beforeprint
updated the stamp to the expected America/New_York date/time with EST. Both
positive names had bold markup. There were no JavaScript page errors. This tests
the downloaded HTML, not a Streamlit browser session or a physical printer.

## Limitations

The full Streamlit runtime/browser interface and authenticated private GitHub
storage were not tested. Installing Streamlit in this build environment failed
because package-host DNS resolution was unavailable. UI tests use a widget stub.
Mock storage checks do not establish live token permissions, network availability,
hosted concurrency behavior, or successful deployment.

A PDF records its download/preparation time and cannot update when the same saved
file is printed later. Printable HTML uses the browser beforeprint event. That
represents printing/print-preview initiation, not confirmation of a physical print.

Autosave applies to imported handoffs and editor values received by the server.
It does not parse unsubmitted paste-form text, save after a browser closes, or
recover a disconnected/expired browser session. In session-only mode no persistent
GitHub save occurs. A failed persistent save blocks the requested room change.

These checks do not establish clinical validity, patient identification, institutional
approval, privacy compliance, or a security audit of the hosting environment.
