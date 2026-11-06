"""Route recorded vital-sign lines without recalculating ranges or values."""
from dataclasses import dataclass, field
import re


def route(label: str) -> str:
    key = re.sub(r'\s+', ' ', label.strip().casefold().replace('₂', '2'))
    if re.match(r'^(?:icp|cpp|intracranial pressure|cerebral perfusion pressure|wat(?:[- ]?1)?|target arousal level|sbs|rass)\b', key):
        return 'Neurologic'
    if re.match(r'^(?:temp(?:erature)?|tmax|t min|t max)\b', key):
        return 'Infectious Disease'
    if re.match(r'^(?:resp(?:iratory)?(?: rate)?|respirations|rr|spo2|sao2|oxygen saturation|o2 sat(?:uration)?|fio2)\b', key):
        return 'Respiratory'
    if re.match(r'^(?:heart rate|hr|pulse(?: rate)?|bp|blood pressure|systolic|diastolic|sbp|dbp|map|mean arterial pressure|abp|art(?:erial)?(?: line)?(?: bp| blood pressure| pressure)?|cvp|central venous pressure|pap|pulmonary artery pressure)\b', key):
        return 'Cardiovascular'
    return 'Other'


def validate_vitals(rows: list[dict]) -> None:
    if not isinstance(rows, list) or len(rows) > 200:
        raise ValueError('The vital-sign list is invalid or too large.')
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'label', 'value', 'section', 'include'}:
            raise ValueError('A vital-sign row has an invalid structure.')
        if row['section'] not in ('Neurologic', 'Respiratory', 'Cardiovascular', 'Infectious Disease', 'Other') or not isinstance(row['include'], bool):
            raise ValueError('A vital-sign destination or inclusion setting is invalid.')
        for key in ('label', 'value'):
            if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 1500 or '\n' in row[key] or '\r' in row[key]:
                raise ValueError('A vital-sign field is empty or invalid.')


@dataclass
class VitalsResult:
    rows: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    error: str = ''


def parse_vitals(block: str) -> VitalsResult:
    out = VitalsResult()
    for number, raw in enumerate(block.splitlines(), 1):
        text = raw.strip()
        if not text or text.rstrip(':').casefold() in ('vitals', 'vital signs', 'none', 'not documented'):
            continue
        if ':' not in text:
            out.error = f'Vital-sign line {number} needs a label followed by a colon. Nothing was imported.'
            return out
        label, value = (x.strip() for x in text.split(':', 1))
        if not value:
            out.issues.append('A blank vital-sign field was left out.')
            continue
        section = route(label)
        out.rows.append({'label': label, 'value': value, 'section': section, 'include': True})
        if section == 'Other':
            out.issues.append('An unrecognized vital-sign label was retained in Other for review.')
    try:
        validate_vitals(out.rows)
    except ValueError as exc:
        out.error = str(exc)
    return out


def text_by_system(rows: list[dict]) -> dict[str, str]:
    result = {}
    for row in rows:
        if row['include']:
            section = row['section']
            result[section] = (result.get(section, '') + '\n' + row['label'] + ': ' + row['value']).strip()
    return result
