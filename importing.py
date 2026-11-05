"""One-click A/B/C/D import with all-or-nothing updates for malformed input."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from models import validate_sheet, apply_diagnoses, apply_medications, apply_respiratory, ValidationError
from parser import parse_smartphrase, SECTION_NAMES, MAX_PASTE
from medications import parse_medications
from noninvasive import parse_respiratory


@dataclass
class ImportResult:
    sheet: dict | None = None
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    imported: list[str] = field(default_factory=list)


def import_sections(sheet: dict, text: str, settings: dict) -> ImportResult:
    out = ImportResult()
    if not isinstance(text, str) or not text.strip():
        out.errors.append("Paste the SmartPhrase first.")
        return out
    if len(text) > MAX_PASTE:
        out.errors.append("The paste is too large. Use one room at a time.")
        return out
    parsed = parse_smartphrase(text)
    relevant = set("abcd") & (set(parsed.blocks) | parsed.invalid)
    if not relevant:
        out.errors.append("No supported block was found. Use paired A, B, C or D dividers.")
        return out
    out.notices.extend(parsed.issues)
    candidate = deepcopy(sheet)
    for letter in "abcd":
        if letter in parsed.invalid:
            out.errors.append("Check the " + SECTION_NAMES[letter] + " dividers. Nothing was imported.")
            continue
        if letter not in parsed.blocks:
            continue
        try:
            if letter == "a":
                if parsed.diagnosis_error:
                    out.errors.append(parsed.diagnosis_error)
                    continue
                candidate = apply_diagnoses(candidate, "\n".join(parsed.diagnoses), settings["diagnoses_destination"])
                out.imported.append("Diagnoses")
            elif letter == "b":
                meds = parse_medications(parsed.blocks[letter], settings["medication_mappings"])
                if meds.error:
                    out.errors.extend([meds.error] + meds.issues)
                    continue
                candidate = apply_medications(candidate, meds.rows)
                out.imported.append(str(len(meds.rows)) + " medication orders")
            elif letter in "cd":
                if letter == "d" and ("c" in parsed.blocks or "c" in parsed.invalid):
                    continue  # C and D are interpreted together, once.
                if set("cd") & parsed.invalid:
                    continue  # The invalid divider is reported by the loop.
                vent = parse_respiratory(parsed.blocks.get("c"), parsed.blocks.get("d"))
                if vent.error:
                    out.errors.append(vent.error)
                    continue
                candidate = apply_respiratory(candidate, vent.invasive, vent.devices)
                out.notices.extend(vent.issues)
                out.imported.append("respiratory support" if vent.invasive or vent.devices else "respiratory display cleared")
        except (ValidationError, ValueError) as exc:
            out.errors.append(str(exc))
    if out.errors:
        out.imported = []
        return out
    validate_sheet(candidate)
    out.sheet = candidate
    return out
