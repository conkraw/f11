# PICU Handoff 6.10: room autosave and clean printing

Complete web-app ZIP. No direct code-repository change is made by distributing it.

## Update the existing app

1. Save open work before replacing the app files.
2. Extract PICU610.zip and open PICU_Handoff_v6_10_Workflow. Upload its contents
   into your existing application code repository, replacing matching files.
   Keep app.py at the repository root.
3. Include all Python files and requirements.txt. New modules are print_time.py
   and microbiology_display.py. The host must install Streamlit 1.52 or newer for
   click-time downloads and tzdata for Eastern-time rules. They are in requirements.txt.
4. Keep Streamlit Secrets, password hash, encryption key, GitHub token and private
   data repository unchanged. Do not rerun the secrets generator.
5. Restart the deployment. The sidebar identifies Version 6.10.

Storage schema remains 10. Existing handoffs, mapping rules, hidden medications
and source observations are preserved. No re-paste is needed for display changes.

## Cleaner workspace

All Load ... example buttons are removed from the handoff screen. The paste box,
Create / update handoff, editors, save controls, Admin and Print all remain.
Synthetic text files are still included in examples/ for optional manual testing.

## Automatic save before changing rooms

Selecting a different room saves the outgoing room's imported results and edits
through the existing encrypted storage path before the destination room opens.
Choosing Other room also saves before the current editor is hidden. Unchanged
saved handoffs do not create unnecessary commits. Only the outgoing handoff is
saved by a room change. Existing explicit Save and Save all actions remain.

If storage fails, a validation problem occurs, or the saved room has changed in
another session, the app keeps the current room and its editor values. The room
selector returns to the current room. A visible error explains that the save was
not confirmed. It does not silently advance or overwrite a conflicting record.

The snapshot captures editor values delivered with the room-switch event,
including a just-blurred text field. The original pasted SmartPhrase is not
saved in the archive. Click Create / update handoff to import pasted text before
switching rooms. Unsubmitted form text is not an imported handoff. Autosave does
not mean the app can save after a browser closes, disconnects or expires. Save
before logging out or closing the browser. In session-only test mode, the save
is session-only and the app explicitly says GitHub storage is not enabled.

## Print time at the upper left

Every PDF page, including continuation pages and Print all, shows a timestamp at
upper left. It is created at download time, not copied from the last saved time.
One print packet shares one timestamp. Printable HTML refreshes its timestamp
when the browser opens print preview or prints.

The timezone is America/New_York: EST in standard time and EDT during daylight
saving time, independent of the server or browser's local timezone. The source
handoff dates and values are not rewritten by this display change.

A downloaded PDF cannot detect a later physical printer action. Its heading
therefore says Print prepared. Regenerate it for a fresh timestamp when printing
later. HTML changes its heading to Printed on the browser's beforeprint event.
Plain-text exports include the preparation timestamp but cannot contain bold fonts.

## Viral heading and positive-organism emphasis

The O-block summary now reads Rapid Viral Panel: followed by the selected positive
viral names. The source SmartPhrase heading can remain Respiratory Viral Panel.
Source codes, dates, inclusion settings and positive-only selection are unchanged.

Positive viral targets and named culture organism results are bold in the screen
summary, handoff preview, PDF and printable HTML. For example, Candida parapsilosis
is bold, while the collection date and sample location remain normal weight.
No growth, negative, pending and administrative statuses are not emphasized.
The wording and provisional/final status of a result are not changed. Bolding is
a display aid, not a determination that an organism represents clinical infection.
Manually typed notes are kept as plain source text, not interpreted as HTML.

## Existing functionality retained

The compact landscape format, CBC/BMP trees and dates, horizontal hepatic and
coagulation summaries, CRP/procalcitonin in ID, separated culture groups,
SpO2 ranges, neurologic observations, measured weight/Z-score/dosing-weight order,
admission date, respiratory settings, medication taper/PN/ADS handling, remembered
system assignments, hidden/restorable medications and Print all remain included.
Long handoffs continue onto another page rather than having content cut off.

## Data boundaries

The app host receives pasted content before storage encryption. Existing private
archive checks and encryption remain. This update does not access your deployment
Secrets or private records from ChatGPT. No source data is put into this package.
Exports are unencrypted. Git history can retain older encrypted versions. A shared
app password, encryption and absence of a name/MRN field alone do not establish
institutional approval. Use only approved hosting/storage for clinical data.

## Testing and technical references

See TEST_REPORT.md for the actual checks and limitations. The preview is synthetic.
For an optional manual test, paste examples/synthetic_viral_positive.txt into a
room, create the handoff, edit a note, then switch rooms and reopen it. Verify the
save in your own deployment. Use the printable preview to check the header and bold names.

Implementation references:
- https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- https://docs.streamlit.io/1.52.0/develop/api-reference/widgets/st.download_button
- https://docs.python.org/3/library/zoneinfo.html
- https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeprint_event
