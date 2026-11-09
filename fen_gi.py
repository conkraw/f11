"""User-requested FEN/GI display groups, not inferred medication indications.

The specified drug-name list supplies the automatic defaults. Per-formulation,
route and frequency choices can override them. Original medication fields and
saved system rules are not destroyed by presentation grouping.
"""
from __future__ import annotations
from copy import deepcopy
from html import escape
import re
from medications import match_name, normalized, visible, format_medication
from output_text import medication_output
from fluid_balance import balance_text
from feeds import feeds_text
from diet import diet_text
from medication_groups import group_for as special_group, GROUP_SECTIONS

MODES = ("auto", "prophylaxis", "bowel", "diuretic", "antiemetic", "endocrine", "other")
MODE_LABELS = {"auto": "Automatic", "prophylaxis": "GI prophylaxis", "bowel": "Bowel Regimen", "diuretic": "Diuretics", "antiemetic": "Antiemetics", "endocrine": "Endocrine Medications", "other": "No GI grouping"}
GROUP_NAMES = {"prophylaxis": "GI prophylaxis", "bowel": "Bowel Regimen", "diuretic": "Diuretics", "antiemetic": "Antiemetics", "endocrine": "Endocrine Medications"}


def automatic_group(row: dict) -> str:
    name = match_name(row.get("name", ""))
    if re.match(r"^(?:levothyroxine|synthroid|levoxyl|insulin|lantus|metformin)(?=$|[\s(,])", name):
        return "endocrine"
    if re.match(r"^(?:ondansetron|zofran)\b", name):
        return "antiemetic"
    if re.match(r"^(?:bumetanide|chlorothiazide|furosemide)\b", name):
        return "diuretic"
    if re.match(r"^(?:famotidine|omeprazole|pantoprazole)\b", name):
        return "prophylaxis"
    if re.match(r"^(?:docusate|lactulose|polyethylene\s+glycol|sennosides)\b", name):
        return "bowel"
    if re.match(r"^glycerin\b", name) and (re.search(r"\b(?:supp|suppository|suppositories|rectal)\b", name) or normalized(row.get("route", "")) == "rectal"):
        return "bowel"
    return ""


def group_for(row: dict) -> str:
    mode = row.get("gi_mode", "auto")
    return automatic_group(row) if mode == "auto" else mode if mode in GROUP_NAMES else ""


def effective_section(row: dict) -> str:
    special = special_group(row)
    if special:
        return GROUP_SECTIONS[special]
    return "FEN / GI" if group_for(row) else row["section"]


def gi_key(row: dict) -> tuple[str, str, str]:
    return match_name(row["name"]), normalized(row["route"]), normalized(row["frequency"])


def validate_gi_rules(rules: list[dict]) -> None:
    if not isinstance(rules, list) or len(rules) > 1500:
        raise ValueError("The FEN/GI display rules are invalid or too large.")
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"name", "route", "frequency", "mode"}:
            raise ValueError("A FEN/GI display rule has an invalid structure.")
        for key in ("name", "route", "frequency"):
            if not isinstance(rule[key], str) or len(rule[key]) > 4000 or any(c in rule[key] for c in "\n\r\t"):
                raise ValueError("A FEN/GI display rule contains invalid text.")
        if not rule["name"] or rule["mode"] not in ("prophylaxis", "bowel", "diuretic", "antiemetic", "endocrine", "other"):
            raise ValueError("A FEN/GI display rule has an invalid choice.")
        key = (rule["name"], rule["route"], rule["frequency"])
        if key in seen:
            raise ValueError("Duplicate FEN/GI display rules were found.")
        seen.add(key)


def set_gi_rule(rules: list[dict], row: dict, mode: str) -> list[dict]:
    if mode not in MODES:
        raise ValueError("Choose a valid FEN/GI display setting.")
    key = gi_key(row)
    result = [deepcopy(r) for r in rules if (r["name"], r["route"], r["frequency"]) != key]
    if mode != "auto":
        result.append(dict(zip(("name", "route", "frequency"), key), mode=mode))
    result.sort(key=lambda r: (r["name"], r["route"], r["frequency"]))
    validate_gi_rules(result)
    return result


def gi_mode_for(row: dict, rules: list[dict]) -> str:
    key = gi_key(row)
    return next((r["mode"] for r in rules if (r["name"], r["route"], r["frequency"]) == key), "auto")


def apply_gi_rules(rows: list[dict], rules: list[dict]) -> list[dict]:
    validate_gi_rules(rules)
    result = deepcopy(rows)
    for row in result:
        mode = gi_mode_for(row, rules)
        if mode != "auto" or "gi_mode" in row:
            row["gi_mode"] = mode
    return result


def fen_gi_body(notes: str, rows: list[dict], intake_output: dict | None, rich: bool = False, esc=escape, feeds: dict | None = None, feeds_failed: bool = False, diet: dict | None = None, diet_failed: bool = False, dosing_weight: str = "") -> str:
    """Totals, then feeds.  Each visible order appears exactly once, without changing doses."""
    encode = esc if rich else lambda s: s
    meds = [r for r in rows if visible(r) and effective_section(r) == "FEN / GI"]
    sections = []
    totals = balance_text(intake_output, dosing_weight)
    if totals:
        sections.append(encode(totals))
    diet_summary = diet_text(diet, rich, esc)
    if diet_failed:
        diet_summary = ("<b>Diet:</b>" if rich else "Diet:") + " Not updated. Review needed."
    if diet_summary:
        sections.append(diet_summary)
    feeding = feeds_text(feeds, rich, esc)
    if feeds_failed:
        feeding = ("<b>Feeds:</b>" if rich else "Feeds:") + "\nNot updated. Review needed."
    if feeding:
        sections.append(feeding)
    for mode, label in GROUP_NAMES.items():
        grouped = [r for r in meds if group_for(r) == mode]
        if grouped:
            heading = "<b>" + encode(label) + "</b>" if rich else label
            # Local import avoids the presentation-module import cycle. It is
            # evaluated only when rendering, after all modules are initialized.
            from infusions import infusion_entry, is_infusion
            entries = [(infusion_entry(r, rich, esc, handoff_only=True).replace("\n", "<br/>") if rich
                        else infusion_entry(r, False, esc, handoff_only=True))
                       if mode == "endocrine" and is_infusion(r)
                       else encode(medication_output(format_medication(r))) for r in grouped]
            sections.append("\n".join([heading] + entries))
    if notes.strip():
        sections.append(encode(notes.rstrip()))
    others = [r for r in meds if not group_for(r)]
    if others:
        heading = ("<b>Other FEN/GI medications</b>" if rich else "Other FEN/GI medications") if any(group_for(r) for r in meds) else ""
        sections.append("\n".join(([heading] if heading else []) + [encode(medication_output(format_medication(r))) for r in others]))
    return "\n-----\n".join(sections)
