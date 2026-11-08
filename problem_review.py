"""Deterministic review prompts, NOT a diagnosis or a billing-code generator.

Source diagnoses are never edited. Each suggestion retains its supporting
observation and a limitation. Clinical confirmation/dismissal is per sheet and
per evidence fingerprint, so a previous decision cannot approve changed data.
No medication doses or treatment recommendations are produced.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import escape
import json
import re

from labs import canonical, date_parts, ordered_components
from cbc import cbc_cards
from medications import visible
from fen_gi import effective_section, group_for as gi_group
from lab_windows import clock, eligible_time

TITLE = 'Suggested Problems / Review Required'
STATUSES = ('review', 'confirmed', 'dismissed')
RULES = {
    'sepsis': 'Sepsis',
    'respiratory': 'Acute hypoxemic respiratory failure',
    'aki': 'Acute kidney injury',
    'NA': 'Hyponatremia', 'K': 'Hypokalemia', 'ALBUMIN': 'Hypoalbuminemia',
    'CO2': 'Metabolic acidosis', 'MG': 'Hypomagnesemia', 'PHOS': 'Hypophosphatemia',
    'HGB': 'Anemia', 'PLT': 'Thrombocytopenia', 'constipation': 'Constipation',
}
LOW_RULES = tuple(k for k in RULES if k in ('NA','K','ALBUMIN','CO2','MG','PHOS','HGB','PLT'))
LABELS = {'NA':'Sodium', 'K':'Potassium', 'ALBUMIN':'Albumin', 'CO2':'Serum CO2',
          'MG':'Magnesium', 'PHOS':'Phosphorus', 'HGB':'Hemoglobin', 'PLT':'Platelets'}
LOW = re.compile(r'\((?:L|LL|LOW)\)', re.I)
NUMBER = re.compile(r'^\s*([<>≤≥]?)\s*([+-]?(?:\d[\d,]*(?:\.\d*)?|\.\d+))(.*)$')


def empty_review() -> dict:
    return {'enabled': True, 'decisions': {}, 'low_limits': {}}


def validate_review(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != {'enabled','decisions','low_limits'} or type(data['enabled']) is not bool:
        raise ValueError('The suggested-problem review settings are invalid.')
    if not isinstance(data['decisions'], dict) or set(data['decisions']) - set(RULES):
        raise ValueError('The problem review decisions are invalid.')
    for key, row in data['decisions'].items():
        if (not isinstance(row, dict) or set(row) != {'fingerprint','status','text'}
                or row['status'] not in STATUSES or not isinstance(row['fingerprint'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', row['fingerprint'])
                or not isinstance(row['text'], str) or not row['text'].strip()
                or len(row['text']) > 200 or any(c in row['text'] for c in '\r\n\t')):
            raise ValueError('A problem review decision is invalid.')
    if not isinstance(data['low_limits'], dict) or set(data['low_limits']) - set(LOW_RULES):
        raise ValueError('The low-result limits are invalid.')
    for key, value in data['low_limits'].items():
        if not isinstance(value, dict) or set(value) != {'value','unit'}:
            raise ValueError('A low-result limit is invalid.')
        number = numeric(value['value'])
        if (number is None or not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)', value['value']) or number[0] or number[1] <= 0 or number[1] > 100000
                or not isinstance(value['unit'], str) or not value['unit'].strip()
                or len(value['unit']) > 50 or any(c in value['unit'] for c in '\n\r\t')):
            raise ValueError('Use a positive low-result limit and its source units.')


def numeric(value: str):
    if not isinstance(value, str):
        return None
    match = NUMBER.fullmatch(value.strip())
    if not match or '|' in value:
        return None
    tail = re.sub(r'\((?:H|L|HH|LL|A|LOW|HIGH|C)\)|\*', '', match[3], flags=re.I).strip()
    if tail and not re.fullmatch(r'[a-zA-Zµμ%\d/^ .-]+', tail):
        return None
    try:
        number = Decimal(match[2].replace(',', ''))
    except InvalidOperation:
        return None
    return (match[1], number, tail)


def unit_key(value):
    return re.sub(r'\s+', '', value).replace('µ','u').replace('μ','u').casefold()


def _is_low(row: dict, limit: dict | None) -> tuple[bool, str]:
    parsed = numeric(row['value'])
    if parsed is None:
        return False, ''
    if LOW.search(row['value']):
        return True, 'source marked low'
    if not limit:
        return False, ''
    # A clinician supplies a cutoff for this patient, in documented source units.
    source_unit = row.get('unit') or parsed[2]
    if not source_unit or unit_key(source_unit) != unit_key(limit['unit']):
        return False, ''
    cutoff = Decimal(limit['value'])
    comparator, number, _ = parsed
    low = (number < cutoff if not comparator or comparator == '≤' else
           number <= cutoff if comparator == '<' else False)
    return low, 'below your limit ' + limit['value'] + ' ' + limit['unit'] if low else ''


def _medication_active(row: dict, now: datetime) -> bool:
    if not visible(row):
        return False
    name = row['name']
    if re.search(r'\[(?:held by provider|discontinued|removed)\]|ADS Override Pull', name, re.I):
        return False
    start = re.search(r'\[START ON ([^]]+)\]', name, re.I)
    if start:
        try:
            when, timed = date_parts(start[1])
            if (when.date() > now.date() or (timed and when > now.replace(tzinfo=None))):
                return False
        except ValueError:
            return False
    return True


def _latest_rows(sheet: dict, now: datetime) -> dict:
    data = {'rows': [], 'notes': []}
    if 'g' not in sheet.get('import_warnings', {}):
        admission = sheet.get('admission_date', '')
        data['rows'] = [r for r in sheet['labs']['rows'] if r['include'] and
                        eligible_time(r, now, admission=admission)]
    groups = ordered_components(data)
    latest = {k: v[0] for k,v in groups.items() if v}
    # Reuse existing standard-Hgb-over-ISTAT selection unchanged.
    if 'q' not in sheet.get('import_warnings', {}):
        cards = cbc_cards(data, sheet.get('cbc'))
        if cards:
            for key in ('HGB','PLT'):
                row = cards[0]['rows'].get(key)
                if row and row.get('date') and eligible_time(row, now, admission=sheet.get('admission_date', '')):
                    latest[key] = row
                else:
                    latest.pop(key, None)
    else:
        latest.pop('HGB', None)
        latest.pop('PLT', None)
    return latest


def suggestions(sheet: dict, as_of: datetime | None = None) -> list[dict]:
    now = clock(as_of)
    config = sheet.get('problem_review', empty_review())
    validate_review(config)
    out = []
    def add(key, evidence, caution, detail=None):
        label = RULES[key]
        fingerprint = sha256(json.dumps([key, evidence, caution, detail, sheet.get('admission_date', '')], ensure_ascii=False).encode()).hexdigest()
        decision = config['decisions'].get(key, {})
        applies = decision.get('fingerprint') == fingerprint
        out.append({'key':key, 'label': decision['text'] if applies else label,
                    'evidence':evidence, 'caution':caution, 'fingerprint':fingerprint,
                    'status':decision['status'] if applies else 'review'})
    meds = [r for r in sheet.get('medications', []) if _medication_active(r, now)]
    if 'b' not in sheet.get('import_warnings', {}):
        id_meds = [r for r in meds if effective_section(r) == 'Infectious Disease']
        if id_meds:
            names = list(dict.fromkeys(r['name'] for r in id_meds))
            add('sepsis', 'ID-mapped medication: ' + ', '.join(names),
                'Medication mapping alone does not establish infection or sepsis. Verify indication and organ dysfunction.', id_meds)
        bowel = [r for r in meds if gi_group(r) == 'bowel']
        if bowel:
            add('constipation', 'Bowel regimen: ' + ', '.join(dict.fromkeys(r['name'] for r in bowel)),
                'A bowel regimen may be preventive. Verify symptoms and the medication indication.', bowel)
    if 'cd' not in sheet.get('import_warnings', {}):
        support = []
        vent = sheet.get('ventilation')
        if vent:
            support.append('Ventilation: ' + str(vent.get('mode', 'documented settings')))
        for device in sheet.get('noninvasive', []):
            name = device.get('device', '')
            if name in ('HFNC','BiPAP','CPAP','Nasal cannula','Non-rebreather','Face mask'):
                suffix = ' (inferred device, verify)' if device.get('flow_inferred') or device.get('pressure_inferred') else ''
                support.append(name + suffix)
        if support:
            add('respiratory', ', '.join(dict.fromkeys(support)),
                'Support alone does not establish acute hypoxemia. Verify acuity, oxygenation and whether support is baseline or for airway protection.', [vent, sheet.get('noninvasive')])
    latest = _latest_rows(sheet, now)
    for key in LOW_RULES:
        row = latest.get(key)
        if not row:
            continue
        low, why = _is_low(row, config['low_limits'].get(key))
        if low:
            units = (' ' + row['unit']) if row.get('unit') else ''
            evidence = LABELS[key] + ' ' + row['value'] + units + ' [' + row['date'] + '], ' + why
            caution = ('Low serum CO2 does not alone determine the acid-base disorder. Review pH, PCO2 and the clinical context.'
                       if key == 'CO2' else 'Verify the applicable reference range and clinical context.')
            add(key, evidence, caution)
    if 'g' not in sheet.get('import_warnings', {}):
        rows = [r for r in sheet['labs']['rows'] if r['include'] and canonical(r['component']) == 'CREATININE'
                and eligible_time(r, now, admission=sheet.get('admission_date', ''))]
        rows = ordered_components({'rows': rows, 'notes': []}).get('CREATININE', [])
        if len(rows) >= 2:
            new, old = rows[:2]
            n, o = numeric(new['value']), numeric(old['value'])
            nd, nt = date_parts(new['date'])
            od, ot = date_parts(old['date'])
            ordered_dates = nd > od and (nd.date() != od.date() or (nt and ot))
            # Exact ties/date-only same-day rows do not establish a trend direction.
            if (n and o and not n[0] and not o[0] and o[1] > 0 and ordered_dates
                    and unit_key(n[2]) == unit_key(o[2])
                    and 0 < (nd-od).total_seconds() <= 7*86400
                    and n[1] > o[1]*Decimal('1.5')):
                change = (n[1]/o[1]-1)*100
                evidence = 'Creatinine ' + old['value'] + ' [' + old['date'] + '] to ' + new['value'] + ' [' + new['date'] + '] (' + str(round(change,1)) + '% rise)'
                add('aki', evidence,
                    'User-defined >50% rise screen, not a complete AKI assessment. Verify baseline, collection timing, urine output and clinical context.')
    return out


def set_decision(sheet: dict, key: str, fingerprint: str, status: str, text: str) -> dict:
    result = deepcopy(sheet)
    review = deepcopy(result.get('problem_review', empty_review()))
    review['decisions'][key] = {'fingerprint':fingerprint, 'status':status, 'text':text.strip()}
    validate_review(review)
    result['problem_review'] = review
    return result


def review_text(sheet: dict, as_of: datetime | None = None, rich: bool = False, esc=escape) -> str:
    if not sheet.get('problem_review', empty_review())['enabled']:
        return ''
    rows = [r for r in suggestions(sheet, as_of) if r['status'] != 'dismissed']
    if not rows:
        return ''
    lines = ['Review prompts only. Not added to the source diagnoses.']
    for row in rows:
        heading = ('Reviewed by user: ' if row['status'] == 'confirmed' else 'Review for: ') + row['label']
        evidence = row['evidence']
        # Compact medicine trigger, without truncating the accessible evidence in UI.
        if row['key'] in ('sepsis','constipation'):
            evidence = ('ID-mapped medication present, verify indication and organ dysfunction'
                        if row['key'] == 'sepsis' else 'Bowel regimen present, verify indication')
        if row['key'] == 'respiratory':
            evidence += ', acuity/hypoxemia not established by device alone'
        if row['key'] == 'CO2':
            evidence += ', acid-base disorder requires review'
        if rich:
            lines.append('<b>' + esc(heading) + '</b>: ' + esc(evidence))
        else:
            lines.append(heading + ': ' + evidence)
    return '\n'.join(lines)


def limitation_notes(sheet: dict, as_of: datetime | None = None) -> list[str]:
    latest = _latest_rows(sheet, clock(as_of))
    config = sheet.get('problem_review', empty_review())
    notes = []
    for key in LOW_RULES:
        row = latest.get(key)
        if row and '*' in row['value'] and not LOW.search(row['value']) and key not in config['low_limits']:
            notes.append(LABELS[key] + ': an asterisk does not specify low versus high. Supply a patient-appropriate low limit in documented units or review manually.')
    if not sheet.get('admission_date'):
        notes.append('Admission date is missing. Problem prompts use the latest supplied results with their dates, not a verified admission interval.')
    return notes
