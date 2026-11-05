"""Deterministic SmartPhrase parsing. No OCR, external calls, or clinical inference."""
from __future__ import annotations

from dataclasses import dataclass, field
import re

SECTION_NAMES = {
    "a": "Diagnoses", "b": "Medications", "c": "Invasive Ventilation",
    "d": "Non-invasive Ventilation", "e": "VITALS", "f": "CULTURES",
    "g": "LABS", "h": "INTAKE/OUTPUT", "i": "NUTRITION", "j": "Wound Review",
    "k": "Target Arousal Level", "l": "WAT Score", "m": "ICP Trends",
}
MAX_PASTE = 150_000
DIVIDER = re.compile(r"^([a-m])\1{7,}$", re.I)
NUMBER_OR_BULLET = re.compile(r"^\s*(?:\d+[.)]\s+|[•\-]\s+)")


def _heading(line: str) -> str | None:
    text = line.strip().rstrip(":").strip().casefold()
    for key, value in SECTION_NAMES.items():
        if text == value.casefold():
            return key
    return None


@dataclass
class ParseResult:
    blocks: dict[str, str] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    invalid: set[str] = field(default_factory=set)
    diagnosis_error: str = ""
    diagnoses: list[str] = field(default_factory=list)


def parse_smartphrase(text: str) -> ParseResult:
    """Accept matching a..m divider lines of any length >= 8.

    Ambiguous/missing/duplicate boundaries fail closed for that section.
    Issues in a later section do not invalidate a complete, unambiguous a block.
    Patient content is never included in exception or diagnostic strings.
    """
    result = ParseResult()
    if not isinstance(text, str) or not text.strip():
        result.diagnosis_error = "Paste the SmartPhrase text first."
        return result
    if len(text) > MAX_PASTE:
        result.diagnosis_error = "The paste is too large. Use one patient's SmartPhrase."
        return result
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    active: str | None = None
    buffer: list[str] = []
    seen: dict[str, int] = {}
    outside = False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        marker = DIVIDER.fullmatch(line)
        if marker:
            key = marker.group(1).lower()
            if active == key:
                seen[key] = seen.get(key, 0) + 1
                if seen[key] > 1:
                    result.invalid.add(key)
                    result.issues.append(f"More than one {SECTION_NAMES[key]} block was found. Paste one patient at a time.")
                else:
                    result.blocks[key] = "\n".join(buffer).strip()
                active, buffer = None, []
            else:
                if active:
                    result.invalid.add(active)
                    result.issues.append(f"{SECTION_NAMES[active]} is missing its closing divider before line {n}.")
                active, buffer = key, []
            continue
        # A likely divider with one or more wrong letters is NOT silently corrected.
        if len(line) >= 8 and line.isalpha() and set(line.lower()) <= set("abcdefghijklm"):
            result.issues.append(f"Malformed divider on line {n}. Use only one repeated letter on that line.")
            if active:
                result.invalid.add(active)
            continue
        if active:
            buffer.append(raw)
        elif line:
            outside = True
    if active:
        result.invalid.add(active)
        result.issues.append(f"{SECTION_NAMES[active]} is missing its closing divider at the end.")
    if outside:
        result.issues.append("Text outside the paired dividers was not imported.")
    for key, body in list(result.blocks.items()):
        nonempty = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if not nonempty or _heading(nonempty[0]) != key:
            result.invalid.add(key)
            result.issues.append(f"The {SECTION_NAMES[key]} divider pair must begin with its matching heading.")
        elif any(_heading(ln) not in (None, key) for ln in nonempty[1:]):
            result.invalid.add(key)
            result.issues.append(f"Another section heading appears inside {SECTION_NAMES[key]}. Check the dividers.")
    if "a" not in result.blocks or "a" in result.invalid:
        result.diagnosis_error = "Diagnoses could not be imported safely. Use one complete a-divider pair with Diagnoses: inside."
        return result
    body = result.blocks["a"].splitlines()
    # Drop blank lines and the first heading only. Do not alter medical wording/codes.
    lines = [ln.strip() for ln in body if ln.strip()][1:]
    if not lines:
        result.diagnosis_error = "The Diagnoses section is empty. Existing content has not been changed."
        return result
    numbered = any(NUMBER_OR_BULLET.match(ln) for ln in lines)
    diagnoses: list[str] = []
    if numbered:
        for ln in lines:
            if NUMBER_OR_BULLET.match(ln):
                value = NUMBER_OR_BULLET.sub("", ln, count=1).strip()
                if value:
                    diagnoses.append(value)
            elif diagnoses:
                diagnoses[-1] += " " + ln
            else:
                diagnoses.append(ln)
    else:
        diagnoses = lines
    result.diagnoses = diagnoses
    if not diagnoses:
        result.diagnosis_error = "No diagnosis text was found. Existing content has not been changed."
    return result
