"""One-click A/B/C/D/E/F/G/I/K/L/M/N/O/P/Q/R/S import with independent section recovery and explicit retained-data warnings."""
from __future__ import annotations
from copy import deepcopy
import re
from dataclasses import dataclass, field
from models import validate_sheet, apply_diagnoses, apply_medications, apply_respiratory, ValidationError
from parser import parse_smartphrase, SECTION_NAMES, MAX_PASTE
from medications import parse_medications
from infusions import apply_infusion_rules
from noninvasive import parse_respiratory
from labs import parse_labs
from vitals import parse_vitals
from observations import parse_neuro, parse_nutrition
from cultures import parse_cultures
from demographics import parse_admission
from viral import parse_viral_panel
from blood_gases import parse_gases
from cbc import parse_cbc
from recurring_orders import parse_orders, selected_orders
from fluid_balance import parse_balance
from fen_gi import apply_gi_rules
from medication_groups import apply_group_rules
from import_review import diagnostic, diagnostic_text

SUPPORTED_SECTIONS = "abcdefgiklmnopqrs"


@dataclass
class ImportResult:
    sheet: dict | None = None
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    imported: list[str] = field(default_factory=list)
    diagnostics: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def import_sections(sheet: dict, text: str, settings: dict) -> ImportResult:
    out = ImportResult()
    if not isinstance(text, str) or not text.strip():
        out.errors.append("Paste the SmartPhrase first.")
        return out
    if len(text) > MAX_PASTE:
        out.errors.append("The paste is too large. Use one room at a time.")
        return out
    parsed = parse_smartphrase(text)
    relevant = set(SUPPORTED_SECTIONS) & (set(parsed.blocks) | parsed.invalid)
    if not relevant:
        out.errors.append("No supported block was found. Use paired A, B, C, D, E, F, G, I, K, L, M, N, O, P, Q, R or S dividers.")
        return out
    # Repeated paired sections can mean two patients were pasted together.
    # That document-wide identity ambiguity cannot be repaired by partial import.
    if any(message.startswith("More than one ") for message in parsed.issues):
        out.errors.append("Repeated sections may contain more than one patient. Nothing was changed.")
        out.diagnostics.append(diagnostic('document', 'document_rejected', action='nothing_changed'))
        return out
    out.notices.extend(parsed.issues)
    candidate = deepcopy(sheet)
    def reject(group, code='section_parse_failed', line=0):
        nonlocal candidate
        item = diagnostic(group, code,
                          action='orders_hidden' if group == 'r' else 'not_updated', line=line)
        candidate['import_warnings'][group] = [item]
        out.diagnostics.append(item)
        if group not in out.skipped:
            out.skipped.append(group)

    for letter in SUPPORTED_SECTIONS:
        group = 'cd' if letter in 'cd' else letter
        if letter == 'd' and ('c' in parsed.blocks or 'c' in parsed.invalid):
            continue
        if letter in 'cd' and set('cd') & parsed.invalid:
            out.errors.append('Respiratory support: check the C/D dividers. This section was not updated.')
            reject('cd', 'section_boundary')
            continue
        if letter in parsed.invalid:
            out.errors.append("Check the " + SECTION_NAMES[letter] + " dividers. This section was not updated.")
            reject(group, "section_boundary")
            continue
        if letter not in parsed.blocks:
            continue
        before = deepcopy(candidate)
        error_count, import_count = len(out.errors), len(out.imported)
        recoveries = []
        failure_code = "section_parse_failed"
        try:
            if letter == "a":
                if parsed.diagnosis_error:
                    out.errors.append(parsed.diagnosis_error)
                    continue
                candidate = apply_diagnoses(candidate, "\n".join(parsed.diagnoses), settings["diagnoses_destination"])
                out.imported.append("Diagnoses")
            elif letter == "b":
                meds = parse_medications(parsed.blocks[letter], settings["medication_mappings"], settings.get("medication_visibility", []))
                if meds.error:
                    out.errors.extend([meds.error] + meds.issues)
                    continue
                candidate = apply_medications(candidate, apply_group_rules(apply_gi_rules(apply_infusion_rules(meds.rows, settings.get("medication_infusions", [])), settings.get("medication_gi_groups", [])), settings.get("medication_groups", [])))
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
            elif letter == "e":
                vitals = parse_vitals(parsed.blocks[letter])
                if vitals.error:
                    out.errors.append(vitals.error)
                    continue
                candidate["vitals"] = vitals.rows
                out.notices.extend(vitals.issues)
                out.imported.append("vital signs")
            elif letter == "f":
                cultures = parse_cultures(parsed.blocks[letter])
                if cultures.error:
                    out.errors.append(cultures.error)
                    continue
                candidate["cultures"] = cultures.data
                out.notices.extend(cultures.issues)
                out.imported.append("cultures" if cultures.data["rows"] else "culture display cleared")
            elif letter == "g":
                labs = parse_labs(parsed.blocks[letter])
                if labs.error:
                    out.errors.append(labs.error)
                    continue
                candidate["labs"] = labs.data
                out.notices.extend(labs.issues)
                out.imported.append("laboratory results")
            elif letter == "i":
                nutrition = parse_nutrition(parsed.blocks[letter])
                if nutrition.error:
                    out.errors.append(nutrition.error)
                    continue
                candidate["nutrition"] = nutrition.data
                candidate["dosing_weight"] = nutrition.dosing_weight
                out.notices.extend(nutrition.issues)
                out.imported.append("weight / dosing weight / Z-score" if nutrition.data or nutrition.dosing_weight else "weight display cleared")
            elif letter == "n":
                admission = parse_admission(parsed.blocks[letter])
                if admission.error:
                    out.errors.append(admission.error)
                    continue
                candidate["admission_date"] = admission.date
                out.imported.append("admission date" if admission.date else "admission date cleared")
            elif letter == "o":
                viral = parse_viral_panel(parsed.blocks[letter])
                if viral.error:
                    out.errors.append(viral.error)
                    continue
                candidate["viral_panel"] = viral.data
                out.notices.extend(viral.issues)
                out.imported.append("respiratory viral panel")
            elif letter == "p":
                gas = parse_gases(parsed.blocks[letter])
                if gas.error:
                    out.errors.append(gas.error)
                    continue
                candidate["blood_gas"] = gas.data
                out.notices.extend(gas.issues)
                out.imported.append("latest blood gas" if gas.data["samples"] else "blood gas display cleared")
            elif letter == "q":
                cbc = parse_cbc(parsed.blocks[letter])
                if cbc.error:
                    out.errors.append(cbc.error)
                    continue
                candidate["cbc"] = cbc.data
                recoveries = cbc.diagnostics[:100]
                out.notices.extend(cbc.issues)
                out.imported.append("CBC and latest ANC / ALC" if cbc.data["rows"] else "CBC display cleared")
            elif letter == "r":
                orders = parse_orders(parsed.blocks[letter])
                if orders.error:
                    out.errors.append(orders.error)
                    continue
                candidate["recurring_orders"] = orders.data
                out.notices.extend(orders.issues)
                count = len(selected_orders(orders.data))
                out.imported.append(str(count) + " recurring lab/imaging orders" if count else "recurring lab/imaging orders cleared")
            elif letter == "s":
                balance = parse_balance(parsed.blocks[letter])
                if balance.error:
                    out.errors.append(balance.error)
                    continue
                candidate["intake_output"] = balance.data
                out.notices.extend(balance.issues)
                out.imported.append("intake / output totals" if balance.data else "intake / output display cleared")
            elif letter in "klm":
                observations = parse_neuro(parsed.blocks[letter], letter)
                if observations.error:
                    out.errors.append(observations.error)
                    continue
                candidate["neuro_vitals"][letter] = observations.rows
                out.notices.extend(observations.issues)
                out.imported.append(SECTION_NAMES[letter] if observations.rows else SECTION_NAMES[letter] + " display cleared")
            validate_sheet(candidate)
        except (ValidationError, ValueError) as exc:
            out.errors.append(str(exc))
        except Exception:
            # Do not log the exception body, source text or stack locals.
            failure_code = 'parser_exception'
            out.errors.append('An unexpected parser problem occurred in this section.')
        finally:
            if len(out.errors) > error_count:
                candidate = before
                del out.imported[import_count:]
                if group == 'r' and failure_code == 'section_parse_failed':
                    message = ' '.join(out.errors[error_count:]).lower()
                    failure_code = ('orders_count' if 'occurrence' in message else
                                    'orders_timing' if 'timing' in message else 'orders_structure')
                match = re.search(r"(?:row|line) (\d+)", out.errors[error_count], re.I)
                reject(group, failure_code, int(match.group(1)) if match else 0)
                for index in range(error_count, len(out.errors)):
                    message = out.errors[index].replace('Nothing was imported.', '').replace('Nothing has been applied.', '')
                    out.errors[index] = SECTION_NAMES[letter] + ': ' + message.strip() + ' Only this section was skipped.'
            elif len(out.imported) > import_count:
                candidate['import_warnings'].pop(group, None)
                if recoveries:
                    candidate['import_warnings'][group] = recoveries
                    out.diagnostics.extend(recoveries)
    validate_sheet(candidate)
    out.sheet = candidate
    return out
