"""Route recorded vital signs and display explicit SpO2 Min/Max as a range.

No mean, endpoint or clinical value is calculated. Ordinary vital lines remain
verbatim. The special SpO2 summary rule reads only the provided Min and Max.
"""
from dataclasses import dataclass, field
from decimal import Decimal
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



_SPO2_SUMMARY = re.compile(
    r'^spo[2₂](?P<units>\s*\(\s*%\s*\))?\s*:?\s*'
    r'(?=(?:avg|average|min|minimum|max|maximum)\s*:)', re.IGNORECASE,
)
_SUMMARY_STAT = re.compile(r'\b(avg|average|min|minimum|max|maximum)\s*:', re.IGNORECASE)
_PERCENT_VALUE = re.compile(r'(?P<number>[+-]?\d+(?:\.\d+)?)\s*(?P<unit>%?)')


def spo2_summary_range(text: str) -> str | None:
    """Return explicit Min/Max only, or None for an ordinary vital-sign line.

    Handle an optional colon after SpO2, tabs, nonbreaking spaces, subscript 2,
    decimals and reordered statistics. An incomplete/conflicting summary raises
    an actionable error instead of inventing endpoints or substituting Avg.
    """
    text = text.strip()
    prefix = _SPO2_SUMMARY.match(text)
    if prefix is None:
        return None
    stats_text = text[prefix.end():]
    markers = list(_SUMMARY_STAT.finditer(stats_text))
    limits: dict[str, str] = {}
    for index, marker in enumerate(markers):
        stat = marker.group(1).casefold()
        if stat in ('avg', 'average'):
            continue
        stat = 'min' if stat.startswith('min') else 'max'
        end = markers[index + 1].start() if index + 1 < len(markers) else len(stats_text)
        source = stats_text[marker.end():end].strip()
        value = _PERCENT_VALUE.fullmatch(source)
        if value is None or (not value.group('unit') and not prefix.group('units')):
            raise ValueError('SpO2 Min and Max need numeric percentage values. Nothing was imported.')
        number = value.group('number')
        if not Decimal('0') <= Decimal(number) <= Decimal('100'):
            raise ValueError('SpO2 Min and Max must be between 0% and 100%. Check the source. Nothing was imported.')
        if stat in limits and Decimal(limits[stat]) != Decimal(number):
            raise ValueError('The SpO2 summary has conflicting repeated Min or Max values. Nothing was imported.')
        limits.setdefault(stat, number)
    if set(limits) != {'min', 'max'}:
        raise ValueError('The SpO2 summary needs both Min and Max. The average cannot supply a missing limit. Nothing was imported.')
    if Decimal(limits['min']) > Decimal(limits['max']):
        raise ValueError('SpO2 Min is greater than Max. Check the source. Nothing was imported.')
    return limits['min'] + '% to ' + limits['max'] + '%'


def parse_vitals(block: str) -> VitalsResult:
    out = VitalsResult()
    for number, raw in enumerate(block.splitlines(), 1):
        text = raw.strip()
        if not text or text.rstrip(':').casefold() in ('vitals', 'vital signs', 'none', 'not documented'):
            continue
        try:
            saturation_range = spo2_summary_range(text)
        except ValueError as exc:
            out.error = f'Vital-sign line {number}: {exc}'
            return out
        if saturation_range is not None:
            out.rows.append({'label': 'SpO2', 'value': saturation_range,
                             'section': 'Respiratory', 'include': True})
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
