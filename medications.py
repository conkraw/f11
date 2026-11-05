"""Parse Epic medication table rows, never infer a dose or therapeutic system.

TAB boundaries are authoritative. Providers and Last Admin are never retained.
Mapping rules match medication-name prefixes/exact names, not patient doses.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import re
import uuid

DESTINATIONS = ("Neurologic", "Respiratory", "Cardiovascular", "FEN / GI", "Hematology",
                "Infectious Disease", "Labs", "Skin / Wounds", "Other Medications")
BULLET = re.compile(r"^\s*[•●▪◦\-]\s*")
SPACE = re.compile(r"\s+")
RATE = re.compile(r"^\s*(\d+(?:\.\d+)?\s*(?:m[lL]|[uµμ]g|mcg|mg|g|units?|Units?|mEq)(?:\s*/\s*(?:kg|hr|min|h|day|24h)){1,3})\b", re.I)
FIELDS = {"id", "name", "dose", "route", "frequency", "last_rate", "rate_time", "section",
          "custom_text", "include", "warnings"}


def clean(value: str) -> str:
    return SPACE.sub(" ", value.replace("\u00a0", " ")).strip()


def normalized(value: str) -> str:
    return clean(value).casefold()


def match_name(value: str) -> str:
    return normalized(re.sub(r"^\s*\[(?:held by provider|discontinued)\]\s*", "", value, flags=re.I))


def suggested_key(name: str) -> str:
    """A stable name prefix, used only after a user chooses a destination."""
    head = re.split(r"\(|\d", re.sub(r"^\[[^]]+\]\s*", "", name), maxsplit=1)[0].strip()
    head = re.split(r"\s+(?:in\s+(?:NaCl|sodium chloride)|injection|infusion|syringe|nebulizer|ophthalmic|cream)\b", head, maxsplit=1, flags=re.I)[0]
    head = re.sub(r"\s+(?:NCS|PF|neo/ped)$", "", head, flags=re.I).strip(" ,-:;")
    head = re.sub(r"\s+continuous$", "", head, flags=re.I).strip()
    return normalized(head or name)


def destination_for(name: str, rules: list[dict]) -> str:
    name_key = match_name(name)
    choices = []
    for rule in rules:
        term = normalized(rule["name"])
        if rule["match"] == "exact":
            matched = name_key == term
        else:
            matched = name_key == term or (name_key.startswith(term) and len(name_key) > len(term)
                        and not name_key[len(term)].isalnum())
        if matched:
            choices.append((rule["match"] == "exact", len(term), rule["destination"]))
    return max(choices)[2] if choices else "Other Medications"


def validate_rules(rules: list[dict]) -> None:
    if not isinstance(rules, list) or len(rules) > 1500:
        raise ValueError("The medication mapping list is invalid or too large.")
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"name", "match", "destination"}:
            raise ValueError("A medication mapping has an invalid structure.")
        if not isinstance(rule["name"], str) or not 2 <= len(rule["name"]) <= 250 or '\n' in rule['name'] or '\t' in rule['name']:
            raise ValueError("Use a medication name of 2 to 250 characters, on one line.")
        if rule["match"] not in ("prefix", "exact") or rule["destination"] not in DESTINATIONS:
            raise ValueError("A medication mapping has an invalid destination or match type.")
        key = (normalized(rule["name"]), rule["match"])
        if key in seen:
            raise ValueError("Duplicate medication mappings were found.")
        seen.add(key)


def upsert_rule(rules: list[dict], name: str, destination: str, match: str = "prefix") -> list[dict]:
    rule = {"name": normalized(name), "match": match, "destination": destination}
    candidate = [deepcopy(r) for r in rules if (normalized(r["name"]), r["match"]) != (rule["name"], match)]
    candidate.append(rule)
    candidate.sort(key=lambda r: (r["name"], r["match"]))
    validate_rules(candidate)
    return candidate


def validate_medication(row: dict) -> None:
    if not isinstance(row, dict) or set(row) != FIELDS:
        raise ValueError("A medication entry has an invalid structure.")
    if not isinstance(row["id"], str) or not re.fullmatch(r"[0-9a-f]{32}", row["id"]):
        raise ValueError("A medication identifier is invalid.")
    for key in ("name", "dose", "route", "frequency", "last_rate", "rate_time", "custom_text"):
        if not isinstance(row[key], str) or len(row[key]) > 4000:
            raise ValueError("A medication entry is too long or invalid.")
    if not row["name"].strip() or row["section"] not in DESTINATIONS or not isinstance(row["include"], bool):
        raise ValueError("Check the medication name, destination, and inclusion setting.")
    if not isinstance(row["warnings"], list) or len(row["warnings"]) > 20 or any(not isinstance(v,str) or len(v)>500 for v in row["warnings"]):
        raise ValueError("Medication review warnings are invalid.")


def format_medication(row: dict) -> str:
    """Use explicit dose column. Keep different formulation/ordered doses visible."""
    if row.get("custom_text", "").strip():
        return row["custom_text"].strip()
    name, dose = row["name"].strip(), row["dose"].strip()
    text = name
    normalized_title, normalized_dose = normalized(name), normalized(dose)
    start = len(normalized_title) - len(normalized_dose)
    # 190 mg must NOT count as an existing 90 mg or 0 mg dose.
    duplicate_dose = bool(normalized_dose and normalized_title.endswith(normalized_dose)
                          and (start == 0 or normalized_title[start-1].isspace()
                               or normalized_title[start-1] in "(="))
    if dose and not duplicate_dose:
        text += " | Dose: " + dose
    continuous = bool(re.search(r"\bcontinuous\b", row["frequency"], re.I))
    # A pump rate on an intermittent medication is not a replacement for its dose.
    if continuous and row["last_rate"]:
        if normalized(dose) != normalized(row["last_rate"]):
            text += " @ " + row["last_rate"]
    if row["route"].strip():
        text += " | " + row["route"].strip()
    if row["frequency"].strip():
        text += " | " + row["frequency"].strip()
    return text


def remap(rows: list[dict], rules: list[dict]) -> list[dict]:
    result = deepcopy(rows)
    for row in result:
        row["section"] = destination_for(row["name"], rules)
    return result


@dataclass
class MedicationResult:
    rows: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    error: str = ""
    empty_confirmed: bool = False


def parse_medications(block: str, rules: list[dict] | None = None) -> MedicationResult:
    """Receive only a validated B block, not the entire SmartPhrase.

    The standard table is Medication, Dose, Route, Frequency, Provider,
    Last Rate, Last Admin. Tabs preserve blank dose/rate cells. A malformed
    or tab-less row stops the import, rather than guessing medication boundaries.
    """
    result = MedicationResult()
    rules = rules or []
    chunks: list[str] = []
    current = ""
    leftovers = []
    text = block.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if normalized(line.rstrip(':')) in ("medications", "current facility-administered medications"):
            continue
        if re.match(r"^Medication\s+Dose\s+Route\s+Frequency\b", line, flags=re.I):
            continue
        if normalized(line.rstrip('.')) in ("no current facility-administered medications", "no medications", "none"):
            result.empty_confirmed = True
            continue
        if BULLET.match(raw):
            if current:
                chunks.append(current)
            # Do not strip tabs. A trailing empty field is meaningful.
            current = BULLET.sub("", raw, count=1)
        elif '\t' in raw and not current:
            chunks.append(raw.lstrip(' '))
        elif current:
            # Newline inside an Epic row, before the next bullet.
            current += " " + raw.lstrip(' ')
        else:
            leftovers.append(line)
    if current:
        chunks.append(current)
    if leftovers:
        result.issues.append("Some text in the medication block was not a table row. Check that the full Epic table was copied.")
        result.error = "The medication block contains unrecognized text. Nothing has been applied. Copy the table again with its column tabs."
    if len(chunks) > 300:
        result.error = "Too many medication rows. Paste one patient at a time."
        return result
    for index, chunk in enumerate(chunks, 1):
        cols = [clean(c) for c in chunk.split('\t')]
        # Allow omitted trailing empty cells, but never infer missing internal columns.
        if len(cols) < 4 or len(cols) > 7:
            result.issues.append(f"Medication row {index}: columns could not be separated safely. Copy directly from Epic with tabs between cells.")
            result.error = "At least one medication row could not be read safely. Nothing has been applied."
            continue
        cols += [''] * (7-len(cols))
        name, dose, route, frequency, _provider, raw_rate, _last_admin = cols
        if not name or not route or not frequency:
            result.issues.append(f"Medication row {index}: name, route, or frequency is missing. Check the original table.")
            result.error = "At least one medication row is incomplete. Nothing has been applied."
            continue
        warnings = []
        rate, rate_time = '', ''
        if raw_rate:
            m = RATE.match(raw_rate)
            if m:
                rate = clean(m.group(1))
                tail = raw_rate[m.end():].strip()
                if tail.lower().startswith('at '):
                    rate_time = tail[3:].strip()
                elif tail:
                    warnings.append("The Last Rate field contained extra text. Verify the rate against Epic.")
            else:
                warnings.append("The Last Rate field could not be read as a numeric rate. Check Epic and edit the handoff wording if needed.")
        continuous = bool(re.search(r"\bcontinuous\b", frequency, re.I))
        if not dose:
            if continuous and rate:
                warnings.append("Dose was blank. The handoff uses Last Rate. Verify that the recorded rate is current.")
            else:
                warnings.append("Dose was blank in the source. No dose has been inferred.")
        if continuous and rate:
            warnings.append("The displayed infusion rate comes from Last Rate, not a live pump feed.")
            if re.match(r'^0(?:\.0+)?\s', rate):
                warnings.append("The last recorded rate is zero. This does not establish that the order was discontinued.")
        row = {"id": uuid.uuid4().hex, "name": name, "dose": dose, "route": route,
               "frequency": frequency, "last_rate": rate, "rate_time": rate_time,
               "section": destination_for(name, rules), "custom_text": "", "include": True,
               "warnings": warnings}
        validate_medication(row)
        result.rows.append(row)
    if not result.rows and not result.error and not result.empty_confirmed:
        result.error = "No medication rows were found. Existing medications have not been changed."
    if result.rows and result.empty_confirmed:
        result.error = "The block says no medications but also contains orders. Check the source before importing."
    return result


def rule_for_inline_mapping(name: str, rules: list[dict]) -> tuple[str, str]:
    """Reuse the most specific matching rule, else a dose-free name prefix.

    Prefer a more-specific generated formulation prefix over a broad matched
    prefix (for example heparin flush rather than heparin). Exact rules remain
    editable without creating a conflicting lower-priority rule.
    """
    name_key = match_name(name)
    matches = []
    for rule in rules:
        term = normalized(rule["name"])
        if rule["match"] == "exact":
            match = name_key == term
        else:
            match = name_key == term or (name_key.startswith(term) and len(name_key) > len(term) and not name_key[len(term)].isalnum())
        if match:
            matches.append(rule)
    suggested = suggested_key(name)
    if matches:
        best = max(matches, key=lambda r: (r["match"] == "exact", len(normalized(r["name"]))))
        if best["match"] == "exact" or len(normalized(best["name"])) >= len(suggested):
            return best["name"], best["match"]
    return suggested, "prefix"
