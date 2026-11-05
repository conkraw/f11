"""Dated CBC/BMP fishbones and labelled branches, shared by PDF and HTML.

All values are escaped for HTML and drawn as text in PDFs. Long/nonstandard
values use a full-text fallback rather than clipping or shortening results.
"""
from html import escape
from io import StringIO
from textwrap import wrap
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph
from reportlab.lib.styles import ParagraphStyle
from labs import result_cards, short_date

NOTE = ('Latest/preceding PER COMPONENT, not confirmed same-draw panels. Dates are shown beside each result. '
        'Same-date ties without collection times follow source order. -- = not supplied.')


def ascii_text(s: str) -> str:
    for a, b in {'₂':'2', '−':'-', '–':'-', '—':'-', '≤':'<=', '≥':'>=', 'μ':'u', 'µ':'u'}.items():
        s = s.replace(a, b)
    return s


def card_plan(card: dict, width: float) -> tuple[float, list]:
    """Return a small vector display list in bottom-origin coordinates."""
    scale = width / 180
    kind, rows = card['kind'], card['rows']
    plan = []
    def text(x,y,value,size=8,font='Times-Roman',align='left'):
        plan.append(('text', x*scale, y, ascii_text(value), size, font, align))
    def line(x1,y1,x2,y2):
        plan.append(('line', x1*scale,y1,x2*scale,y2))
    def node(key,x,y,maxw=48):
        row = rows.get(key)
        label = {'CREATININE':'Cr', 'GLUCOSE':'Glucose', 'NA':'Na', 'CL':'Cl', 'HGB':'Hgb', 'HCT':'Hct', 'PLT':'Plt'}.get(key,key)
        text(x,y+9,label,6.5,'Times-Bold','center')
        text(x,y,row['value'] if row else '--',8,'Times-Roman','center')
        if row:
            text(x,y-9,short_date(row['date']),6.3,'Times-Roman','center')
    # If a cell cannot fit faithfully, use labelled branches below instead.
    if kind in ('cbc','bmp'):
        main = ('WBC','HGB','HCT','PLT') if kind == 'cbc' else ('NA','K','CL','CO2','BUN','CREATININE','GLUCOSE')
        for key in main:
            if key in rows and (stringWidth(ascii_text(rows[key]['value']),'Times-Roman',8) > 40*scale
                              or stringWidth(short_date(rows[key]['date']),'Times-Roman',6.3)>42*scale):
                kind = 'branch'
                break
    if kind == 'cbc':
        extras = [rows[k] for k in ('MCV','NEUTROABS','LYMPHSABS') if k in rows]
        height = 126 + len(extras)*10
        offset = len(extras)*10
        node('WBC',25,64+offset); node('HGB',90,90+offset,65)
        node('HCT',90,38+offset,65); node('PLT',155,64+offset)
        line(53,82+offset,66,64+offset); line(66,64+offset,53,46+offset)
        line(127,82+offset,114,64+offset); line(114,64+offset,127,46+offset)
        line(66,64+offset,114,64+offset)
        for i, row in enumerate(extras):
            short = row['component']
            value = short + ': ' + row['value'] + ' [' + short_date(row['date']) + ']'
            text(6,8+10*(len(extras)-i-1),value,7)
    elif kind == 'bmp':
        extras = [rows['CALCIUM']] if 'CALCIUM' in rows else []
        height = 126 + len(extras)*10
        offset = len(extras)*10
        for key,x,y in (('NA',22,90),('K',22,43),('CL',65,90),('CO2',65,43),('BUN',108,90),('CREATININE',108,43),('GLUCOSE',158,66)):
            node(key,x,y+offset)
        line(3,66+offset,137,66+offset)
        for x in (44,87):
            line(x,28+offset,x,105+offset)
        line(130,102+offset,140,66+offset);line(140,66+offset,130,30+offset)
        if extras:
            row=extras[0];text(6,8,'Ca: '+row['value']+' ['+short_date(row['date'])+']',7)
    else:
        # Labelled branches for hepatic, coagulation, gases and other results.
        lines = []
        for row in rows.values():
            value = row['component'] + ': ' + row['value']
            chunks = wrap(ascii_text(value), max(18, int(width/4.2)), break_long_words=True, break_on_hyphens=False) or ['']
            lines.append((chunks, short_date(row['date'])))
        height = 28 + sum(9*len(chunks)+11 for chunks,_ in lines)
        y = height-30
        line(5, y+4, 5, 11)
        for chunks, date in lines:
            line(5,y+2,10,y+2)
            for chunk in chunks:
                text(13,y,chunk,7.7); y-=9
            text(13,y,date,6.5); y-=11
    title, _, subtitle = card['title'].partition(' | ')
    text(6,height-11,title,8.6,'Times-Bold')
    text(6,height-21,subtitle,6.5)
    return height, plan


class LabRow(Flowable):
    """Up to four dated cards in a single indivisible row."""
    def __init__(self, cards: list[dict], width: float):
        super().__init__()
        self.width=width
        self.cell_width=width/4
        self.cards=cards
        self.plans=[card_plan(card,self.cell_width-6) for card in cards]
        self.height=max((h for h,_ in self.plans),default=0)+6
    def wrap(self, availWidth, availHeight):
        return self.width,self.height
    def split(self, availWidth, availHeight):
        return []
    def draw(self):
        c=self.canv
        c.saveState(); c.setLineWidth(.45)
        for i,(height,plan) in enumerate(self.plans):
            x0=i*self.cell_width+3
            y0=self.height-height-3
            c.setStrokeGray(.55); c.rect(x0-1,3,self.cell_width-5,self.height-6)
            c.setStrokeGray(0)
            for item in plan:
                if item[0]=='line':
                    _,x1,y1,x2,y2=item;c.line(x0+x1,y0+y1,x0+x2,y0+y2)
                else:
                    _,x,y,value,size,font,align=item
                    c.setFont(font,size)
                    if align=='center':c.drawCentredString(x0+x,y0+y,value)
                    else:c.drawString(x0+x,y0+y,value)
        c.restoreState()


def laboratory_flowables(data: dict, width: float) -> list:
    style=ParagraphStyle('labnote',fontName='Times-Roman',fontSize=7.3,leading=8.5,splitLongWords=True)
    cards=result_cards(data)
    out=[Paragraph(escape(NOTE),style)] if cards else []
    for i in range(0,len(cards),4):
        row=LabRow(cards[i:i+4],width)
        if row.height <= 205:
            out.append(row)
        else:
            # Arbitrarily long user edits must still paginate without truncation.
            for card in cards[i:i+4]:
                out.append(Paragraph(escape(card['title']),style))
                for value in card['rows'].values():
                    out.append(Paragraph(escape(value['component']+': '+value['value']+' ['+value['date']+']'),style))
    for text in data['notes']:
        out.append(Paragraph(escape('Source: '+text),style))
    return out


def laboratory_html(data: dict) -> str:
    cards=result_cards(data)
    pieces=['<div class="labnote">'+escape(NOTE)+'</div>'] if cards else []
    pieces.append('<div class="labcards">')
    for card in cards:
        height,plan=card_plan(card,180)
        # SVG is a visual layout only. All text is escaped, with no external assets.
        body=[]
        for item in plan:
            if item[0]=='line':
                _,x1,y1,x2,y2=item
                body.append(f'<line x1="{x1}" y1="{height-y1}" x2="{x2}" y2="{height-y2}" stroke="black" stroke-width="0.5"/>')
            else:
                _,x,y,value,size,font,align=item
                weight='bold' if font=='Times-Bold' else 'normal'
                anchor='middle' if align=='center' else 'start'
                body.append(f'<text x="{x}" y="{height-y}" font-family="Times New Roman,serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')
        pieces.append(f'<svg class="labcard" role="img" aria-label="{escape(card["title"], quote=True)}" viewBox="0 0 180 {height}" xmlns="http://www.w3.org/2000/svg">'+''.join(body)+'</svg>')
    pieces.append('</div>')
    for text in data['notes']:
        pieces.append('<div class="labnote">Source: '+escape(text)+'</div>')
    return ''.join(pieces)
