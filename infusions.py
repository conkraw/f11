"""Presentation-only infusion grouping. No clinical dose inference or conversion.

Explicit continuous parenteral orders are recognized automatically. Respiratory
continuous nebulized/inhaled orders also use the emphasized display. A saved
user choice is keyed to the complete formulation, route and frequency, so a
PRN order for the same drug is not accidentally changed. No doses are supplied
by a rule. Source amounts, qualifiers, held/start labels and recorded rates stay.
"""
from __future__ import annotations
from copy import deepcopy
from html import escape
import re
from medications import normalized, match_name, visible, format_medication
from output_text import medication_output
from infusion_rates import administration_display, show_recorded_pump_rate
from fen_gi import effective_section, group_for as gi_group
from medication_groups import (group_for as special_group, GROUP_NAMES, CV_GROUPS,
                               RESP_GROUPS, NEURO_OTHER_GROUPS, NEURO_PRIORITY_GROUPS)

MODES = ("auto", "infusion", "other")
MODE_LABELS = {"auto": "Automatic", "infusion": "Infusion", "other": "Other medication"}
INFUSION_HEADINGS = {
    "Neurologic": "Infusions", "Cardiovascular": "CV Infusions",
    "Respiratory": "Respiratory Infusions", "Hematology": "Heme Infusions",
}
INFUSION_SECTIONS = tuple(INFUSION_HEADINGS)
DISPLAY_LABELS = {"Neurologic": "Neuro", "Cardiovascular": "CV",
                  "Respiratory": "Respiratory", "Hematology": "Heme", "FEN / GI": "Endocrine"}


def supports_infusion_display(row: dict) -> bool:
    """Keep existing special groups, allowing DVT infusions to be emphasized.

    This does not change the stored system mapping or any clinical source field.
    PRN/fever and GI groups retain their existing priority over infusion display.
    """
    section = effective_section(row)
    group = special_group(row)
    if section == "FEN / GI":
        return gi_group(row) == "endocrine"
    return section in INFUSION_HEADINGS and (not group or group == "dvt"
                                            or group in CV_GROUPS + RESP_GROUPS + ("paralytic_infusion",))


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
    parenteral = route in {
        "intravenous", "iv", "intra arterial", "intraarterial", "ia",
        "subcutaneous", "subcut", "sq", "epidural", "intrathecal",
    }
    respiratory_delivery = effective_section(row) == "Respiratory" and route in {
        "nebulization", "nebulisation", "nebulized", "nebulised",
        "inhalation", "inhaled", "nebulized inhalation", "nebulised inhalation",
    }
    return bool(re.search(r"\bcontinuous\b|\btitrat(?:e|able)\b", frequency) and (parenteral or respiratory_delivery))


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


def infusion_entry(row: dict, rich: bool = False, esc=escape, handoff_only: bool = False) -> str:
    """Emphasize documented Last Admin rate when available, without altering Dose."""
    if handoff_only:
        row = deepcopy(row)
        for field in ("name", "dose", "route", "frequency", "last_rate", "custom_text", "last_admin_rate"):
            row[field] = medication_output(row.get(field, ""))
    encode = esc if rich else lambda v: v
    bold = lambda v: '<b>' + encode(v) + '</b>' if rich else v
    custom = row.get('custom_text', '').strip()
    if custom:
        # A user override remains authoritative. Do not add a contradictory dose.
        return bold(custom)
    lines = [bold(row['name'].strip())]
    dose = row['dose'].strip()
    rate = row['last_rate'].strip()
    admin = administration_display(row)
    if admin:
        label, value, stamp = admin
        text = label + ': ' + value
        primary = '<b><u>' + encode(text) + '</u></b>' if rich else text
        if stamp:
            primary += ' [' + encode(stamp) + ']'
        lines.append(primary)
    elif dose:
        lines.append('<b><u>' + encode('Dose: ' + dose) + '</u></b>' if rich else 'Dose: ' + dose)
    if rate and show_recorded_pump_rate(row):
        text = 'Recorded rate: ' + rate
        # Explicit infusion choice also enables rate display with a blank frequency.
        if not dose and not admin:
            lines.append('<b><u>' + encode(text) + '</u></b>' if rich else text)
        elif normalized(admin[1] if admin else dose) != normalized(rate):
            lines.append(encode(text))
    details = ' | '.join(v.strip() for v in (row['route'], row['frequency']) if v.strip())
    if details:
        lines.append(encode(details))
    return '\n'.join(lines)


def system_body_blocks(section: str, notes: str, rows: list[dict]) -> list[tuple[str, object]]:
    """One shared block model for plain text, HTML and PDF. No duplicate orders."""
    meds = [r for r in rows if visible(r) and effective_section(r) == section]
    if section == "Neurologic":
        # Stable leading-name sort keeps the same medicine's taper steps in
        # source order, even when Epic embeds different doses in the product name.
        # Do not rewrite source fields or reorder the stored medication list.
        meds = sorted(meds, key=lambda r: match_name(r.get("name", "")).split(" ", 1)[0])
    groups = []
    assigned = set()
    if section == "Hematology":
        # The requested category takes priority over the route of delivery.
        # Keep all DVT orders together, using infusion emphasis within the group
        # rather than moving its continuous orders into a separate group.
        dvt = [r for r in meds if special_group(r) == "dvt"]
        if dvt:
            groups.append([("heading", GROUP_NAMES["dvt"])] + [
                ("infusion" if supports_infusion_display(r) and is_infusion(r)
                 else "medication", r) for r in dvt
            ])
            assigned.update(r["id"] for r in dvt)
    # Category headings take priority over the generic CV infusion bucket.
    # An infusion remains emphasized inside its category and appears only once.
    if section == "Cardiovascular":
        for mode in CV_GROUPS:
            group = [r for r in meds if r["id"] not in assigned and special_group(r) == mode]
            if group:
                groups.append([("heading", GROUP_NAMES[mode])] + [
                    ("infusion" if is_infusion(r) else "medication", r) for r in group])
                assigned.update(r["id"] for r in group)
    if section in INFUSION_SECTIONS:
        drips = [r for r in meds if r["id"] not in assigned
                 and supports_infusion_display(r) and is_infusion(r) and not special_group(r)]
        if drips:
            groups.append([("heading", INFUSION_HEADINGS[section])] +
                          [("infusion", r) for r in drips])
            assigned.update(r["id"] for r in drips)
    modes = ((NEURO_PRIORITY_GROUPS + tuple(sorted(NEURO_OTHER_GROUPS,
                      key=lambda key: GROUP_NAMES[key].casefold()))) if section == "Neurologic"
             else RESP_GROUPS if section == "Respiratory" else ())
    for mode in modes:
        group = [r for r in meds if r["id"] not in assigned and special_group(r) == mode]
        if group:
            groups.append([("heading", GROUP_NAMES[mode])] + [("infusion" if (mode in ("antiepileptic", "paralytic_infusion") + RESP_GROUPS) and is_infusion(r) else "medication", r) for r in group])
            assigned.update(r["id"] for r in group)
    other = [r for r in meds if r["id"] not in assigned]
    if not groups:
        return ([("notes", notes.rstrip())] if notes.strip() else []) + [("medication", r) for r in other]
    if notes.strip():
        groups.append([("notes", notes.rstrip())])
    if other:
        groups.append([("heading", "Other Medications")] + [("medication", r) for r in other])
    blocks = []
    for group in groups:
        if blocks:
            blocks.append(("separator", "-----"))
        blocks.extend(group)
    return blocks


def render_body_blocks(blocks: list[tuple[str, object]], rich: bool = False, esc=escape) -> str:
    encode = esc if rich else lambda v: v
    lines = []
    for kind, item in blocks:
        if kind == "infusion":
            lines.append(infusion_entry(item, rich, esc, handoff_only=True))
        elif kind == "heading":
            lines.append("<b>" + encode(item) + "</b>" if rich else item)
        elif kind == "subheading":
            lines.append("<b><i>" + encode(item) + "</i></b>" if rich else item)
        elif kind == "medication":
            lines.append(encode(medication_output(format_medication(item))))
        else:
            lines.append(encode(item))
    return "\n".join(lines)


def neuro_body(notes: str, rows: list[dict], rich: bool = False, esc=escape) -> str:
    """Infusions, PRNs, paralytics, alphabetical categories, notes and other meds."""
    return render_body_blocks(system_body_blocks("Neurologic", notes, rows), rich, esc)


def cardiovascular_body(notes: str, rows: list[dict], rich: bool = False, esc=escape) -> str:
    return render_body_blocks(system_body_blocks("Cardiovascular", notes, rows), rich, esc)


def hematology_body(notes: str, rows: list[dict], rich: bool = False, esc=escape) -> str:
    return render_body_blocks(system_body_blocks("Hematology", notes, rows), rich, esc)


def respiratory_body(notes: str, rows: list[dict], rich: bool = False, esc=escape) -> str:
    return render_body_blocks(system_body_blocks("Respiratory", notes, rows), rich, esc)
