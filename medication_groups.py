"""User-selected display groups. These labels do not infer clinical indications.

Heparin qualification inspects the ordered Dose only, never product strength or
pump rate. A grouping changes presentation, not the source order or clinical use.
"""
from __future__ import annotations
from copy import deepcopy
import re
from medications import match_name, normalized

MODES = ("auto", "dvt", "fever", "sedative_prn", "paralytic_prn", "other")
MODE_LABELS = {"auto": "Automatic", "dvt": "DVT Prophylaxis", "fever": "Fever Control",
               "sedative_prn": "PRN", "paralytic_prn": "Paralytic PRN", "other": "No special grouping"}
GROUP_NAMES = {key: MODE_LABELS[key] for key in ("dvt", "fever", "sedative_prn", "paralytic_prn")}
GROUP_SECTIONS = {"dvt": "Hematology", "fever": "Neurologic", "sedative_prn": "Neurologic", "paralytic_prn": "Neurologic"}


def is_prn(row: dict) -> bool:
    """Only the recorded frequency establishes PRN status."""
    return bool(re.search(r"\bprn\b|\bas[ -]+needed\b", normalized(row.get("frequency", ""))))


def automatic_group(row: dict) -> str:
    name = match_name(row.get("name", ""))
    if re.match(r"^(?:enoxaparin|cangrelor)\b", name):
        return "dvt"
    if re.match(r"^heparin\b", name):
        # Avoid flush/lock mixtures even if an unusual source has a misleading dose.
        if re.search(r"\b(?:flush|lock|taurolidine)\b", name) or normalized(row.get("route", "")) in {"intracatheter", "irrigation"}:
            return ""
        dose = normalized(row.get("dose", ""))
        # Keep exact units. A numeric value or range must occur in Dose.
        if re.search(r"(?<![\w/])\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s*units?\s*/\s*kg\s*/\s*(?:hr|h|hour)(?![\w/])", dose):
            return "dvt"
    if re.match(r"^(?:acetaminophen|ibuprofen)\b", name):
        return "fever"
    if is_prn(row):
        if re.match(r"^(?:fentanyl|midazolam|ketamine|morphine|hydromorphone)\b", name):
            return "sedative_prn"
        if re.match(r"^(?:rocuronium|cisatracurium|vecuronium)\b", name):
            return "paralytic_prn"
    return ""


def group_for(row: dict) -> str:
    mode = row.get("group_mode", "auto")
    # An explicit GI override wins over automatic defaults, not over an explicit
    # special-group choice. UI callbacks clear the competing explicit choice.
    if mode == "auto" and row.get("gi_mode", "auto") in ("prophylaxis", "bowel", "diuretic"):
        return ""
    return automatic_group(row) if mode == "auto" else mode if mode in GROUP_NAMES else ""


def group_key(row: dict) -> tuple[str, str, str]:
    return match_name(row["name"]), normalized(row["route"]), normalized(row["frequency"])


def validate_group_rules(rules: list[dict]) -> None:
    if not isinstance(rules, list) or len(rules) > 1500:
        raise ValueError("The medication group rules are invalid or too large.")
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"name", "route", "frequency", "mode"}:
            raise ValueError("A medication group rule has an invalid structure.")
        for key in ("name", "route", "frequency"):
            if not isinstance(rule[key], str) or len(rule[key]) > 4000 or any(c in rule[key] for c in "\n\r\t"):
                raise ValueError("A medication group rule contains invalid text.")
        if not rule["name"] or rule["mode"] not in MODES[1:]:
            raise ValueError("A medication group rule has an invalid choice.")
        key = (rule["name"], rule["route"], rule["frequency"])
        if key in seen:
            raise ValueError("Duplicate medication group rules were found.")
        seen.add(key)


def set_group_rule(rules: list[dict], row: dict, mode: str) -> list[dict]:
    if mode not in MODES:
        raise ValueError("Choose a valid medication group.")
    key = group_key(row)
    result = [deepcopy(r) for r in rules if (r["name"], r["route"], r["frequency"]) != key]
    if mode != "auto":
        result.append(dict(zip(("name", "route", "frequency"), key), mode=mode))
    result.sort(key=lambda r: (r["name"], r["route"], r["frequency"]))
    validate_group_rules(result)
    return result


def group_mode_for(row: dict, rules: list[dict]) -> str:
    key = group_key(row)
    return next((r["mode"] for r in rules if (r["name"], r["route"], r["frequency"]) == key), "auto")


def apply_group_rules(rows: list[dict], rules: list[dict]) -> list[dict]:
    validate_group_rules(rules)
    result = deepcopy(rows)
    for row in result:
        mode = group_mode_for(row, rules)
        if mode != "auto" or "group_mode" in row:
            row["group_mode"] = mode
    return result
