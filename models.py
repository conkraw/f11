"""Data model. All durable room and handoff data lives inside the encrypted vault."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
import uuid

SYSTEMS = (
    "Diagnoses", "Demographics / Weight", "Neurologic", "Respiratory",
    "Cardiovascular", "FEN / GI", "Hematology", "Infectious Disease",
    "Labs", "Skin / Wounds", "Tasks", "Other",
)
# Interpretation of the user's ranges: even P4102..P4116, then the listed 4200 rooms.
DEFAULT_ROOMS = [f"P{n}" for n in range(4102, 4117, 2)] + ["4201", "4203", "4209"] + [str(n) for n in range(4211, 4224, 2)]
MAX_FIELD = 20_000


class ValidationError(ValueError):
    """Only use static, patient-free messages for this exception."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_room(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9 -]{0,15}", value):
        raise ValidationError("Use a room label of 1 to 16 letters, digits, spaces or hyphens. Do not enter a patient name.")
    # Treat an optional P as an alias for the preset numerical room, not a new bed.
    digits = value[1:] if value.startswith("P") else value
    if digits.isdigit() and int(digits) in range(4102, 4117, 2):
        return "P" + digits
    if digits in DEFAULT_ROOMS:
        return digits
    return value


def new_sheet(room: str) -> dict:
    return {"id": uuid.uuid4().hex, "room": normalize_room(room), "created_at": utc_now(),
            "updated_at": None, "fields": {s: "" for s in SYSTEMS}}


def new_vault() -> dict:
    return {"schema": 1, "settings": {"diagnoses_destination": "Diagnoses", "rooms": list(DEFAULT_ROOMS)}, "rooms": {}}


def validate_sheet(sheet: dict) -> None:
    if not isinstance(sheet, dict) or set(sheet) != {"id", "room", "created_at", "updated_at", "fields"}:
        raise ValidationError("The handoff structure is invalid.")
    if not isinstance(sheet["id"], str) or not re.fullmatch(r"[0-9a-f]{32}", sheet["id"]):
        raise ValidationError("The handoff identifier is invalid.")
    if normalize_room(sheet["room"]) != sheet["room"]:
        raise ValidationError("The room label is not normalized.")
    if not isinstance(sheet["created_at"], str) or not isinstance(sheet["updated_at"], (str, type(None))):
        raise ValidationError("The handoff timestamps are invalid.")
    if not isinstance(sheet["fields"], dict) or set(sheet["fields"]) != set(SYSTEMS):
        raise ValidationError("The handoff section structure is invalid.")
    for value in sheet["fields"].values():
        if not isinstance(value, str) or len(value) > MAX_FIELD:
            raise ValidationError("A handoff section is too long or invalid.")


def validate_vault(vault: dict) -> None:
    if not isinstance(vault, dict) or set(vault) != {"schema", "settings", "rooms"} or vault["schema"] != 1:
        raise ValidationError("The encrypted archive has an unsupported structure. It was not overwritten.")
    settings = vault["settings"]
    if not isinstance(settings, dict) or set(settings) != {"diagnoses_destination", "rooms"}:
        raise ValidationError("The saved Admin settings are invalid.")
    if settings["diagnoses_destination"] not in SYSTEMS:
        raise ValidationError("The saved diagnosis destination is invalid.")
    if not isinstance(settings["rooms"], list) or not 1 <= len(settings["rooms"]) <= 100:
        raise ValidationError("The room list must contain between 1 and 100 rooms.")
    for room in settings["rooms"]:
        if normalize_room(room) != room:
            raise ValidationError("A saved room label is invalid.")
    if len(set(settings["rooms"])) != len(settings["rooms"]):
        raise ValidationError("The room list contains duplicates.")
    if not isinstance(vault["rooms"], dict) or len(vault["rooms"]) > 100:
        raise ValidationError("The archive has too many room handoffs.")
    for room, sheet in vault["rooms"].items():
        validate_sheet(sheet)
        if sheet["room"] != room:
            raise ValidationError("The saved handoff does not match its room.")


def save_sheet_in(vault: dict, sheet: dict) -> dict:
    validate_sheet(sheet)
    candidate = deepcopy(vault)
    saved = deepcopy(sheet)
    saved["updated_at"] = utc_now()
    candidate["rooms"][sheet["room"]] = saved
    validate_vault(candidate)
    return candidate


def apply_diagnoses(sheet: dict, diagnosis_text: str, destination: str, append: bool = False) -> dict:
    if destination not in SYSTEMS or not isinstance(diagnosis_text, str) or not diagnosis_text.strip():
        raise ValidationError("Choose a destination and enter diagnosis text before applying it.")
    result = deepcopy(sheet)
    existing = result["fields"][destination].rstrip()
    result["fields"][destination] = (existing + "\n" if append and existing else "") + diagnosis_text.strip()
    validate_sheet(result)
    return result
