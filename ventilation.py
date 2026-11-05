"""A deterministic import rule for the C block, not an airway diagnosis.

Only explicitly recognized mode names are included. BiLevel, CPAP, BiPAP,
NIV and high-flow terms are excluded per the requested display rule. Mode
names alone cannot establish whether an airway is invasive. No values from
D or E, target Vt, observed rate, billing, or equipment fields are substituted.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re

LABELS = (
    "Vent Mode",
    "Resp Rate (Set)",
    "Vt (Set, mL)",
    "PEEP (cm H2O)",
    "Mean Airway Pressure",
    "Insp Time (sec)",
    "PIP Observed (cm H2O)",
    "Pressure Support (cm H2O)",
    "Trigger Sensitivity Flow (L/min)",
    "FiO2 (%)",
)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def mode_rule(mode: str) -> str:
    """Return included, excluded or unknown. No clinical inference is performed."""
    text = normalize(mode).replace("–", "-").replace("—", "-")
    if re.search(r"\b(?:bi[ -]?level|bi[ -]?pap|cpap|niv|nippv|hfnc)\b|non[ -]?invasive|high[ -]?flow", text):
        return "excluded"
    # Explicitly supported source labels. Unrecognized labels are never guessed.
    families = (
        "volume targeted pressure control", "pressure regulated volume control",
        "pressure control", "volume control", "synchronized intermittent mandatory ventilation",
        "intermittent mandatory ventilation", "assist control",
    )
    for prefix in families:
        if text == prefix or text.startswith(prefix + " -") or text.startswith(prefix + " ("):
            return "included"
    if re.fullmatch(r"(?:simv|prvc|pcv|vcv|a/c|ac|pc-ac|vc-ac)(?:[ /+()-]+(?:pc|vc|prvc|ps|pressure support|volume control|pressure control))*", text):
        return "included"
    return "unknown"


def validate_ventilation(data: dict | None) -> None:
    if data is None:
        return
    if not isinstance(data, dict) or set(data) != {"mode", "values"}:
        raise ValueError("The saved ventilation block has an invalid structure.")
    if not isinstance(data["mode"], str) or not data["mode"].strip() or len(data["mode"]) > 500 or "\n" in data["mode"] or "\r" in data["mode"]:
        raise ValueError("The ventilation mode is empty or too long.")
    if mode_rule(data["mode"]) != "included":
        raise ValueError("This mode is not included by the automatic invasive-ventilation display rule.")
    values = data["values"]
    if not isinstance(values, dict) or not set(values).issubset(set(LABELS[1:])):
        raise ValueError("The ventilation block contains an unexpected field.")
    for value in values.values():
        if not isinstance(value, str) or len(value) > 500 or "\n" in value or "\r" in value:
            raise ValueError("A ventilation value is invalid or too long.")


def format_ventilation(data: dict | None) -> str:
    validate_ventilation(data)
    if data is None:
        return ""
    lines = ["Vent Mode: " + data["mode"].strip()]
    for label in LABELS[1:]:
        value = data["values"].get(label, "").strip()
        if value:
            lines.append(label + ": " + value)
    return "\n".join(lines)


@dataclass
class VentilationResult:
    data: dict | None = None
    status: str = "empty"
    issues: list[str] = field(default_factory=list)
    error: str = ""


def parse_ventilation(block: str) -> VentilationResult:
    result = VentilationResult()
    aliases = {normalize(label): label for label in LABELS}
    # Subscript characters in labels are typography only. Values stay verbatim.
    def label_key(label: str) -> str:
        return normalize(label.replace("₂", "2"))
    entries: dict[str, str] = {}
    meaningful = []
    for raw in block.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = raw.strip()
        if not line or normalize(line.rstrip(":")) in ("invasive ventilation", "vent information", "settings"):
            continue
        meaningful.append(line)
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        label = aliases.get(label_key(label))
        if label is None:
            continue
        value = value.strip()
        if len(value) > 500:
            result.error = "A requested ventilation value is too long. Nothing was imported."
            return result
        if label in entries and entries[label] != value:
            result.error = "The C block contains conflicting repeated ventilation fields. Nothing was imported."
            return result
        entries[label] = value
    mode = entries.get("Vent Mode", "").strip()
    if not mode:
        if not meaningful or all(normalize(x.rstrip(".")) in ("none", "no invasive ventilation", "not documented", "no results found") for x in meaningful):
            result.status = "empty"
        else:
            result.error = "No Vent Mode was found in the C block. The previous handoff was not changed."
        return result
    result.status = mode_rule(mode)
    if result.status == "excluded":
        result.issues.append("The C-block mode is excluded by your display rule (for example, BiLevel or CPAP). No invasive ventilation block was added.")
        return result
    if result.status == "unknown":
        result.issues.append("The C-block mode is not recognized by the automatic display rule. No invasive ventilation block was added. You can document it in Respiratory notes.")
        return result
    result.data = {"mode": mode, "values": {label: entries[label] for label in LABELS[1:] if entries.get(label, "").strip()}}
    try:
        validate_ventilation(result.data)
    except ValueError as exc:
        result.data = None
        result.error = str(exc)
        return result
    missing = [label for label in LABELS[1:] if not entries.get(label, "").strip()]
    if missing:
        result.issues.append("Requested fields absent from C were left out: " + ", ".join(missing) + ".")
    return result
