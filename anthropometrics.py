"""Explicit demographic values. No DOB capture or age/sex inference from diagnoses.

Age is the age at the BMI measurement. A years-only display is not treated as an
exact age in months for a BMI percentile. BMI and BSA are imported, not derived
from weight, medication doses, or inferred height. CDC reference lookup is local.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
import re

FIELDS = ('age', 'sex', 'bmi', 'height', 'bsa')
MISSING = {'', 'none', 'n/a', 'na', '--', 'unknown', 'not recorded', 'not documented'}
NUMBER = r'(?:\d+(?:\.\d+)?|\.\d+)'
HEADER = re.compile(r'^(Age(?:\s+(?:in\s+months|at\s+(?:BMI\s+)?measurement))?|Sex(?:\s+for\s+growth\s+chart)?|BMI|Body\s+mass\s+index|Height|Length|BSA|Body\s+surface\s+area)\s*(?::|\bis\b)\s*(.*)$', re.I)


def empty_anthropometrics() -> dict:
    return {key: '' for key in FIELDS}


def age_months(text: str) -> float | None:
    """Accept documented total months or years AND months. Never guess months."""
    text = re.sub(r'\s+', ' ', text.strip().lower())
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:months?|mos?|m)', text)
    if match:
        return float(match.group(1))
    match = re.fullmatch(r'(\d+)\s*(?:years?|yrs?|y)\s*(?:,|and)?\s*(\d+)\s*(?:months?|mos?|m)', text)
    if match and int(match.group(2)) < 12:
        return 12 * int(match.group(1)) + int(match.group(2))
    return None


def age_bounds(text: str) -> tuple[float, float] | None:
    value = age_months(text)
    if value is not None:
        return value, value
    match = re.fullmatch(r'(\d+)\s*(?:years?|yrs?|y)', text.strip(), re.I)
    if match:
        return int(match.group(1)) * 12, (int(match.group(1)) + 1) * 12
    # These infant ages are sufficient to identify the under-two restriction,
    # but never used as a decimal-month input to the CDC table.
    match = re.fullmatch(r'(\d+)\s*(?:days?|d|weeks?|wks?|w)', text.strip(), re.I)
    if match:
        days = int(match.group(1)) * (7 if re.search(r'w', text, re.I) else 1)
        return days / 31, days / 28
    return None


def clean_field(key: str, value: str) -> str:
    value = re.sub(r'\s+', ' ', value.replace('\u00a0', ' ').strip())
    if value.casefold().rstrip('.') in MISSING:
        return ''
    if len(value) > 100:
        raise ValueError('A demographic field is too long.')
    if key == 'age':
        if not re.fullmatch(r'\d+(?:\.\d+)?\s*(?:years?|yrs?|y|months?|mos?|m|weeks?|wks?|w|days?|d)(?:\s*(?:,|and)?\s*\d+\s*(?:months?|mos?|m|days?|d))?', value, re.I):
            raise ValueError('Use an age with units, for example 5 years 2 months, 14 months, or 10 days.')
        if age_months(value) is not None and age_months(value) > 1440:
            raise ValueError('Check the recorded age.')
        return value
    if key == 'sex':
        names = {'m': 'Male', 'male': 'Male', 'boy': 'Male', 'f': 'Female', 'female': 'Female', 'girl': 'Female'}
        if value.casefold() not in names:
            raise ValueError('CDC growth-chart sex must be explicitly Male or Female, or left blank.')
        return names[value.casefold()]
    if key == 'bmi':
        match = re.fullmatch(rf'({NUMBER})(?:\s*kg\s*/\s*m(?:²|\^?2))?\.?', value, re.I)
        if not match or not 0 < Decimal(match.group(1)) <= 200:
            raise ValueError('Enter a positive recorded BMI, such as 17.14 kg/m².')
        return match.group(1) + ' kg/m²'
    if key == 'height':
        match = re.fullmatch(rf'({NUMBER})\s*(cm|m|in(?:ches)?)', value, re.I)
        if not match or Decimal(match.group(1)) <= 0:
            raise ValueError('Enter recorded height with a unit, for example 100 cm.')
        return match.group(1) + ' ' + match.group(2).lower()
    if key == 'bsa':
        match = re.fullmatch(rf'({NUMBER})\s*(?:m²|m\^?2|sq\.?\s*m)', value, re.I)
        if not match or not 0 < Decimal(match.group(1)) <= 10:
            raise ValueError('Check BSA and its unit. Use a recorded value such as 0.65 m², not m/kg².')
        return match.group(1) + ' m²'
    raise ValueError('Unknown demographic field.')


def validate_anthropometrics(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise ValueError('The demographic measurements have an invalid structure.')
    for key, value in data.items():
        if not isinstance(value, str) or any(c in value for c in '\n\r\t'):
            raise ValueError('A demographic measurement contains invalid text.')
        if clean_field(key, value) != value:
            raise ValueError('A demographic measurement is not normalized.')


@dataclass
class AnthropometricResult:
    values: dict = field(default_factory=dict)
    remainder: str = ''
    error: str = ''


def extract_anthropometrics(block: str) -> AnthropometricResult:
    """Remove ONLY explicitly labeled measurements from I/N before old parsing."""
    out = AnthropometricResult()
    remaining = []
    pending = None
    for raw in block.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        text = raw.strip()
        match = HEADER.match(text)
        if match:
            label, value = match.groups()
            name = label.casefold()
            key = ('age' if name.startswith('age') else 'sex' if name.startswith('sex') else
                   'bmi' if name in ('bmi', 'body mass index') else 'bsa' if name in ('bsa', 'body surface area') else 'height')
            if name == 'age in months' and re.fullmatch(NUMBER, value):
                value += ' months'
            pending = key if not value else None
        elif pending and text:
            if HEADER.match(text) or re.match(r'^(?:Dosing|Wt|Weight|Date of Admission|NUTRITION)\b', text, re.I):
                remaining.append(raw)
                pending = None
                continue
            key, value, pending = pending, text, None
        else:
            remaining.append(raw)
            continue
        try:
            value = clean_field(key, value)
        except ValueError as exc:
            out.error = str(exc)
            return out
        if key in out.values and out.values[key] and value and out.values[key] != value:
            out.error = 'Conflicting demographic measurements were supplied in one section.'
            return out
        if value or key not in out.values:
            out.values[key] = value
    out.remainder = '\n'.join(remaining)
    return out


def measurements_text(data: dict) -> str:
    from bmi_reference import bmi_percentile_summary
    validate_anthropometrics(data)
    rows = []
    for key, label in (('height', 'Height'), ('bsa', 'BSA'), ('bmi', 'BMI')):
        if data[key]:
            rows.append(label + ': ' + data[key])
    if data['bmi']:
        text, _ = bmi_percentile_summary(data)
        rows.append('BMI percentile: ' + text)
    return '\n'.join(rows)
