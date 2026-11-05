"""Landscape handoff with system columns, medication band, and bottom handoff rows.

Clinical content is escaped. PDF is generated in memory, without temporary files.
Long content continues onto additional landscape pages instead of being clipped.
"""
from __future__ import annotations
from html import escape
from io import BytesIO
from models import SYSTEMS, fields_with_medications, validate_sheet
from lab_layout import laboratory_flowables, laboratory_html, LabRow

COLUMNS = (("PATIENT", None), ("NEURO", "Neurologic"), ("RESP", "Respiratory"),
           ("CARDIAC", "Cardiovascular"), ("FEN / GI", "FEN / GI"),
           ("HEME", "Hematology"), ("ID", "Infectious Disease"), ("LABS", "Labs"))
WIDTHS = (0.12, 0.14, 0.17, 0.12, 0.15, 0.10, 0.10, 0.10)
BOTTOM = ("Other Medications", "Lab Results / Trends", "Goals / Follow-up")
ACCESS_FIELDS = ("Airway", "Last Intubation", "Access", "Drains / Tubes")


def handoff_text(sheet: dict) -> str:
    fields = fields_with_medications(sheet)
    parts = ["PICU HANDOFF", "Room: " + sheet["room"], "Handoff reference: " + sheet["id"][:8],
             "Saved (UTC): " + (sheet["updated_at"] or "Unsaved draft"),
             "Confirm patient identity in Epic. A room is not a patient identifier."]
    for section in SYSTEMS:
        content = fields[section].strip()
        if content:
            parts.extend(["", section.upper(), content])
    return "\n".join(parts) + "\n"


def patient_column(sheet: dict, fields: dict) -> str:
    lines = ["Room: " + sheet["room"]]
    if fields["Demographics / Weight"].strip():
        lines.append(fields["Demographics / Weight"].strip())
    if fields["Diagnoses"].strip():
        lines.append("Diagnoses:\n" + fields["Diagnoses"].strip())
    return "\n\n".join(lines)


def handoff_html(sheet: dict) -> str:
    fields = fields_with_medications(sheet, include_lab_text=False)
    headers = ''.join('<th>' + escape(label) + '</th>' for label, _ in COLUMNS)
    cells = ''.join('<td><div class="content">' + escape(patient_column(sheet, fields) if section is None else fields[section]) + '</div></td>' for _, section in COLUMNS)
    cols = ''.join(f'<col style="width:{w*100:.1f}%">' for w in WIDTHS)
    bands = []
    for key in BOTTOM:
        bands.append('<div class="band"><strong>' + escape(key) + ':</strong>' + (laboratory_html(sheet['labs']) if key == 'Lab Results / Trends' else '') + '<span class="content">' + escape(fields[key]) + '</span></div>')
    extra = '\n'.join(k + ': ' + fields[k] for k in ('Skin / Wounds', 'Tasks', 'Other') if fields[k].strip())
    if extra:
        bands.insert(2, '<div class="band"><strong>Additional notes:</strong> <span class="content">' + escape(extra) + '</span></div>')
    access = ''.join('<td><strong>' + escape(key) + ':</strong> <span class="content">' + escape(fields[key]) + '</span></td>' for key in ACCESS_FIELDS)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>PICU handoff</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:18px;background:#eee;color:#111;font-family:"Times New Roman",serif}
main{width:11in;min-height:8.5in;margin:0 auto;background:white;padding:.28in .30in}
.meta{font:10px Arial,sans-serif;margin-bottom:9px;display:flex;justify-content:space-between}
table{border-collapse:collapse;width:100%;table-layout:fixed}th{font-size:10pt;text-align:center;padding:3px;border-bottom:1px solid black}
.systems td{border:1px solid black;vertical-align:top;height:4.05in;padding:4px;font-size:8.5pt;line-height:1.08}
.content{white-space:pre-wrap;overflow-wrap:anywhere}.band{border:1px solid black;border-top:0;font-size:9pt;line-height:1.15;padding:5px;min-height:24px}
.access{font-size:9pt}.access td{vertical-align:top;border:1px solid black;border-top:0;padding:5px;overflow-wrap:anywhere}
.labcards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:4px;align-items:start}.labcard{width:100%;height:auto;border:1px solid #888;break-inside:avoid}.labnote{font:7.5pt/1.2 "Times New Roman",serif;margin:3px 0}
footer{font:9px/1.3 Arial,sans-serif;margin-top:7px}
@page{size:letter landscape;margin:.3in}
@media print{body{margin:0;padding:0;background:white}main{width:100%;min-height:0;padding:0;margin:0}.systems td{height:3.95in}thead{display:table-header-group}footer{font-size:7pt}.band{break-inside:auto}}
</style></head><body><main><div class="meta"><span>PICU HANDOFF | Room ''' + escape(sheet['room']) + '''</span><span>Reference ''' + escape(sheet['id'][:8]) + ' | Saved (UTC): ' + escape(sheet['updated_at'] or 'Unsaved draft') + '''</span></div>
<table class="systems"><colgroup>''' + cols + '</colgroup><thead><tr>' + headers + '</tr></thead><tbody><tr>' + cells + '</tr></tbody></table>' + ''.join(bands) + '<table class="access"><tbody><tr>' + access + '''</tr></tbody></table>
<footer>Confirm the current patient in Epic. Blank sections are not confirmed normal. Downloaded copies are not encrypted. Infusion rates reflect the source Last Rate, not a live feed.</footer>
</main></body></html>'''


def _pdf_text(text: str) -> str:
    """Helvetica covers Latin-1. Normalize common clinical symbols explicitly."""
    for a, b in {'\u00a0':' ', '₂':'2', '₃':'3', '₄':'4', '⁺':'+', '⁻':'-', '−':'-', '–':'-', '—':'-', 'μ':'µ', '→':' -> ', '≤':'<=', '≥':'>=', '•':''}.items():
        text = text.replace(a, b)
    return text


def handoffs_pdf(sheets: list[dict]) -> bytes:
    """One landscape document. Each room starts on a new page, in memory only."""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.pdfgen import canvas
    if not sheets or len(sheets) > 100:
        raise ValueError("Select between 1 and 100 handoffs to print.")
    for sheet in sheets:
        validate_sheet(sheet)
    if len({s["room"] for s in sheets}) != len(sheets):
        raise ValueError("A room cannot be included twice in one print packet.")
    output = BytesIO()
    width, height = landscape(letter)
    c = canvas.Canvas(output, pagesize=(width, height), pageCompression=1)
    c.setTitle("PICU handoffs")
    c.setAuthor("")
    for position, sheet in enumerate(sheets, 1):
        _draw_sheet(c, sheet, width, height, position, len(sheets))
    c.save()
    return output.getvalue()


def handoff_pdf(sheet: dict) -> bytes:
    return handoffs_pdf([sheet])


def _draw_sheet(c, sheet: dict, width: float, height: float, position: int = 1, count: int = 1) -> None:
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    fields = fields_with_medications(sheet, include_lab_text=False)
    margin = 21.6
    total_width = width - 2 * margin
    widths = [total_width * v for v in WIDTHS]
    font_size, leading = 8.2, 9.4
    normal = ParagraphStyle('clinical', fontName='Times-Roman', fontSize=font_size, leading=leading,
                            splitLongWords=True, spaceAfter=0, allowWidows=1, allowOrphans=1)
    wide = ParagraphStyle('bands', parent=normal, fontSize=9, leading=10.5)

    def paragraphs(text: str, style=normal):
        if not text.strip():
            return []
        return [Paragraph(escape(_pdf_text(line)) if line else '&#160;', style) for line in text.split('\n')]

    queues = [paragraphs(patient_column(sheet, fields) if s is None else fields[s]) for _, s in COLUMNS]
    band_items = [(k, fields[k]) for k in BOTTOM]
    extra = '\n'.join(k + ': ' + fields[k] for k in ('Skin / Wounds', 'Tasks', 'Other') if fields[k].strip())
    if extra:
        band_items.insert(2, ('Additional notes', extra))
    bands = [(k, (laboratory_flowables(sheet["labs"], total_width-8) if k == "Lab Results / Trends" else []) + paragraphs(value, wide)) for k, value in band_items]
    access = [(k, paragraphs(fields[k], wide)) for k in ACCESS_FIELDS]

    def needed(queue, w):
        return sum(p.wrap(w, 100000)[1] for p in queue)

    def draw_queue(queue, x, y, w, available):
        """Draw into one cell and return leftover flowables. No clipping."""
        remaining = list(queue)
        while remaining and available >= leading + .1:
            p = remaining[0]
            _, h = p.wrap(w, available)
            if h <= available + .01:
                p.drawOn(c, x, y-h)
                y -= h
                available -= h
                remaining.pop(0)
            else:
                parts = p.split(w, available)
                if not parts:
                    break
                first = parts[0]
                _, h = first.wrap(w, available)
                if h > available + .1:
                    break
                first.drawOn(c, x, y-h)
                y -= h
                available -= h
                remaining = parts[1:] + remaining[1:]
        return remaining

    page = 0
    while True:
        page += 1
        if page > 150:
            raise ValueError('The handoff is too long to export safely. Shorten it or export text.')
        c.setFont('Helvetica', 8)
        c.drawString(margin, height-margin-5, 'PICU HANDOFF | Room ' + sheet['room'] + (' | Continued' if page > 1 else ''))
        c.drawRightString(width-margin, height-margin-5, 'Sheet ' + str(position) + '/' + str(count) + ' | Reference ' + sheet['id'][:8] + ' | Page ' + str(page))
        y = height-margin-17
        # Keep all eight columns, matching the supplied handoff. Continue long columns.
        main_needed = max((needed(q, w-8) for q, w in zip(queues, widths)), default=0)
        main_height = min(280 if sheet["labs"]["rows"] else 300, max((190 if sheet["labs"]["rows"] else 260) if page == 1 else 28, main_needed+8))
        c.setLineWidth(.6)
        x = margin
        for (label, _), w, q in zip(COLUMNS, widths, queues):
            c.setFont('Times-Bold', 9)
            c.drawCentredString(x+w/2, y-10, label)
            c.line(x, y-14, x+w, y-14)
            x += w
        y -= 14
        updated = []
        x = margin
        for w, q in zip(widths, queues):
            c.rect(x, y-main_height, w, main_height)
            updated.append(draw_queue(q, x+4, y-4, w-8, main_height-8))
            x += w
        queues = updated
        y -= main_height
        updated_bands = []
        # Reserve room for the access row and a readable footer on every page.
        available_bands = y - (margin + 54)
        for index, (label, queue) in enumerate(bands):
            label_height = 12
            reserve = (len(bands)-index-1) * 23
            limit = max(23, min(450 if label == "Lab Results / Trends" else 105, available_bands-reserve))
            bh = max(23, min(limit, needed(queue, total_width-10) + label_height+6))
            if label == 'Lab Results / Trends' and any(isinstance(item, LabRow) for item in queue):
                # Reserve only space actually usable on this page, not blank
                # space left by a whole tree row that must move to the next page.
                used = 0.0
                capacity = max(0.0, limit-label_height-5)
                for item in queue:
                    _, item_height = item.wrap(total_width-8, capacity-used)
                    if item_height + used > capacity + .01:
                        break
                    used += item_height
                bh = max(23, min(limit, used+label_height+6))
            c.rect(margin, y-bh, total_width, bh)
            c.setFont('Times-Bold', 9)
            c.drawString(margin+4, y-10, label + (':' if page == 1 else ' (continued):'))
            rest = draw_queue(queue, margin+4, y-label_height-2, total_width-8, bh-label_height-5)
            updated_bands.append((label, rest))
            y -= bh
            available_bands -= bh
        bands = updated_bands
        aw = total_width/4
        ah = max(30, min(48, y-margin-18))
        updated_access = []
        for index, (label, queue) in enumerate(access):
            x = margin+index*aw
            c.rect(x,y-ah,aw,ah)
            c.setFont('Times-Bold',9)
            c.drawString(x+4,y-10,label+':')
            rest = draw_queue(queue,x+4,y-14,aw-8,ah-17)
            updated_access.append((label,rest))
        access=updated_access
        c.setFont('Helvetica',6.7)
        c.drawString(margin, margin-1, 'Confirm the current patient in Epic. Blank sections are not confirmed normal. Downloaded copies are not encrypted.')
        c.drawRightString(width-margin, margin-10, 'Last Rate is a recorded source value, not a live pump feed.')
        c.showPage()
        if not any(queues) and not any(q for _,q in bands) and not any(q for _,q in access):
            break


def handoffs_html(sheets: list[dict]) -> str:
    if not sheets or len(sheets) > 100:
        raise ValueError("Select between 1 and 100 handoffs to print.")
    if len({s["room"] for s in sheets}) != len(sheets):
        raise ValueError("A room cannot be included twice in one print packet.")
    docs = [handoff_html(sheet) for sheet in sheets]
    head = docs[0].split("</head>", 1)[0]
    head += """<style>
main{margin-bottom:24px}.printbar{font:15px Arial,sans-serif;max-width:11in;margin:0 auto 18px}
.printbar button{padding:10px 16px;cursor:pointer}
@media print{.printbar{display:none}main{break-after:page;margin:0}main:last-child{break-after:auto}}
</style></head>"""
    pages = ["<main>" + doc.split("<main>", 1)[1].split("</main>", 1)[0] + "</main>" for doc in docs]
    return head + '<body><div class="printbar"><button onclick="window.print()">Print all handoffs</button> Landscape Letter. Each room starts on a new page.</div>' + "".join(pages) + "</body></html>"
