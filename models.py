"""Data model. All durable room and handoff data lives inside the encrypted vault."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
import uuid

LEGACY_SYSTEMS = (
    "Diagnoses", "Demographics / Weight", "Neurologic", "Respiratory",
    "Cardiovascular", "FEN / GI", "Hematology", "Infectious Disease",
    "Labs", "Skin / Wounds", "Tasks", "Other",
)
SYSTEMS = LEGACY_SYSTEMS + ("Other Medications", "Lab Results / Trends", "Goals / Follow-up", "Airway", "Last Intubation", "Access", "Drains / Tubes")
from medications import validate_medication, validate_rules, format_medication, validate_visibility, visible
from ventilation import validate_ventilation, format_ventilation
from noninvasive import validate_noninvasive, format_noninvasive
from labs import empty_labs, validate_labs, labs_text, lactate_text
from vitals import validate_vitals, text_by_system
from observations import empty_neuro, validate_neuro, neuro_rows, validate_nutrition, format_nutrition

SCHEMA_VERSION = 7

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
            "updated_at": None, "fields": {s: "" for s in SYSTEMS}, "medications": [], "ventilation": None, "noninvasive": [], "vitals": [], "labs": empty_labs(), "neuro_vitals": empty_neuro(), "nutrition": None}


def new_vault() -> dict:
    return {"schema": SCHEMA_VERSION, "settings": {"diagnoses_destination": "Diagnoses", "rooms": list(DEFAULT_ROOMS), "medication_mappings": [], "medication_visibility": []}, "rooms": {}}


def validate_sheet(sheet: dict) -> None:
    if not isinstance(sheet, dict) or set(sheet) != {"id", "room", "created_at", "updated_at", "fields", "medications", "ventilation", "noninvasive", "vitals", "labs", "neuro_vitals", "nutrition"}:
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

    if not isinstance(sheet["medications"], list) or len(sheet["medications"]) > 300:
        raise ValidationError("The medication list is invalid or too large.")
    try:
        validate_ventilation(sheet["ventilation"])
        validate_noninvasive(sheet["noninvasive"])
        validate_vitals(sheet["vitals"])
        validate_labs(sheet["labs"])
        validate_neuro(sheet["neuro_vitals"])
        validate_nutrition(sheet["nutrition"])
    except ValueError as exc:
        raise ValidationError(str(exc)) from None
    ids = set()
    for row in sheet["medications"]:
        try:
            validate_medication(row)
        except ValueError as exc:
            raise ValidationError(str(exc)) from None
        if row["id"] in ids:
            raise ValidationError("Medication row identifiers must be unique.")
        ids.add(row["id"])


def validate_vault(vault: dict) -> None:
    if not isinstance(vault, dict) or set(vault) != {"schema", "settings", "rooms"} or vault["schema"] != SCHEMA_VERSION:
        raise ValidationError("The encrypted archive has an unsupported structure. It was not overwritten.")
    settings = vault["settings"]
    if not isinstance(settings, dict) or set(settings) != {"diagnoses_destination", "rooms", "medication_mappings", "medication_visibility"}:
        raise ValidationError("The saved Admin settings are invalid.")
    try:
        validate_rules(settings["medication_mappings"])
        validate_visibility(settings["medication_visibility"])
    except ValueError as exc:
        raise ValidationError(str(exc)) from None
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


def upgrade_vault(vault: dict) -> dict:
    """Migrate schemas 1-6 without replacing keys, notes or saved mappings."""
    if not isinstance(vault, dict) or set(vault) != {"schema", "settings", "rooms"}:
        raise ValidationError("The encrypted archive has an invalid structure.")
    version = vault.get("schema")
    if version == SCHEMA_VERSION:
        validate_vault(vault)
        return vault
    if version not in (1, 2, 3, 4, 5, 6):
        raise ValidationError("The encrypted archive has an unsupported structure. It was not overwritten.")
    candidate = deepcopy(vault)
    settings = candidate["settings"]
    expected_settings = {"diagnoses_destination", "rooms"} | ({"medication_mappings"} if version >= 2 else set())
    if version >= 6:
        expected_settings.add("medication_visibility")
    if not isinstance(settings, dict) or set(settings) != expected_settings or not isinstance(candidate["rooms"], dict):
        raise ValidationError("The previous archive structure is invalid. Nothing was discarded.")
    if version == 1:
        settings["medication_mappings"] = []
    if version < 6:
        settings["medication_visibility"] = []
    for sheet in candidate["rooms"].values():
        expected = {"id", "room", "created_at", "updated_at", "fields"}
        if version >= 2:
            expected.add("medications")
        if version >= 3:
            expected.add("ventilation")
        if version >= 4:
            expected.add("noninvasive")
        if version >= 6:
            expected.update({"vitals", "labs"})
        if not isinstance(sheet, dict) or set(sheet) != expected:
            raise ValidationError("A previous handoff structure is invalid. Nothing was discarded.")
        expected_fields = set(LEGACY_SYSTEMS if version == 1 else SYSTEMS)
        if not isinstance(sheet["fields"], dict) or set(sheet["fields"]) != expected_fields:
            raise ValidationError("A previous handoff has unexpected fields. Nothing was discarded.")
        if version == 1:
            for section in SYSTEMS:
                sheet["fields"].setdefault(section, "")
            sheet["medications"] = []
        if version < 3:
            sheet["ventilation"] = None
        if version < 4:
            sheet["noninvasive"] = []
        elif version == 4:
            if not isinstance(sheet["noninvasive"], list):
                raise ValidationError("The previous respiratory support list is invalid.")
            for device in sheet["noninvasive"]:
                if (not isinstance(device, dict)
                        or set(device) != {"device", "values", "flow_inferred"}
                        or device["device"] not in ("BiPAP", "CPAP", "HFNC")):
                    raise ValidationError("A previous respiratory entry is invalid. Nothing was discarded.")
                device["pressure_inferred"] = False
        if version < 6:
            sheet["vitals"] = []
            sheet["labs"] = empty_labs()
            for row in sheet["medications"]:
                if "hidden" in row:
                    raise ValidationError("The previous medication structure is invalid.")
                row["hidden"] = False
        sheet["neuro_vitals"] = empty_neuro()
        sheet["nutrition"] = None
    candidate["schema"] = SCHEMA_VERSION
    validate_vault(candidate)
    return candidate


def apply_medications(sheet: dict, rows: list[dict]) -> dict:
    """Replace the previous medication import, never append duplicate orders.

    System notes remain separate, so reimporting/remapping cannot erase them.
    Each source order remains separate even when names/doses repeat.
    """
    candidate = deepcopy(sheet)
    candidate["medications"] = deepcopy(rows)
    validate_sheet(candidate)
    return candidate


def fields_with_medications(sheet: dict, include_lab_text: bool = True) -> dict[str, str]:
    validate_sheet(sheet)
    result = dict(sheet["fields"])
    for row in sheet["medications"]:
        if not visible(row):
            continue
        section = row["section"]
        content = format_medication(row)
        result[section] = (result[section].rstrip() + "\n" if result[section].strip() else "") + content
    vent = respiratory_text(sheet)
    if vent:
        result["Respiratory"] = vent + "\n-----" + ("\n" + result["Respiratory"] if result["Respiratory"].strip() else "")
    lactate = lactate_text(sheet["labs"])
    if lactate:
        result["Cardiovascular"] = lactate + ("\n-----\n" + result["Cardiovascular"] if result["Cardiovascular"].strip() else "")
    for section, text in automatic_vitals(sheet).items():
        result[section] = text + ("\n-----\n" + result[section] if result[section].strip() else "")
    nutrition = format_nutrition(sheet["nutrition"])
    if nutrition:
        diagnosis = result["Diagnoses"].rstrip()
        result["Diagnoses"] = (diagnosis + "\n----\n" if diagnosis else "") + nutrition
    if include_lab_text:
        laboratory = labs_text(sheet["labs"])
        if laboratory:
            result["Lab Results / Trends"] = laboratory + ("\n" + result["Lab Results / Trends"] if result["Lab Results / Trends"].strip() else "")
    return result


def apply_ventilation(sheet: dict, data: dict | None) -> dict:
    result = deepcopy(sheet)
    result["ventilation"] = deepcopy(data)
    validate_sheet(result)
    return result


def respiratory_text(sheet: dict) -> str:
    """Automatic support only, before the separator, notes and medications."""
    parts = [format_ventilation(sheet["ventilation"]), format_noninvasive(sheet["noninvasive"])]
    return "\n".join(part for part in parts if part)


def apply_respiratory(sheet: dict, invasive: dict | None, devices: list[dict]) -> dict:
    """Replace the support snapshot only. Never merge it with old device settings."""
    result = deepcopy(sheet)
    result["ventilation"] = deepcopy(invasive)
    result["noninvasive"] = deepcopy(devices)
    validate_sheet(result)
    return result


def automatic_vitals(sheet: dict) -> dict[str, str]:
    """Keep imported neurologic observations before notes and medications."""
    return text_by_system(neuro_rows(sheet["neuro_vitals"]) + sheet["vitals"])
