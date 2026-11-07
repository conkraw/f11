"""Team instructions and reusable Epic source text, never a patient handoff.

Published separately from the clinical vault. An empty source is intentional:
expanded sample results cannot reconstruct an institution's SmartLinks.
"""
from __future__ import annotations
from datetime import datetime, timezone
from html import escape
import re

MAX_TEMPLATE = 80000
MAX_INSTRUCTIONS = 32000
MAX_NOTES = 8000
DEFAULT_INSTRUCTIONS = """# Create a handoff you can check and trust

Use this guide to turn one patient's Epic SmartPhrase output into an editable, system-based handoff. Before sharing it, compare the information with Epic and confirm that your changes are saved.

## Before your first handoff

Open Instructions / SmartPhrase in the sidebar to find the team's current SmartPhrase name and reusable source text. If the SmartPhrase is already available in Epic, use its name there. If you need to add it to your own Epic SmartPhrases, use the source text and your local Epic instructions. Ask your app administrator if the name or source has not been published. Do not use an example patient's results as a template.

You need only the app password for routine handoffs. The separate Admin password is for managing the shared guide, SmartPhrase, and Admin settings.

## 1. Open the app

Sign in with the app password. Open Epic in a separate window so you can compare the source with your handoff. Use only your team's approved hosting and data-handling workflow.

## 2. Go to Handoff

Choose Handoff in the sidebar. The Instructions and Epic SmartPhrase panel is available above the room selector whenever you need it.

## 3. Choose the patient's room

Select the room and confirm that it matches the patient whose chart is open in Epic. Choose Other room if the room is not listed. If a new patient is occupying a previously used room, open Start over / reload and choose Start blank for new patient before importing. This clears the open draft, so use it only when starting a new occupant's handoff.

## 4. Run the SmartPhrase in Epic

Use the current team SmartPhrase in the correct patient's chart and encounter. Let it finish populating. Copy the generated text, including the repeated-letter section dividers, table headings, dates, times, and results. Copy one patient at a time. Copy directly from Epic to help preserve the table columns. Do not copy the reusable source definition into the handoff paste box.

## 5. Paste the generated text

In Handoff, open Paste / create and paste into SmartPhrase text. Check the room again before continuing. Do not add names, MRNs, or other identifiers that your approved workflow does not permit. A room number does not make clinical text anonymous.

## 6. Click Create / update handoff

The app organizes the supported sections into the draft. Read any warnings. A skipped section was not refreshed, and an excluded value may be missing from the output. Compare it with Epic and correct or re-paste the affected section. Do not assume that an incomplete import is ready to use. Technical error references are available in Import errors for later review.

## 7. Review, edit, and preview

Use Medications, Labs / Vitals, Cultures, Labs/Imaging, and Edit handoff to correct the draft. Check doses and infusion rates, respiratory support, result dates, weight and dosing weight, and any retained information. Unmapped medications appear in Other Medications. You can assign their system or hide an entry without deleting it. Remembered mapping and hiding choices can affect later imports for the team. Open Preview / print and compare the finished sheet with Epic. Add your assessment, tasks, and follow-up notes where needed. The handoff supports communication and does not replace the chart or current orders.

## 8. Save and confirm

Click Save handoff. Confirm the saved status and the Last saved to GitHub date and time. Changing rooms also saves the current imported draft when storage is enabled, but text only pasted into the box is not imported or saved until you click Create / update handoff. Save before logging out or closing the tab. A failed save is not a saved handoff. Session-only testing does not persist data to GitHub.

## Print the team's handoffs

Open Print all, select the rooms you need, and click Save all open handoffs. Check each room's saved status and date/time above the download controls. Download all selected handoffs (PDF), open it, and print in landscape. Each room starts on a new page. Downloading or printing alone does not save drafts. The print-preparation time is separate from the last-save time. Handle downloaded and printed sheets according to your team's approved policy, then log out.

## Updating only part of a handoff

Paste a complete pair of dividers around each section you want to update. An omitted section keeps its previous content. An included empty section can clear its automatic content. Separate notes remain separate, so review older notes when updating a handoff. Never combine patients in one paste.

## Working with others

Use Reload saved archive to see another user's confirmed saves. If a conflict appears, compare your draft with the saved handoff before making changes. Ask the administrator to change the shared SmartPhrase or guide. Do not put passwords, tokens, or patient results into those shared teaching fields.
"""


def default_guide() -> dict:
    return dict(schema=1, smartphrase_name="", smartphrase_text="", setup_notes="",
                instructions=DEFAULT_INSTRUCTIONS, updated_at=None)


def validate_guide(value: dict) -> None:
    expected = {"schema", "smartphrase_name", "smartphrase_text", "setup_notes", "instructions", "updated_at"}
    if not isinstance(value, dict) or set(value) != expected or type(value["schema"]) is not int or value["schema"] != 1:
        raise ValueError("The saved user guide has an unsupported structure. Nothing was overwritten.")
    for key, limit in (("smartphrase_name", 120), ("smartphrase_text", MAX_TEMPLATE),
                       ("setup_notes", MAX_NOTES), ("instructions", MAX_INSTRUCTIONS)):
        text = value[key]
        if not isinstance(text, str) or len(text) > limit or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
            raise ValueError("A user-guide field is invalid or too long.")
    if "\n" in value["smartphrase_name"] or "\r" in value["smartphrase_name"]:
        raise ValueError("The SmartPhrase name must fit on one line.")
    if not value["instructions"].strip():
        raise ValueError("Enter the user instructions before saving.")
    stamp = value["updated_at"]
    if stamp is not None:
        try:
            when = datetime.fromisoformat(stamp)
            if when.tzinfo is None or when.utcoffset() is None:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("The user-guide timestamp is invalid.") from None


def publication(name: str, source: str, notes: str, instructions: str) -> dict:
    """Do not strip indentation/tabs in the reusable SmartPhrase source."""
    result = dict(schema=1, smartphrase_name=name.strip(), smartphrase_text=source,
                  setup_notes=notes, instructions=instructions,
                  updated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    validate_guide(result)
    return result


def instructions_html(value: dict) -> str:
    """Portable learner guide. All administrator-supplied text is escaped."""
    validate_guide(value)
    sections = []
    for block in value["instructions"].split("\n\n"):
        block = block.strip()
        if not block:
            continue
        tag = "h2" if block.startswith("## ") else "h1" if block.startswith("# ") else "p"
        text = block[3:] if tag == "h2" else block[2:] if tag == "h1" else block
        sections.append(f"<{tag}>" + escape(text).replace("\n", "<br>") + f"</{tag}>")
    name = escape(value["smartphrase_name"]) or "Not yet published by the administrator"
    source = value["smartphrase_text"]
    phrase = '<h2>Team Epic SmartPhrase</h2><p>Name: <code>' + name + '</code></p>'
    if value["setup_notes"]:
        phrase += '<p>' + escape(value["setup_notes"]).replace("\n", "<br>") + '</p>'
    if source.strip():
        phrase += '<details><summary>Reusable source text</summary><pre>' + escape(source) + '</pre></details>'
    else:
        phrase += '<p>The source definition has not been published. Ask your app administrator. The guide does not reconstruct SmartLinks from sample patient results.</p>'
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PICU Handoff user guide</title><style>
body{font:16px/1.65 system-ui,Arial,sans-serif;color:#243749;background:#f3f6f8;margin:0;padding:28px}main{max-width:850px;margin:auto;background:white;padding:36px 42px;border:1px solid #d7e1e8;border-radius:10px}h1{font-size:29px;line-height:1.25;color:#123c53}h2{font-size:20px;line-height:1.35;margin-top:29px;color:#123c53}p{margin:12px 0}code{background:#edf2f5;padding:3px 6px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 monospace;background:#edf2f5;padding:16px}details{margin:14px 0}header{border-bottom:1px solid #d7e1e8;padding-bottom:18px;margin-bottom:24px}small{color:#566d7d}@media(max-width:600px){body{padding:8px}main{padding:20px}}@media print{body{background:white;padding:0}main{border:0;padding:0}h2{break-after:avoid}p{orphans:3;widows:3}}
</style></head><body><main><header><small>PICU HANDOFF / USER GUIDE</small>''' + phrase + '</header>' + ''.join(sections) + '</main></body></html>'
