"""Presentation-only infusion grouping. No clinical dose inference or conversion.

Explicit continuous parenteral orders are recognized automatically. A saved
user choice is keyed to the complete formulation, route and frequency, so a
PRN order for the same drug is not accidentally changed. No doses are supplied
by a rule. Source amounts, qualifiers, held/start labels and recorded rates stay.
"""
from __future__ import annotations
from copy import deepcopy
from html import escape
import re
from medications import normalized, match_name, visible, format_medication

MODES = ("auto", "infusion", "other")
MODE_LABELS = {"auto": "Automatic", "infusion": "Infusion", "other": "Other medication"}


def infusion_key(row: dict) -> tuple[str, str, str]:
    return (match_name(row["name"]), normalized(row["route"]), normalized(row["frequency"]))


def is_infusion(row: dict) -> bool:
    mode = row.get("infusion_mode", "auto")
    if mode != "auto":
        return mode == "infusion"
    frequency = normalized(row.get("frequency", ""))
    route = normalized(row.get("route", "")).replace("-", " ")
    # A PRN syringe may say 'infusion' in its product name. That is not sufficient.
    if re.search(r"\bprn\b|as needed", frequency):
        return False
    return bool(re.search(r"\bcontinuous\b", frequency) and route in {
        "intravenous", "iv", "intra arterial", "intraarterial", "ia",
        "subcutaneous", "subcut", "sq", "epidural", "intrathecal",
    })


def validate_infusion_rules(rules: list[dict]) -> None:
    if not isinstance(rules, list) or len(rules) > 1500:
        raise ValueError("The infusion display rules are invalid or too large.")
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"name", "route", "frequency", "mode"}:
            raise ValueError("An infusion display rule has an invalid structure.")
        for key in ("name", "route", "frequency"):
            value = rule[key]
            if not isinstance(value, str) or len(value) > 4000 or any(c in value for c in "\n\r\t"):
                raise ValueError("An infusion display rule contains invalid text.")
        if not rule['name'] or rule['mode'] not in ("infusion", "other"):
            raise ValueError("An infusion display rule has an invalid choice.")
        key = (rule['name'], rule['route'], rule['frequency'])
        if key in seen:
            raise ValueError("Duplicate infusion display rules were found.")
        seen.add(key)


def set_infusion_rule(rules: list[dict], row: dict, mode: str) -> list[dict]:
    if mode not in MODES:
        raise ValueError("Choose Automatic, Infusion or Other medication.")
    key = infusion_key(row)
    result = [deepcopy(r) for r in rules if (r['name'], r['route'], r['frequency']) != key]
    if mode != 'auto':
        result.append(dict(zip(('name', 'route', 'frequency'), key), mode=mode))
    result.sort(key=lambda r: (r['name'], r['route'], r['frequency']))
    validate_infusion_rules(result)
    return result


def infusion_mode_for(row: dict, rules: list[dict]) -> str:
    key = infusion_key(row)
    for rule in rules:
        if (rule['name'], rule['route'], rule['frequency']) == key:
            return rule['mode']
    return 'auto'


def apply_infusion_rules(rows: list[dict], rules: list[dict]) -> list[dict]:
    validate_infusion_rules(rules)
    result = deepcopy(rows)
    for row in result:
        mode = infusion_mode_for(row, rules)
        if mode != 'auto' or 'infusion_mode' in row:
            row['infusion_mode'] = mode
    return result


def infusion_entry(row: dict, rich: bool = False, esc=escape) -> str:
    """Keep the entire formulation. Emphasize the explicit ordered dose, not strength."""
    encode = esc if rich else lambda v: v
    bold = lambda v: '<b>' + encode(v) + '</b>' if rich else v
    custom = row.get('custom_text', '').strip()
    if custom:
        # A user override remains authoritative. Do not add a contradictory dose.
        return bold(custom)
    lines = [bold(row['name'].strip())]
    dose = row['dose'].strip()
    rate = row['last_rate'].strip()
    if dose:
        lines.append('<b><u>' + encode('Dose: ' + dose) + '</u></b>' if rich else 'Dose: ' + dose)
    if rate:
        text = 'Recorded rate: ' + rate
        # Explicit infusion choice also enables rate display with a blank frequency.
        if not dose:
            lines.append('<b><u>' + encode(text) + '</u></b>' if rich else text)
        elif normalized(dose) != normalized(rate):
            lines.append(encode(text))
    details = ' | '.join(v.strip() for v in (row['route'], row['frequency']) if v.strip())
    if details:
        lines.append(encode(details))
    return '\n'.join(lines)


def neuro_body(notes: str, rows: list[dict], rich: bool = False, esc=escape) -> str:
    """Infusions first, then separate notes and remaining neuro medications."""
    meds = [r for r in rows if visible(r) and r['section'] == 'Neurologic']
    drips = [r for r in meds if is_infusion(r)]
    other = [r for r in meds if not is_infusion(r)]
    encode = esc if rich else lambda v: v
    if not drips:
        return '\n'.join([encode(notes.rstrip())] * bool(notes.strip()) +
                         [encode(format_medication(r)) for r in other])
    parts = ['<b>INFUSIONS</b>' if rich else 'INFUSIONS']
    for index, row in enumerate(drips):
        if index:
            parts.append("")
        parts.append(infusion_entry(row, rich, esc))
    if notes.strip():
        parts.extend(['-----', encode(notes.rstrip())])
    if other:
        parts.extend(['-----', '<b>OTHER MEDICATIONS</b>' if rich else 'OTHER MEDICATIONS'])
        parts.extend(encode(format_medication(r)) for r in other)
    return '\n'.join(parts)
