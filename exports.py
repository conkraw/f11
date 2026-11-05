"""Printable UTF-8 handoff. Clinical text is escaped, never treated as HTML."""
from html import escape
from models import SYSTEMS, validate_sheet


def handoff_text(sheet: dict) -> str:
    validate_sheet(sheet)
    parts = ["PICU HANDOFF", "Room: " + sheet["room"], "Handoff reference: " + sheet["id"][:8],
             "Saved (UTC): " + (sheet["updated_at"] or "Unsaved draft"),
             "Confirm patient identity in Epic. A room is not a patient identifier."]
    for section in SYSTEMS:
        content = sheet["fields"][section].strip()
        if content:
            parts.extend(["", section.upper(), content])
    return "\n".join(parts) + "\n"


def handoff_html(sheet: dict) -> str:
    validate_sheet(sheet)
    sections = []
    for section in SYSTEMS:
        content = sheet["fields"][section].strip()
        if content:
            sections.append('<section><h2>' + escape(section) + '</h2><div class="content">' + escape(content) + '</div></section>')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>PICU handoff</title>
<style>
body{font:15px/1.5 Arial,sans-serif;color:#172c3d;background:#edf2f6;margin:0;padding:32px}
main{max-width:900px;margin:auto;background:white;padding:40px;border:1px solid #d7e0e8}
.kicker{font-size:12px;letter-spacing:2px;color:#356474}h1{font-size:30px;margin:8px 0}
.meta{font-size:12px;color:#506373;padding-bottom:18px;border-bottom:2px solid #245766}
h2{font-size:15px;text-transform:uppercase;color:#245766;margin:0 0 10px}
section{padding:18px 0;border-bottom:1px solid #d7e0e8;break-inside:avoid}
.content{white-space:pre-wrap;overflow-wrap:anywhere}footer{font-size:11px;color:#506373;margin-top:24px}
@media print{body{background:white;padding:0;font-size:11pt}main{padding:0;border:0;max-width:none}h1{font-size:21pt}section{break-inside:auto}h2{break-after:avoid}}
@page{size:letter;margin:0.6in}
</style></head><body><main><div class="kicker">PICU / HANDOFF</div><h1>Room ''' + escape(sheet["room"]) + '''</h1>
<div class="meta">Reference ''' + escape(sheet["id"][:8]) + ' | Saved (UTC): ' + escape(sheet["updated_at"] or "Unsaved draft") + '''<br>
Confirm the current patient in Epic. Room assignment alone does not establish identity.</div>''' + "".join(sections) + '''
<footer>Review copy. Blank sections are omitted, not confirmed normal. This downloaded file is not encrypted.</footer>
</main></body></html>'''
