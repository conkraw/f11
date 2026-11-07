"""Landscape handoff with system columns, medication band, and bottom handoff rows.

Clinical content is escaped. PDF is generated in memory, without temporary files.
Long content continues onto additional landscape pages instead of being clipped.
"""
from __future__ import annotations
from html import escape
from io import BytesIO
from copy import deepcopy
from datetime import datetime
import time
import re
from import_review import review_summary
from models import SYSTEMS, fields_with_medications, validate_sheet, automatic_vitals, section_label
from infusions import (neuro_body, cardiovascular_body, hematology_body, is_infusion, infusion_entry,
                       system_body_blocks, render_body_blocks)
from labs import lactate_text
from medications import visible, format_medication
from output_text import medication_output
from fen_gi import effective_section, fen_gi_body
from lab_layout import laboratory_flowables, laboratory_html, LabRow
from cultures import cultures_text
from viral import viral_text
from microbiology_display import culture_markup, viral_markup
from print_time import eastern_print_time, PRINT_TIME_SCRIPT

COLUMNS = (("PATIENT", None), ("NEURO", "Neurologic"), ("RESP", "Respiratory"),
           ("CARDIAC", "Cardiovascular"), ("FEN / GI", "FEN / GI"),
           ("HEME", "Hematology"), ("ID", "Infectious Disease"), ("LABS/IMAGING", "Labs"))
WIDTHS = (0.12, 0.14, 0.17, 0.12, 0.15, 0.10, 0.10, 0.10)
BOTTOM = ("Other Medications", "Lab Results / Trends", "Goals / Follow-up")
ACCESS_FIELDS = ("Airway", "Last Intubation", "Access", "Drains / Tubes")


def handoff_text(sheet: dict, printed_at: datetime | None = None) -> str:
    fields = fields_with_medications(sheet)
    parts = ["Print prepared: " + eastern_print_time(printed_at), "PICU HANDOFF", "Room: " + sheet["room"], "Handoff reference: " + sheet["id"][:8],
             "Saved (UTC): " + (sheet["updated_at"] or "Unsaved draft"),
             "Confirm patient identity in Epic. A room is not a patient identifier."]
    if review_summary(sheet):
        parts.extend(["", review_summary(sheet)])
    for section in SYSTEMS:
        content = fields[section].strip()
        if content:
            parts.extend(["", section_label(section).upper(), content])
    return "\n".join(parts) + "\n"


def patient_column(sheet: dict, fields: dict) -> str:
    lines = ["Room: " + sheet["room"]]
    if fields["Demographics / Weight"].strip():
        lines.append(fields["Demographics / Weight"].strip())
    if fields["Diagnoses"].strip():
        heading = "Diagnoses:\n" if sheet["fields"]["Diagnoses"].strip() else ""
        lines.append(heading + fields["Diagnoses"].strip())
    return "\n\n".join(lines)


def field_markup(sheet: dict, fields: dict, section: str, esc=escape) -> str:
    """Bold only generated microorganism names, never arbitrary source markup."""
    text = fields[section]
    if section == "FEN / GI":
        return fen_gi_body(sheet["fields"][section], sheet["medications"], sheet["intake_output"], True, esc)
    if section in ("Neurologic", "Cardiovascular", "Hematology"):
        body = render_body_blocks(system_body_blocks(section, sheet["fields"][section], sheet["medications"]), True, esc)
        before = [automatic_vitals(sheet).get(section, "")]
        if section == "Cardiovascular":
            before.append(lactate_text(sheet["labs"]))
        return "\n-----\n".join([esc(v) for v in before if v.strip()] + ([body] if body.strip() else []))
    if section == "Diagnoses":
        plain = viral_text(sheet["viral_panel"])
        if plain and text.endswith(plain):
            return esc(text[:-len(plain)]) + viral_markup(sheet["viral_panel"], esc)
    if section == "Infectious Disease":
        plain = cultures_text(sheet["cultures"])
        if plain:
            index = text.find(plain)
            if index >= 0:
                return esc(text[:index]) + culture_markup(sheet["cultures"], esc) + esc(text[index+len(plain):])
    return esc(text)


def patient_markup(sheet: dict, fields: dict, esc=escape) -> str:
    lines = [esc("Room: " + sheet["room"])]
    if fields["Demographics / Weight"].strip():
        lines.append(field_markup(sheet, fields, "Demographics / Weight", esc).strip())
    if fields["Diagnoses"].strip():
        heading = "Diagnoses:\n" if sheet["fields"]["Diagnoses"].strip() else ""
        lines.append(heading + field_markup(sheet, fields, "Diagnoses", esc).strip())
    return "\n\n".join(lines)


def handoff_html(sheet: dict, printed_at: datetime | None = None) -> str:
    fields = fields_with_medications(sheet, include_lab_text=False)
    headers = ''.join('<th>' + escape(label) + '</th>' for label, _ in COLUMNS)
    cells = ''.join('<td><div class="content">' + (patient_markup(sheet, fields) if section is None else field_markup(sheet, fields, section)) + '</div></td>' for _, section in COLUMNS)
    cols = ''.join(f'<col style="width:{w*100:.1f}%">' for w in WIDTHS)
    bands = []
    for key in BOTTOM:
        bands.append('<div class="band"><strong>' + escape(key) + ':</strong>' + (laboratory_html(sheet['labs'], blood_gas=sheet['blood_gas'], cbc=sheet['cbc']) if key == 'Lab Results / Trends' else '') + '<span class="content">' + escape(fields[key]) + '</span></div>')
    extra = '\n'.join(k + ': ' + fields[k] for k in ('Skin / Wounds', 'Tasks', 'Other') if fields[k].strip())
    if extra:
        bands.insert(2, '<div class="band"><strong>Additional notes:</strong> <span class="content">' + escape(extra) + '</span></div>')
    access = ''.join('<td><strong>' + escape(key) + ':</strong> <span class="content">' + escape(fields[key]) + '</span></td>' for key in ACCESS_FIELDS)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>PICU handoff</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:18px;background:#eee;color:#111;font-family:"Times New Roman",serif}
main{width:11in;min-height:8.5in;margin:0 auto;background:white;padding:.25in}
.meta{font:10px Arial,sans-serif;margin-bottom:5px;display:flex;justify-content:space-between}
table{border-collapse:collapse;width:100%;table-layout:fixed}th{font-size:8pt;text-align:center;padding:2px;border-bottom:1px solid black}
.systems td{border:1px solid black;vertical-align:top;height:auto;min-height:0;padding:3px;font-size:7.2pt;line-height:1.14}
.import-review{font:bold 7pt/1.15 Arial,sans-serif;border:1px solid #222;padding:3px;margin-bottom:3px;overflow-wrap:anywhere}.content{white-space:pre-wrap;overflow-wrap:anywhere}.band{border:1px solid black;border-top:0;font-size:7.2pt;line-height:1.14;padding:3px;min-height:15px}
.access{font-size:7.2pt}.access td{vertical-align:top;border:1px solid black;border-top:0;padding:3px;overflow-wrap:anywhere}
.labcards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:3px;align-items:start}.labcard{width:100%;height:auto;border:1px solid #888;break-inside:avoid}.labnote{font:6.1pt/1.15 "Times New Roman",serif;margin:1px 0}.lab-summary{font:7.2pt/1.14 "Times New Roman",serif;overflow-wrap:anywhere;margin:1px 0}.lab-full{grid-column:1/-1}
footer{font:6.1pt/1.2 Arial,sans-serif;margin-top:4px}
@page{size:letter landscape;margin:.25in}
@media print{body{margin:0;padding:0;background:white}main{width:100%;min-height:0;padding:0;margin:0}.systems td{height:auto}thead{display:table-header-group}footer{font-size:6.1pt}.band{break-inside:auto}}
</style></head><body><main><div class="meta"><span><span data-print-label>Print prepared: </span><span data-print-time>''' + escape(eastern_print_time(printed_at)) + '''</span> | Room ''' + escape(sheet['room']) + '''</span><span>Reference ''' + escape(sheet['id'][:8]) + ' | PICU HANDOFF' + '</span></div>' + ('<div class="import-review">' + escape(review_summary(sheet)) + '</div>' if review_summary(sheet) else '') + '''
<table class="systems"><colgroup>''' + cols + '</colgroup><thead><tr>' + headers + '</tr></thead><tbody><tr>' + cells + '</tr></tbody></table>' + ''.join(bands) + '<table class="access"><tbody><tr>' + access + '''</tr></tbody></table>
<footer>Confirm the current patient in Epic. Blank sections are not confirmed normal. Downloaded copies are not encrypted. Infusion rates reflect the source Last Rate, not a live feed.</footer>
</main>''' + PRINT_TIME_SCRIPT + '</body></html>'


def _pdf_text(text: str) -> str:
    """Helvetica covers Latin-1. Normalize common clinical symbols explicitly."""
    for a, b in {'\u00a0':' ', '₂':'2', '₃':'3', '₄':'4', '⁺':'+', '⁻':'-', '−':'-', '–':'-', '—':'-', 'μ':'µ', '→':' -> ', '≤':'<=', '≥':'>=', '•':''}.items():
        text = text.replace(a, b)
    return text


def handoffs_pdf(sheets: list[dict], printed_at: datetime | None = None) -> bytes:
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
    stamp = eastern_print_time(printed_at)
    for position, sheet in enumerate(sheets, 1):
        _draw_sheet(c, sheet, width, height, position, len(sheets), stamp)
    c.save()
    return output.getvalue()


def handoff_pdf(sheet: dict, printed_at: datetime | None = None) -> bytes:
    return handoffs_pdf([sheet], printed_at)


# Print layout is independent of persisted handoff content or encryption schema.
# Clinical text may shrink only within this explicit, bounded range. Beyond it,
# pagination is used. Nothing is cropped or silently left out to force one page.
PRINT_FONT_SIZES = (7.2, 7.0, 6.8, 6.5)
PRINT_MARGIN = 18.0
BAND_LABEL_HEIGHT = 10.0
BAND_PADDING = 5.0


def _queue_height(queue, width: float) -> float:
    return sum(item.wrap(width, 100000)[1] for item in queue)


def _clinical_markup(text: str) -> str:
    value = escape(_pdf_text(text))
    # Keep short score/value pairs together at a line boundary. This changes
    # layout only, never the underlying score or stored text.
    return re.sub(r"\b(SBS|RASS)\s+([+-]?\d+(?:\.\d+)?)", r"\1&#160;\2", value)


def _make_pdf_plan(sheet: dict, page_width: float, font_size: float) -> dict:
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer
    fields = fields_with_medications(sheet, include_lab_text=False)
    total_width = page_width - 2 * PRINT_MARGIN
    widths = [total_width * value for value in WIDTHS]
    style = ParagraphStyle('compact-clinical', fontName='Times-Roman', fontSize=font_size,
                           leading=font_size+1, splitLongWords=True, spaceAfter=0,
                           allowWidows=1, allowOrphans=1)

    def paragraphs(text, rich=False):
        if not text.strip():
            return []
        return [Paragraph((line if rich else _clinical_markup(line)) if line else '&#160;', style)
                for line in text.split('\n')]

    columns = [paragraphs(patient_markup(sheet, fields, _clinical_markup) if section is None else field_markup(sheet, fields, section, _clinical_markup), rich=True)
               for _, section in COLUMNS]
    # Use the same grouping model as HTML/text. Keep each infusion's name and
    # ordered dose together, including the heading with the first infusion.
    class InfusionParagraph(Paragraph):
        def split(self, availWidth, availHeight):
            if self.height <= 200:
                return []
            return super().split(availWidth, availHeight)
    for column_index, (_, section) in enumerate(COLUMNS):
        if section not in ("Neurologic", "Cardiovascular", "Hematology"):
            continue
        blocks = system_body_blocks(section, sheet["fields"][section], sheet["medications"])
        q = []
        before = [automatic_vitals(sheet).get(section, "")]
        if section == "Cardiovascular":
            before.append(lactate_text(sheet["labs"]))
        before = [v for v in before if v.strip()]
        if before:
            q.extend(paragraphs("\n-----\n".join(before) + ("\n-----" if blocks else "")))
        index = 0
        while index < len(blocks):
            kind, item = blocks[index]
            prefix = ""
            if kind == "heading" and index + 1 < len(blocks) and blocks[index + 1][0] == "infusion":
                prefix = "<b>" + _clinical_markup(item) + "</b>\n"
                index += 1
                kind, item = blocks[index]
            if kind == "infusion":
                markup = prefix + infusion_entry(item, True, _clinical_markup, handoff_only=True)
                q.append(InfusionParagraph(markup.replace("\n", "<br/>"), style))
            else:
                q.extend(paragraphs(render_body_blocks([(kind, item)], True, _clinical_markup), rich=True))
            index += 1
        columns[column_index] = q
    band_items = [(name, fields[name]) for name in BOTTOM]
    extra = '\n'.join(name + ': ' + fields[name] for name in ('Skin / Wounds', 'Tasks', 'Other')
                      if fields[name].strip())
    if extra:
        band_items.insert(2, ('Additional notes', extra))
    bands = [(name, (laboratory_flowables(sheet['labs'], total_width-6, font_size, blood_gas=sheet['blood_gas'], cbc=sheet['cbc'])
                    if name == 'Lab Results / Trends' else []) + paragraphs(text))
             for name, text in band_items]
    access = [(name, paragraphs(fields[name])) for name in ACCESS_FIELDS]
    review = review_summary(sheet)
    banner = Paragraph(escape(review), ParagraphStyle('review', fontName='Helvetica-Bold', fontSize=7, leading=8)) if review else None
    review_height = banner.wrap(total_width, 10000)[1] + 4 if banner else 0
    return {'review_banner': banner, 'review_height': review_height,
            'font_size': font_size, 'leading': font_size+1, 'width': total_width,
            'widths': widths, 'columns': columns, 'bands': bands, 'access': access}


def _plan_heights(plan: dict) -> tuple[float, list[float], float]:
    width = plan['width']
    main = max(20, max((_queue_height(q, w-6) for q, w in zip(plan['columns'], plan['widths'])), default=0)+6)
    bands = [max(15, _queue_height(q, width-6) + BAND_LABEL_HEIGHT + BAND_PADDING)
             for _, q in plan['bands']]
    access = max(24, max((_queue_height(q, width/4-6) for _, q in plan['access']), default=0)+14)
    return main, bands, access


def _select_pdf_plan(sheet: dict, width: float, height: float) -> tuple[dict, bool]:
    # Meta line 16 pt, column headings 12 pt, footer 18 pt, plus both margins.
    available = height - 2 * PRINT_MARGIN - 46
    original = None
    for size in PRINT_FONT_SIZES:
        plan = _make_pdf_plan(sheet, width, size)
        if original is None:
            original = plan
        main, bands, access = _plan_heights(plan)
        if main + sum(bands) + access <= available - plan['review_height'] + .01:
            return plan, True
    # Do not leave a multi-page handoff needlessly tiny when a single page is
    # impossible. Revert to the default compact size and keep every item.
    return original, False


def print_layout_info(sheet: dict) -> dict:
    """Patient-free layout status for UI/tests. No source content is returned."""
    plan, fits = _select_pdf_plan(sheet, 792, 612)
    return {'font_size': plan['font_size'], 'fits_one_page': fits}


def _draw_sheet(c, sheet: dict, width: float, height: float, position: int = 1, count: int = 1, print_stamp: str | None = None) -> None:
    print_stamp = print_stamp or eastern_print_time()
    plan, _ = _select_pdf_plan(sheet, width, height)
    margin = PRINT_MARGIN
    total_width = plan['width']
    widths = plan['widths']
    leading = plan['leading']
    queues, bands, access = plan['columns'], plan['bands'], plan['access']
    # Top of columns after the metadata and column headings.
    column_top = height-margin-28-plan['review_height']
    body_height = column_top-(margin+18)

    def draw_queue(queue, x, y, w, available):
        remaining = list(queue)
        while remaining and available > .01:
            item = remaining[0]
            _, h = item.wrap(w, available)
            if h <= available + .01:
                item.drawOn(c, x, y-h)
                y -= h
                available -= h
                remaining.pop(0)
                continue
            parts = item.split(w, available)
            if not parts:
                break
            first = parts[0]
            _, h = first.wrap(w, available)
            if h > available + .01 or h <= 0:
                break
            first.drawOn(c, x, y-h)
            y -= h
            available -= h
            remaining = parts[1:] + remaining[1:]
        return remaining

    def minimum_band(queue):
        if not queue:
            return 15.0
        minimum = BAND_LABEL_HEIGHT+BAND_PADDING+2*leading
        # A fishbone row must fit intact. Reserve its preceding short note too,
        # so a large Other Medications band cannot starve the lab row forever.
        before = 0.0
        for item in queue:
            h = item.wrap(total_width-6, 100000)[1]
            if isinstance(item, LabRow):
                return min(195, max(minimum, before+h+BAND_LABEL_HEIGHT+BAND_PADDING))
            before += h
            if before > 30:
                break
        return minimum

    page = 0
    while True:
        page += 1
        if page > 150:
            raise ValueError('The handoff is too long to export safely. Shorten it or export text.')
        c.setFont('Helvetica', 7)
        c.drawString(margin, height-margin-5, 'Print prepared: ' + print_stamp + ' | Room ' + sheet['room'] + (' | Continued' if page > 1 else ''))
        c.drawRightString(width-margin, height-margin-5,
                         'Sheet ' + str(position) + '/' + str(count) + ' | Reference ' + sheet['id'][:8] + ' | Page ' + str(page))
        if plan['review_banner'] is not None:
            banner = plan['review_banner']
            _, bh = banner.wrap(total_width, 10000)
            banner.drawOn(c, margin, height-margin-11-bh)
        plan.update(columns=queues, bands=bands, access=access)
        main_need, band_needs, access_need = _plan_heights(plan)
        all_fit = main_need+sum(band_needs)+access_need <= body_height+.01
        if all_fit:
            access_height = access_need
            band_heights = band_needs
            # Use remaining space for the system columns, rather than imposing
            # an arbitrary minimum that would push otherwise-fitting labs out.
            main_height = body_height-sum(band_heights)-access_height
        else:
            access_height = min(54, access_need)
            minimums = [minimum_band(q) for _, q in bands]
            main_cap = max(24, body_height-access_height-sum(minimums))
            main_height = min(main_need, main_cap, 250)
            remaining_height = body_height-main_height-access_height
            band_heights = []
            for index, wanted in enumerate(band_needs):
                later = sum(minimums[index+1:])
                allowed = max(minimums[index], remaining_height-later)
                actual = min(wanted, allowed)
                band_heights.append(actual)
                remaining_height -= actual

        y = column_top+12
        c.setLineWidth(.5)
        x = margin
        for (label, _), w in zip(COLUMNS, widths):
            c.setFont('Times-Bold', 8)
            c.drawCentredString(x+w/2, y-9, label)
            c.line(x, y-12, x+w, y-12)
            x += w
        y -= 12
        updated = []
        x = margin
        for w, q in zip(widths, queues):
            c.rect(x, y-main_height, w, main_height)
            updated.append(draw_queue(q, x+3, y-3, w-6, main_height-6))
            x += w
        queues = updated
        y -= main_height
        updated_bands = []
        for (label, queue), bh in zip(bands, band_heights):
            c.rect(margin, y-bh, total_width, bh)
            c.setFont('Times-Bold', 7.5)
            c.drawString(margin+3, y-8, label + (':' if page == 1 else ' (continued):'))
            rest = draw_queue(queue, margin+3, y-BAND_LABEL_HEIGHT-2,
                              total_width-6, bh-BAND_LABEL_HEIGHT-BAND_PADDING)
            updated_bands.append((label, rest))
            y -= bh
        bands = updated_bands
        aw = total_width/4
        updated_access = []
        for index, (label, queue) in enumerate(access):
            x = margin+index*aw
            c.rect(x, y-access_height, aw, access_height)
            c.setFont('Times-Bold', 7.5)
            c.drawString(x+3, y-8, label+':')
            rest = draw_queue(queue, x+3, y-11, aw-6, access_height-14)
            updated_access.append((label, rest))
        access = updated_access
        c.setFont('Helvetica', 6.1)
        c.drawString(margin, margin+6, 'Confirm the current patient in Epic. Blank sections are not confirmed normal. Downloaded copies are not encrypted.')
        c.drawRightString(width-margin, margin-2, 'Last Rate is a recorded source value, not a live pump feed.')
        c.showPage()
        if not any(queues) and not any(q for _, q in bands) and not any(q for _, q in access):
            break


def handoffs_html(sheets: list[dict], printed_at: datetime | None = None) -> str:
    if not sheets or len(sheets) > 100:
        raise ValueError("Select between 1 and 100 handoffs to print.")
    if len({s["room"] for s in sheets}) != len(sheets):
        raise ValueError("A room cannot be included twice in one print packet.")
    from datetime import timezone
    printed_at = printed_at or datetime.now(timezone.utc)
    docs = [handoff_html(sheet, printed_at) for sheet in sheets]
    head = docs[0].split("</head>", 1)[0]
    head += """<style>
main{margin-bottom:24px}.printbar{font:15px Arial,sans-serif;max-width:11in;margin:0 auto 18px}
.printbar button{padding:10px 16px;cursor:pointer}
@media print{.printbar{display:none}main{break-after:page;margin:0}main:last-child{break-after:auto}}
</style></head>"""
    pages = ["<main>" + doc.split("<main>", 1)[1].split("</main>", 1)[0] + "</main>" for doc in docs]
    return head + '<body><div class="printbar"><button onclick="window.print()">Print all handoffs</button> Landscape Letter. Each room starts on a new page.</div>' + "".join(pages) + PRINT_TIME_SCRIPT + "</body></html>"


def download_payload(sheets: list[dict], kind: str, expires_at: float | None = None):
    """Return a zero-argument generator for Streamlit >=1.52 downloads.

    A private snapshot is captured on render, not a shared cache. The timestamp
    is generated on the click, not when the UI was last opened. No Streamlit
    session data is accessed from the download worker thread.
    """
    if kind not in ("pdf", "html", "text"):
        raise ValueError("Unknown handoff download format.")
    if kind == "text" and len(sheets) != 1:
        raise ValueError("Text export expects one handoff.")
    snapshot = deepcopy(sheets)
    for sheet in snapshot:
        validate_sheet(sheet)

    def generate():
        if expires_at is not None and time.monotonic() >= expires_at:
            raise ValueError("The session expired. Sign in and prepare a new download.")
        try:
            if kind == "pdf":
                return handoffs_pdf(snapshot)
            if kind == "html":
                return handoffs_html(snapshot).encode("utf-8")
            return handoff_text(snapshot[0]).encode("utf-8")
        except Exception:
            raise ValueError("The print file could not be generated. Refresh the app and try again.") from None
    return generate
