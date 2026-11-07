"""PICU SmartPhrase v6.21: keep emphasized infusions in the DVT group."""
from __future__ import annotations
from copy import deepcopy
from html import escape
from pathlib import Path
import time
import json
from datetime import datetime, timezone

import streamlit as st
from cryptography.fernet import Fernet
from exports import handoff_html, handoff_text, handoff_pdf, handoffs_pdf, handoffs_html, print_layout_info, download_payload
from github_store import GitHubConfig, GitHubVault, StorageError
from error_store import ErrorJournal, new_error_event
from import_review import review_summary, diagnostic_text, SECTIONS as REVIEW_SECTIONS
from models import (MAX_FIELD, SYSTEMS, ValidationError, new_sheet, new_vault,
                    normalize_room, save_sheet_in, validate_vault, validate_sheet,
                    upgrade_vault, fields_with_medications, respiratory_text, automatic_vitals, SCHEMA_VERSION, DEFAULT_ROOMS, section_label)
from medications import (DESTINATIONS, format_medication, suggested_key, upsert_rule,
                         remap, rule_for_inline_mapping, validate_medication, visible, hidden_for, set_visibility_rule)
from ventilation import LABELS, format_ventilation, validate_ventilation
from noninvasive import DEVICE_FIELDS, format_noninvasive, validate_noninvasive
from importing import import_sections, SUPPORTED_SECTIONS
from batching import available_handoffs
from save_status import (room_save_status, saved_time_text, latest_saved_time,
                         most_recent_save_caption, save_status_table)
from parser import MAX_PASTE, SECTION_NAMES
from security import valid_password_hash, verify_password
from labs import validate_labs, lactate_text, id_labs_text, theophylline_text
from cbc import validate_cbc, cbc_summary, cbc_selection_issues
from recurring_orders import validate_orders, selected_orders, orders_text, order_line, recurring_frequency
from blood_gases import FIELDS as GAS_FIELDS, validate_gases, latest_sample, gas_summary, legacy_gases
from vitals import validate_vitals, text_by_system
from lab_layout import laboratory_html
from observations import NEURO_SECTIONS, validate_neuro, validate_nutrition, format_nutrition
from demographics import validate_dosing_weight, validate_admission_date, demographic_weight_text
from cultures import validate_cultures, cultures_text, compact_groups, category_for
from viral import validate_viral_panel, viral_text
from microbiology_display import culture_markup, viral_markup
from fluid_balance import FIELDS as IO_FIELDS, META_FIELDS as IO_META_FIELDS, validate_balance, balance_text, empty_balance
from fen_gi import (MODES as GI_MODES, MODE_LABELS as GI_MODE_LABELS, GROUP_NAMES,
                    automatic_group, group_for, effective_section, fen_gi_body,
                    apply_gi_rules, set_gi_rule, gi_key, gi_mode_for)
from infusions import (MODES, MODE_LABELS, is_infusion, infusion_entry, neuro_body, cardiovascular_body, hematology_body,
                       set_infusion_rule, apply_infusion_rules, infusion_key, infusion_mode_for, respiratory_body, INFUSION_SECTIONS, DISPLAY_LABELS, supports_infusion_display)

from medication_groups import (MODES as GROUP_MODES, MODE_LABELS as GROUP_MODE_LABELS,
    GROUP_SECTIONS, group_for as special_group, automatic_group as automatic_special_group,
    apply_group_rules, set_group_rule, group_key, group_mode_for)

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="PICU Handoff", layout="wide", initial_sidebar_state="expanded")


def note(text: str, kind: str = "info") -> None:
    st.session_state["notice"] = (kind, text)


def clear_session() -> None:
    st.session_state.clear()


def require_session() -> bool:
    now = time.monotonic()
    ss = st.session_state
    if (not ss.get("authenticated")
            or now - ss.get("last_activity", 0) > ss.get("idle_seconds", 900)
            or now - ss.get("login_at", 0) > 8 * 3600):
        clear_session()
        return False
    ss["last_activity"] = now
    return True


def authenticate(encoded: str) -> None:
    now = time.monotonic()
    if now < st.session_state.get("retry_after", 0):
        st.session_state.pop("login_password", None)
        return
    password = st.session_state.pop("login_password", "")
    if verify_password(password, encoded):
        clear_session()
        st.session_state.update(authenticated=True, last_activity=now, login_at=now)
    else:
        attempts = min(st.session_state.get("attempts", 0) + 1, 10)
        st.session_state.update(attempts=attempts, retry_after=now + min(30, 2 ** attempts),
                                login_error="Password not accepted. Wait briefly before trying again.")


def edit_key(sheet: dict, section: str) -> str:
    return "field_" + sheet["id"] + "_" + str(SYSTEMS.index(section))


def discard_editor_widget_values() -> None:
    for key in list(st.session_state):
        if key.startswith(("field_", "med_draft_", "med_pending_", "vent_", "niv_", "lab_", "vital_", "neuro_", "weight_", "culture_", "demo_", "viral_", "gas_", "cbc_", "rorder_", "io_")):
            st.session_state.pop(key, None)


def set_editor(room: str, sheet: dict) -> None:
    validate_sheet(sheet)
    discard_editor_widget_values()
    st.session_state.setdefault("drafts", {})[room] = deepcopy(sheet)
    st.session_state["paste"] = ""
    st.session_state.pop("import_result", None)


def editor_snapshot(room: str) -> dict:
    """Capture current widget values before a room callback clears widgets.

    Streamlit can deliver a blurred text edit and a room change in one event.
    Read only widget keys belonging to the outgoing sheet. Validate the whole
    candidate before any save or switch. No pasted source text enters storage.
    """
    ss = st.session_state
    sheet = deepcopy(ss["drafts"][room])
    for section in SYSTEMS:
        key = edit_key(sheet, section)
        if key in ss:
            sheet["fields"][section] = ss[key]
    for row in sheet["medications"]:
        old_signature = infusion_key(row)
        old_mode = row.get("infusion_mode", "auto")
        old_gi_mode = row.get("gi_mode", "auto")
        old_group_mode = row.get("group_mode", "auto")
        old_effective = effective_section(row)
        prefix = "med_draft_" + row["id"] + "_"
        for field in ("name", "dose", "route", "frequency", "last_rate", "rate_time", "section", "custom_text", "include", "infusion_mode", "gi_mode", "group_mode"):
            if prefix + field in ss:
                if field == "section" and ss[prefix + field] == old_effective:
                    continue  # The automatic FEN/GI label is not a changed saved mapping.
                row[field] = ss[prefix + field]
        if row.get("gi_mode", "auto") != old_gi_mode and row.get("gi_mode", "auto") not in ("auto", "other"):
            row["group_mode"] = "auto"
        if infusion_key(row) != old_signature and row.get("infusion_mode", "auto") == old_mode:
            row["infusion_mode"] = infusion_mode_for(row, ss["vault"]["settings"]["medication_infusions"])
        if infusion_key(row) != old_signature and row.get("gi_mode", "auto") == old_gi_mode:
            row["gi_mode"] = gi_mode_for(row, ss["vault"]["settings"]["medication_gi_groups"])
        if infusion_key(row) != old_signature and row.get("group_mode", "auto") == old_group_mode:
            row["group_mode"] = group_mode_for(row, ss["vault"]["settings"]["medication_groups"])
        if prefix + "section" in ss and ss[prefix + "section"] != old_effective:
            if row["section"] != "FEN / GI":
                row["gi_mode"] = "other"
            group = special_group(row)
            if group and row["section"] != GROUP_SECTIONS[group]:
                row["group_mode"] = "other"
    if sheet["intake_output"] is not None:
        for field in IO_FIELDS + IO_META_FIELDS + ("include",):
            key = "io_" + sheet["id"] + "_" + field
            if key in ss:
                sheet["intake_output"][field] = ss[key].strip() if isinstance(ss[key], str) else ss[key]
    for group, prefix, fields in (
        (sheet["labs"]["rows"], "lab_", ("value", "date", "include")),
        (sheet["viral_panel"]["rows"], "viral_", ("name", "result", "date", "include")),
        (sheet["cultures"]["rows"], "culture_", ("date", "specimen", "organisms", "include")),
    ):
        for row in group:
            for field in fields:
                key = prefix + row["id"] + "_" + field
                if key in ss:
                    value = ss[key]
                    if field == "organisms":
                        value = [line.strip() for line in value.splitlines() if line.strip()]
                    row[field] = value
    if sheet["recurring_orders"] is not None:
        for row in sheet["recurring_orders"]["rows"]:
            for field in ("name", "timing", "occurrences", "include"):
                key = "rorder_" + row["id"] + "_" + field
                if key in ss:
                    row[field] = order_widget_value(field, ss[key])
    if sheet["cbc"] is not None:
        for row in sheet["cbc"]["rows"]:
            dkey = "cbc_date_" + sheet["id"] + "_" + str(row["column"])
            if dkey in ss:
                row["date"] = ss[dkey].strip()
            for field in ("value", "unit", "include"):
                key = "cbc_" + row["id"] + "_" + field
                if key in ss:
                    row[field] = ss[key].strip() if isinstance(ss[key], str) else ss[key]
    if sheet["blood_gas"] is not None:
        for sample in sheet["blood_gas"]["samples"]:
            prefix = "gas_" + sample["id"] + "_"
            for field in ("date", "include"):
                if prefix + field in ss:
                    sample[field] = ss[prefix + field]
            for index, label in enumerate(GAS_FIELDS):
                if label in sample["values"]:
                    for field in ("value", "unit"):
                        key = prefix + str(index) + "_" + field
                        if key in ss:
                            sample["values"][label][field] = ss[key].strip()
    for index, row in enumerate(sheet["vitals"]):
        key = "vital_" + sheet["id"] + "_" + str(index)
        for field, widget in (("value", key), ("include", key + "_include")):
            if widget in ss:
                row[field] = ss[widget]
    for source, rows in sheet["neuro_vitals"].items():
        for index, row in enumerate(rows):
            key = "neuro_" + sheet["id"] + "_" + source + "_" + str(index)
            for field, widget in (("value", key), ("include", key + "_include")):
                if widget in ss:
                    row[field] = ss[widget]
    if sheet["nutrition"] is not None:
        for field in ("weight", "z_score", "include"):
            key = "weight_" + sheet["id"] + "_" + field
            if key in ss:
                value = ss[key]
                sheet["nutrition"][field] = value.strip() if isinstance(value, str) else value
    for field in ("admission_date", "dosing_weight"):
        key = "demo_" + sheet["id"] + "_" + field
        if key in ss:
            sheet[field] = ss[key].strip()
    if sheet["ventilation"] is not None:
        for index, label in enumerate(LABELS):
            key = "vent_" + sheet["id"] + "_" + str(index)
            if key not in ss:
                continue
            value = ss[key].strip()
            if index == 0:
                sheet["ventilation"]["mode"] = value
            elif value:
                sheet["ventilation"]["values"][label] = value
            else:
                sheet["ventilation"]["values"].pop(label, None)
    for device in sheet["noninvasive"]:
        for index, label in enumerate(DEVICE_FIELDS[device["device"]]):
            key = "niv_" + sheet["id"] + "_" + device["device"] + "_" + str(index)
            if key in ss:
                value = ss[key].strip()
                if value:
                    device["values"][label] = value
                else:
                    device["values"].pop(label, None)
    validate_sheet(sheet)
    return sheet


def autosave_before_room_change(store: GitHubVault | None) -> bool:
    ss = st.session_state
    room = ss.get("current_room")
    if not room or room not in ss.get("drafts", {}):
        return True
    try:
        draft = editor_snapshot(room)
    except (ValueError, TypeError, KeyError) as exc:
        note("The current room was not saved or changed. Correct the highlighted editor value before switching rooms. " + str(exc), "error")
        return False
    # Keep the original draft and all widgets until the write is confirmed.
    # A retry captures the same values, including pending mapping changes.
    prior = ss["drafts"][room]
    if draft == ss["vault"]["rooms"].get(room):
        return True
    if ss.get("base_sheets", {}).get(room) != ss["vault"]["rooms"].get(room):
        note("Autosave was blocked because the saved room changed. You are still in the current room and your edits are kept. Reload the archive and compare before saving.", "error")
        return False
    try:
        candidate = deepcopy(ss["vault"])
        rules = candidate["settings"]["medication_mappings"]
        changed_rules = False
        infusion_rules = candidate["settings"]["medication_infusions"]
        gi_rules = candidate["settings"]["medication_gi_groups"]
        group_rules = candidate["settings"]["medication_groups"]
        old_rows = {row["id"]: row for row in prior["medications"]}
        for row in draft["medications"]:
            old = old_rows.get(row["id"])
            if old is not None and old["section"] != row["section"]:
                name, match = rule_for_inline_mapping(row["name"], rules)
                rules = upsert_rule(rules, name, row["section"], match)
                changed_rules = True
            if old is not None and old.get("infusion_mode", "auto") != row.get("infusion_mode", "auto"):
                infusion_rules = set_infusion_rule(infusion_rules, row, row.get("infusion_mode", "auto"))
                changed_rules = True
            if old is not None and old.get("gi_mode", "auto") != row.get("gi_mode", "auto"):
                gi_rules = set_gi_rule(gi_rules, row, row.get("gi_mode", "auto"))
                changed_rules = True
            if old is not None and old.get("group_mode", "auto") != row.get("group_mode", "auto"):
                group_rules = set_group_rule(group_rules, row, row.get("group_mode", "auto"))
                changed_rules = True
        if changed_rules:
            candidate["settings"]["medication_groups"] = group_rules
            candidate["settings"]["medication_gi_groups"] = gi_rules
            candidate["settings"]["medication_mappings"] = rules
            candidate["settings"]["medication_infusions"] = infusion_rules
            draft["medications"] = apply_group_rules(apply_gi_rules(apply_infusion_rules(remap(draft["medications"], rules, candidate["settings"]["medication_visibility"]), infusion_rules), gi_rules), group_rules)
        candidate = save_sheet_in(candidate, draft)
        commit(candidate, store)
    except (StorageError, ValidationError, ValueError) as exc:
        note("Autosave failed. You are still in the current room and your edits are kept. " + str(exc), "error")
        return False
    except Exception:
        # A custom storage implementation must not cause a silent room switch.
        note("Autosave was not confirmed. You are still in the current room and your edits are kept. Check the connection and retry.", "error")
        return False
    saved = deepcopy(candidate["rooms"][room])
    ss["drafts"][room] = saved
    ss.setdefault("base_sheets", {})[room] = deepcopy(saved)
    if changed_rules:
        reapply_open_mappings()
    message = ("Previous room automatically saved to encrypted GitHub." if store else
               "Previous room saved in this session only. GitHub storage is not enabled.")
    note(message + " Last saved: " + saved_time_text(saved["updated_at"]),
         "success" if store else "info")
    return True


def open_room(store: GitHubVault | None = None) -> None:
    if not require_session():
        return
    ss = st.session_state
    choice = ss.get("room_choice", "")
    if choice == "Choose a room":
        return
    value = ss.get("other_room", "") if choice == "Other room" else choice
    try:
        room = normalize_room(value)
    except ValidationError as exc:
        note(str(exc), "error")
        return
    old_room = ss.get("current_room")
    if room == old_room:
        ss["room_choice"] = room
        return
    if not autosave_before_room_change(store):
        ss["room_choice"] = old_room or "Choose a room"
        return
    ss["current_room"] = room
    ss["room_choice"] = room
    drafts = ss.setdefault("drafts", {})
    if room not in drafts:
        saved = ss["vault"]["rooms"].get(room)
        ss.setdefault("base_sheets", {})[room] = deepcopy(saved)
        set_editor(room, saved if saved else new_sheet(room))
    else:
        discard_editor_widget_values()
        ss["paste"] = ""
        ss.pop("import_result", None)


def room_changed(store: GitHubVault | None = None) -> None:
    if not require_session():
        return
    ss = st.session_state
    if ss.get("room_choice") in ("Choose a room", "Other room"):
        # Selecting Other hides the current editor too, so save before that.
        if not autosave_before_room_change(store):
            ss["room_choice"] = ss.get("current_room", "Choose a room")
        return
    open_room(store)


def update_field(room: str, section: str, key: str) -> None:
    if require_session() and room == st.session_state.get("current_room") and key in st.session_state:
        st.session_state["drafts"][room]["fields"][section] = st.session_state[key]


def load_neuro_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_neuro_weight.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def load_compact_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_compact_pn.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def load_observed_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_observed_vt.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def neuro_row_change(room: str, source: str, index: int, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    candidate = deepcopy(ss["drafts"][room]["neuro_vitals"])
    if source not in candidate or not 0 <= index < len(candidate[source]) or field not in ("value", "include"):
        return
    old = candidate[source][index][field]
    candidate[source][index][field] = ss[key]
    try:
        validate_neuro(candidate)
        ss["drafts"][room]["neuro_vitals"] = candidate
    except ValueError as exc:
        ss[key] = old
        note(str(exc), "error")


def nutrition_change(room: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    current = ss["drafts"][room]["nutrition"]
    if current is None or field not in ("weight", "z_score", "include"):
        return
    candidate = deepcopy(current)
    candidate[field] = ss[key].strip() if isinstance(ss[key], str) else ss[key]
    try:
        validate_nutrition(candidate)
        ss["drafts"][room]["nutrition"] = candidate
    except ValueError as exc:
        ss[key] = current[field]
        note(str(exc), "error")


def demographic_change(room: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    validators = {"dosing_weight": validate_dosing_weight, "admission_date": validate_admission_date}
    if field not in validators:
        return
    ss = st.session_state
    old = ss["drafts"][room][field]
    value = ss[key].strip()
    try:
        validators[field](value)
        ss["drafts"][room][field] = value
    except ValueError as exc:
        ss[key] = old
        note(str(exc), "error")


def load_demographics_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_demographics_labs.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)



def load_viral_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_viral_positive.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def viral_row_change(room: str, row_id: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    if field not in ("name", "result", "date", "include"):
        return
    ss = st.session_state
    candidate = deepcopy(ss["drafts"][room]["viral_panel"])
    row = next((r for r in candidate["rows"] if r["id"] == row_id), None)
    if row is None:
        return
    old = row[field]
    value = ss[key]
    row[field] = value.strip() if isinstance(value, str) else value
    try:
        validate_viral_panel(candidate)
        ss["drafts"][room]["viral_panel"] = candidate
    except ValueError as exc:
        ss[key] = old
        note(str(exc), "error")


def viral_editor(sheet: dict) -> None:
    st.subheader("Rapid Viral Panel")
    data = sheet["viral_panel"]
    summary = viral_text(data)
    if summary:
        st.markdown('<div style="white-space:pre-wrap">' + viral_markup(data) + '</div>', unsafe_allow_html=True)
    else:
        st.caption("No positive viral results selected for the handoff.")
    st.caption("Only explicit Detected / Positive results print below a separator in the patient column. Source dates stay here, not on the compact summary. A newer negative or unresolved result does not reuse an older positive.")
    if not data["rows"]:
        st.caption("Paste a paired O block headed Respiratory Viral Panel to add results.")
        return
    with st.expander("Edit viral results and display names (" + str(len(data["rows"])) + ")"):
        st.caption("The code-to-name aliases are editable labels. HUMRHINENRNA is displayed as Rhinovirus/enterovirus, without splitting the combined target. Unfamiliar codes remain unchanged.")
        for row in data["rows"]:
            st.text(row["component"] + " | " + row["result"] + " | " + row["date"])
            for field, label in (("name", "Display name"), ("result", "Source result"), ("date", "Source date / optional time"), ("include", "Include if positive")):
                key = "viral_" + row["id"] + "_" + field
                if key not in st.session_state:
                    st.session_state[key] = row[field]
                kwargs = dict(key=key, on_change=viral_row_change, args=(sheet["room"], row["id"], field, key))
                if field == "include":
                    st.checkbox(label, **kwargs)
                else:
                    st.text_input(label, max_chars={"name": 200, "result": 500, "date": 80}[field], **kwargs)

def neuro_weight_editor(sheet: dict) -> None:
    st.subheader("Neurologic observations")
    st.caption("K: target arousal, L: WAT-1, M: ICP/CPP. Values print at the top of NEURO. Empty sections add nothing. A zero score is retained.")
    present = False
    for source, title in NEURO_SECTIONS.items():
        for index, row in enumerate(sheet["neuro_vitals"][source]):
            present = True
            key = "neuro_" + sheet["id"] + "_" + source + "_" + str(index)
            if key not in st.session_state:
                st.session_state[key] = row["value"]
            st.text_input(row["label"], key=key, max_chars=1500, on_change=neuro_row_change,
                          args=(sheet["room"], source, index, "value", key))
            ikey = key + "_include"
            if ikey not in st.session_state:
                st.session_state[ikey] = row["include"]
            st.checkbox("Include " + row["label"], key=ikey, on_change=neuro_row_change,
                        args=(sheet["room"], source, index, "include", ikey))
    if not present:
        st.caption("No recorded neurologic observations. Paste K, L and/or M to add them.")
    st.subheader("Demographics / Weight")
    st.caption("Admission is shown in the patient column. Below Diagnoses: weight, Z-score when supplied, then dosing weight. A blank dosing-weight field prints Dosing weight: none. Clearing admission omits that date.")
    field = "admission_date"
    key = "demo_" + sheet["id"] + "_" + field
    if key not in st.session_state:
        st.session_state[key] = sheet[field]
    st.text_input("Date of admission", key=key, max_chars=32,
                  on_change=demographic_change, args=(sheet["room"], field, key))
    data = sheet["nutrition"]
    if data is None:
        st.caption("Paste the I block to add a measured weight. Dosing weight is kept separately.")
    else:
        for field, label in (("weight", "Recorded measured weight, with unit"), ("z_score", "Recorded Z-score"), ("include", "Include measured weight and Z-score")):
            key = "weight_" + sheet["id"] + "_" + field
            if key not in st.session_state:
                st.session_state[key] = data[field]
            kwargs = dict(key=key, on_change=nutrition_change, args=(sheet["room"], field, key))
            if field == "include":
                st.checkbox(label, **kwargs)
            else:
                st.text_input(label, max_chars=80 if field == "weight" else 40, **kwargs)
    field = "dosing_weight"
    key = "demo_" + sheet["id"] + "_" + field
    if key not in st.session_state:
        st.session_state[key] = sheet[field]
    st.text_input("Dosing weight, with unit (blank prints none)", key=key, max_chars=80,
                  on_change=demographic_change, args=(sheet["room"], field, key))


def load_taper_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_medication_taper.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def load_labs_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_labs_vitals.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def change_visibility_rule(name: str, hidden: bool, match: str, store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    candidate = deepcopy(ss["vault"])
    try:
        candidate["settings"]["medication_visibility"] = set_visibility_rule(candidate["settings"]["medication_visibility"], name, hidden, match)
        commit(candidate, store)
        reapply_open_mappings()
        note(("Medication hidden from exports and kept for restoration." if hidden else "Medication restored to exports.") + (" Rule saved to encrypted GitHub." if store else " Session-only mode."), "success")
    except (ValueError, StorageError) as exc:
        note(str(exc) + " The visibility rule was not changed.", "error")


def hide_medication(room: str, row_id: str, hidden: bool, store: GitHubVault | None) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    row = next((r for r in st.session_state["drafts"][room]["medications"] if r["id"] == row_id), None)
    if row:
        change_visibility_rule(row["name"], hidden, "exact", store)


def visibility_admin(store: GitHubVault | None) -> None:
    st.subheader("Hidden medication rules")
    rules = st.session_state["vault"]["settings"]["medication_visibility"]
    st.caption("Hide/restore choices are remembered independently of system mappings. Full retained entries remain in their handoffs. No open handoff is needed to restore a rule here.")
    hidden = [r for r in rules if r["hidden"]]
    if not hidden:
        st.caption("No hidden medication rules.")
    for i, rule in enumerate(hidden):
        st.text(rule["name"] + " [" + rule["match"] + "]")
        st.button("Restore this medication", key="restore_rule_" + str(i), on_click=change_visibility_rule,
                  args=(rule["name"], False, rule["match"], store))
    with st.expander("Previously restored rules"):
        for i, rule in enumerate(rules):
            if not rule["hidden"]:
                st.text(rule["name"] + " [" + rule["match"] + "]")
                st.button("Hide again", key="rehide_rule_" + str(i), on_click=change_visibility_rule,
                          args=(rule["name"], True, rule["match"], store))



def load_cultures_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_cultures_ads.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def culture_row_change(room: str, row_id: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    snapshot = ss["drafts"][room]["cultures"]
    candidate = deepcopy(snapshot)
    row = next((r for r in candidate["rows"] if r["id"] == row_id), None)
    if row is None or field not in ("date", "specimen", "organisms", "include"):
        return
    previous = row[field]
    row[field] = ([x.strip() for x in ss[key].splitlines() if x.strip()]
                  if field == "organisms" else ss[key])
    try:
        validate_cultures(candidate)
        ss["drafts"][room]["cultures"] = candidate
    except ValueError as exc:
        ss[key] = "\n".join(previous) if field == "organisms" else previous
        note(str(exc), "error")


def cultures_editor(sheet: dict) -> None:
    st.subheader("Cultures to Infectious Disease")
    st.caption("Prints the two newest collection-date/specimen groups per category: blood, respiratory, urine, and other sites. Same date and site rows are combined for display only, with all their distinct organisms and statuses. No sensitivity columns are stored or printed.")
    st.caption("Collection IDs are not supplied. A displayed group is not proof of one culture. Same-date ties keep source order. Unspecified aspirates stay under their own site rather than being assumed respiratory.")
    data = sheet["cultures"]
    text = cultures_text(data)
    if text:
        st.markdown('<div style="white-space:pre-wrap">' + culture_markup(data) + '</div>', unsafe_allow_html=True)
    else:
        st.caption("No culture results selected. Paste an F block to import them.")
    for message in data["notes"]:
        st.caption(message)
    selected = {key for group in compact_groups(data) for key in group["row_ids"]}
    with st.expander("Edit retained culture rows (" + str(len(data["rows"])) + ")"):
        for number, row in enumerate(data["rows"], 1):
            status = "shown in compact output" if row["id"] in selected else "older / excluded from compact output"
            st.text(str(number) + ". " + row["date"] + " | " + row["specimen"] + " | " + status)
            st.caption("Category: " + category_for(row["specimen"]))
            for field, label in (("date", "Collection date / optional time"), ("specimen", "Sample location"),
                                 ("organisms", "Organisms / results, one per line"), ("include", "Include in newest-result selection")):
                key = "culture_" + row["id"] + "_" + field
                if key not in st.session_state:
                    st.session_state[key] = "\n".join(row[field]) if field == "organisms" else row[field]
                kwargs = dict(key=key, on_change=culture_row_change, args=(sheet["room"], row["id"], field, key))
                if field == "include":
                    st.checkbox(label, **kwargs)
                elif field == "organisms":
                    st.text_area(label, height=90, max_chars=20000, **kwargs)
                else:
                    st.text_input(label, max_chars=80 if field == "date" else 500, **kwargs)


def lab_row_change(room: str, row_id: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    snapshot = ss["drafts"][room]["labs"]
    candidate = deepcopy(snapshot)
    row = next((r for r in candidate["rows"] if r["id"] == row_id), None)
    if row is None:
        return
    previous = row[field]
    row[field] = ss[key]
    try:
        validate_labs(candidate)
        ss["drafts"][room]["labs"] = candidate
    except ValueError as exc:
        ss[key] = previous
        note(str(exc), "error")


def vital_row_change(room: str, index: int, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    candidate = deepcopy(ss["drafts"][room]["vitals"])
    previous = candidate[index][field]
    candidate[index][field] = ss[key]
    try:
        validate_vitals(candidate)
        ss["drafts"][room]["vitals"] = candidate
    except ValueError as exc:
        ss[key] = previous
        note(str(exc), "error")


def cbc_edit(room: str, row_id: str, field: str, key: str, column: int = -1) -> None:
    if not require_session():
        return
    ss = st.session_state
    if room != ss.get("current_room"):
        return
    data = ss["drafts"][room]["cbc"]
    if data is None:
        return
    candidate = deepcopy(data)
    targets = [row for row in candidate["rows"] if row["column"] == column] if field == "date" else [row for row in candidate["rows"] if row["id"] == row_id]
    if not targets:
        return
    previous = targets[0][field]
    value = ss[key].strip() if isinstance(ss[key], str) else ss[key]
    for row in targets:
        row[field] = value
    try:
        validate_cbc(candidate)
        ss["drafts"][room]["cbc"] = candidate
    except ValueError as exc:
        ss[key] = previous
        note(str(exc), "error")


def cbc_editor(sheet: dict) -> None:
    st.subheader("CBC / absolute counts")
    data = sheet["cbc"]
    st.caption("Q keeps each CBC column together. Standard hemoglobin is preferred over ISTAT across the supplied snapshot. ANC and ALC are the latest absolute counts across automatic/manual rows, with their own dates. No percentages are converted.")
    if data is None:
        st.caption("No Q snapshot yet. Earlier G-block CBC rows remain available until a Q block replaces their display.")
        return
    if not data["rows"]:
        st.caption("The included Q section contains no CBC results. Older G-block CBC results are not substituted.")
        return
    for issue in data.get("notes", []):
        if issue.startswith("CBC"):
            st.caption(issue)
    for issue in cbc_selection_issues(data):
        st.caption(issue)
    with st.expander("Edit retained CBC results (" + str(len(data["rows"])) + ")"):
        columns = list(dict.fromkeys(row["column"] for row in data["rows"]))
        for column in columns:
            rows = [row for row in data["rows"] if row["column"] == column]
            st.text("CBC source column " + str(column + 1))
            key = "cbc_date_" + sheet["id"] + "_" + str(column)
            if key not in st.session_state:
                st.session_state[key] = rows[0]["date"]
            st.text_input("Collection date / time (whole column)", key=key, max_chars=80,
                          on_change=cbc_edit, args=(sheet["room"], "", "date", key, column))
            for row in rows:
                st.text(row["component"] + " | " + row["value"] + " " + row["unit"])
                if "|" in row["value"]:
                    st.warning("Multiple source results in this cell. It is excluded from the CBC tree. Replace it with a verified single result before including it.")
                for field, label in (("value", "Recorded CBC result"), ("unit", "Source unit"), ("include", "Include result in CBC selection")):
                    key = "cbc_" + row["id"] + "_" + field
                    if key not in st.session_state:
                        st.session_state[key] = row[field]
                    kwargs = dict(key=key, on_change=cbc_edit, args=(sheet["room"], row["id"], field, key))
                    if field == "include":
                        st.checkbox(label, **kwargs)
                    else:
                        st.text_input(label, max_chars=100 if field == "value" else 50, **kwargs)


def gas_edit(room: str, sample_id: str, label: str, field: str, key: str) -> None:
    if not require_session():
        return
    ss = st.session_state
    if room != ss.get("current_room"):
        return
    data = ss["drafts"][room]["blood_gas"]
    if data is None:
        return
    candidate = deepcopy(data)
    sample = next((row for row in candidate["samples"] if row["id"] == sample_id), None)
    if sample is None:
        return
    target = sample["values"][label] if label else sample
    old = target[field]
    target[field] = ss[key].strip() if isinstance(ss[key], str) else ss[key]
    try:
        validate_gases(candidate)
        ss["drafts"][room]["blood_gas"] = candidate
    except ValueError as exc:
        ss[key] = old
        note(str(exc), "error")


def gas_editor(sheet: dict) -> None:
    st.subheader("Latest blood gas")
    data = sheet["blood_gas"]
    selection_data = legacy_gases(sheet["labs"]) if data is None else data
    sample, issues = latest_sample(selection_data)
    if sample:
        st.text(gas_summary(selection_data))
    else:
        st.caption("No gas results selected. Paste the paired P block to add the latest gas.")
    if data is None and sample:
        st.caption("This is a legacy G-block result. A date-only listing cannot establish a common draw or exact time. Paste P for timed column-based selection.")
    for issue in issues:
        st.caption(issue)
    if data is None:
        return
    st.caption("The newest included specimen/column prints once. Empty and hidden cells are not backfilled. Older columns stay available here but do not print.")
    with st.expander("Review retained gas columns (" + str(len(data["samples"])) + ")"):
        for sample in data["samples"]:
            prefix = "gas_" + sample["id"] + "_"
            st.text(sample["specimen"] + " | " + sample["date"])
            for field, label in (("date", "Gas collection date / time"), ("include", "Include this gas in latest selection")):
                key = prefix + field
                if key not in st.session_state:
                    st.session_state[key] = sample[field]
                kwargs = dict(key=key, on_change=gas_edit, args=(sheet["room"], sample["id"], "", field, key))
                if field == "include":
                    st.checkbox(label, **kwargs)
                else:
                    st.text_input(label, max_chars=80, **kwargs)
            for index, label in enumerate(GAS_FIELDS):
                if label not in sample["values"]:
                    continue
                for field in ("value", "unit"):
                    key = prefix + str(index) + "_" + field
                    if key not in st.session_state:
                        st.session_state[key] = sample["values"][label][field]
                    st.text_input(label + (" result" if field == "value" else " source unit"), key=key,
                                  max_chars=100 if field == "value" else 50,
                                  on_change=gas_edit, args=(sheet["room"], sample["id"], label, field, key))


def labs_vitals_editor(sheet: dict) -> None:
    import streamlit.components.v1 as components
    neuro_weight_editor(sheet)
    viral_editor(sheet)
    st.subheader("Laboratory results")
    st.caption("Q supplies the two latest CBC columns. BMP and older G-only CBCs retain per-component selection. Other tests show the latest result per component. Only one latest gas is printed, labeled VEN, ART or CAP. The P table keeps specimen and column values together. Dates and source flags are preserved. No collection times or same-draw groupings are invented.")
    components.html('<style>.labcards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}.labcard{width:100%;border:1px solid #aaa}.labnote{font:13px sans-serif;margin:8px 0}.lab-summary{font:14px/1.3 sans-serif;overflow-wrap:anywhere;margin:3px 0}.lab-full{grid-column:1/-1}</style>' + laboratory_html(sheet["labs"], blood_gas=sheet["blood_gas"], cbc=sheet["cbc"]), height=490, scrolling=True)
    if theophylline_text(sheet["labs"]):
        st.text("Respiratory: " + theophylline_text(sheet["labs"]))
    if lactate_text(sheet["labs"]):
        st.text("Cardiovascular: " + lactate_text(sheet["labs"]))
    if id_labs_text(sheet["labs"]):
        st.text("Infectious Disease:\n" + id_labs_text(sheet["labs"]))
    st.caption("Glucose is in the BMP tree. Mg and phosphorus are below it. Albumin stays in Hepatic. Coagulation, including Anti-Xa (HEPLMW), is immediately below Hepatic in the lab results. CRP and procalcitonin (PROCAL) remain in ID below temperature. The latest THEOPH result prints as Theophylline level in Respiratory, below support settings and above medications.")
    with st.expander("Edit retained laboratory rows (" + str(len(sheet["labs"]["rows"])) + ")"):
        for row in sheet["labs"]["rows"]:
            st.text(row["component"] + " | " + row["value"] + " | " + row["date"])
            for field, label in (("value", "Result"), ("date", "Source date / optional time"), ("include", "Include in lab selection")):
                key = "lab_" + row["id"] + "_" + field
                if key not in st.session_state:
                    st.session_state[key] = row[field]
                kwargs = dict(key=key, on_change=lab_row_change, args=(sheet["room"], row["id"], field, key))
                if field == "include":
                    st.checkbox(label, **kwargs)
                else:
                    st.text_input(label, max_chars=1000 if field == "value" else 80, **kwargs)
    cbc_editor(sheet)
    gas_editor(sheet)
    st.subheader("Vital signs")
    if not sheet["vitals"]:
        st.caption("Paste an E block to add vital signs.")
    for index, row in enumerate(sheet["vitals"]):
        st.text(row["label"] + " -> " + row["section"])
        key = "vital_" + sheet["id"] + "_" + str(index)
        if key not in st.session_state:
            st.session_state[key] = row["value"]
        st.text_input(row["label"], key=key, max_chars=1500, on_change=vital_row_change,
                      args=(sheet["room"], index, "value", key))
        ikey = key + "_include"
        if ikey not in st.session_state:
            st.session_state[ikey] = row["include"]
        st.checkbox("Include " + row["label"], key=ikey, on_change=vital_row_change,
                    args=(sheet["room"], index, "include", ikey))


def load_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_smartphrase.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)



def load_niv_sample() -> None:
    if require_session():
        st.session_state["paste"] = (ROOT / "examples" / "synthetic_nc_smartphrase.txt").read_text(encoding="utf-8")
        st.session_state.pop("import_result", None)


def clear_paste() -> None:
    if require_session():
        st.session_state["paste"] = ""
        st.session_state.pop("import_result", None)


def create_handoff(store: GitHubVault | None = None) -> None:
    if not require_session():
        return
    ss = st.session_state
    room = ss.get("current_room")
    if not room:
        note("Select a room first.", "error")
        return
    ss.pop("last_error_reference", None)
    result = import_sections(ss["drafts"][room], ss.get("paste", ""), ss["vault"]["settings"])
    if result.sheet is not None:
        set_editor(room, result.sheet)
    ss["import_result"] = {"room": room, "errors": result.errors,
                           "notices": result.notices, "imported": result.imported}
    if result.diagnostics:
        record = new_error_event(result.diagnostics)
        ss.setdefault("pending_error_events", {})[record["id"]] = record
        ss["last_error_reference"] = record["id"]
        ss["error_log_saved"] = False
        send_pending_errors(store)


def start_new_patient() -> None:
    if not require_session():
        return
    ss = st.session_state
    room = ss["current_room"]
    ss.setdefault("base_sheets", {})[room] = deepcopy(ss["vault"]["rooms"].get(room))
    set_editor(room, new_sheet(room))
    note("Blank handoff opened. Save to replace this room's saved sheet.")


def load_saved_into_editor() -> None:
    if not require_session():
        return
    ss = st.session_state
    room = ss["current_room"]
    saved = ss["vault"]["rooms"].get(room)
    ss.setdefault("base_sheets", {})[room] = deepcopy(saved)
    set_editor(room, saved if saved else new_sheet(room))
    note("Saved handoff loaded.")


def commit(candidate: dict, store: GitHubVault | None) -> None:
    validate_vault(candidate)
    if store is not None:
        new_sha = store.save(candidate, st.session_state.get("vault_sha"))
        st.session_state["vault_sha"] = new_sha
    st.session_state["vault"] = candidate


def save_rooms(store: GitHubVault | None, rooms: list[str]) -> None:
    if not require_session():
        return
    ss = st.session_state
    if not rooms:
        note("There are no open drafts to save.")
        return
    for room in rooms:
        if ss.get("base_sheets", {}).get(room) != ss["vault"]["rooms"].get(room):
            note("A saved room changed after its draft was opened. Reload that saved handoff and reapply your edits. No rooms were saved.", "error")
            return
    try:
        candidate = deepcopy(ss["vault"])
        for room in rooms:
            candidate = save_sheet_in(candidate, ss["drafts"][room])
        commit(candidate, store)
    except (StorageError, ValidationError) as exc:
        note(str(exc), "error")
        return
    for room in rooms:
        saved = deepcopy(candidate["rooms"][room])
        ss["drafts"][room] = saved
        ss.setdefault("base_sheets", {})[room] = deepcopy(saved)
    message = ("Handoffs saved to encrypted GitHub." if store else
               "Saved in this session only. GitHub is not enabled.")
    stamp = latest_saved_time({room: candidate["rooms"][room] for room in rooms})
    note(message + (" Last saved: " + stamp if stamp else ""), "success" if store else "info")


def save_room(store: GitHubVault | None) -> None:
    room = st.session_state.get("current_room")
    if room:
        save_rooms(store, [room])


def save_all_rooms(store: GitHubVault | None) -> None:
    save_rooms(store, list(st.session_state.get("drafts", {})))


def reapply_open_mappings() -> None:
    ss = st.session_state
    rules = ss["vault"]["settings"]["medication_mappings"]
    for sheet in ss.get("drafts", {}).values():
        sheet["medications"] = apply_group_rules(apply_gi_rules(apply_infusion_rules(remap(sheet["medications"], rules, ss["vault"]["settings"]["medication_visibility"]), ss["vault"]["settings"]["medication_infusions"]), ss["vault"]["settings"]["medication_gi_groups"]), ss["vault"]["settings"]["medication_groups"])
    # These callbacks run before the widgets are instantiated on the next run.
    for key in list(ss):
        if (key.startswith("med_") and key.endswith(("_section", "_infusion_mode", "_gi_mode", "_group_mode"))) or key.startswith(("infusion_rule_mode_", "gi_rule_mode_", "group_rule_mode_")):
            ss.pop(key, None)


def medication_row_change(room: str, row_id: str, field: str, widget_key: str, store: GitHubVault | None = None) -> None:
    if not require_session():
        return
    ss = st.session_state
    if room != ss.get("current_room"):
        return
    rows = ss["drafts"][room]["medications"]
    original = next((r for r in rows if r["id"] == row_id), None)
    if original is None:
        return
    old_value = original.get(field, "auto") if field in ("infusion_mode", "gi_mode", "group_mode") else original[field]
    edited = deepcopy(original)
    edited[field] = ss[widget_key]
    if field == "section":
        old_value = effective_section(original)
    try:
        validate_medication(edited)
        if field == "group_mode":
            candidate = deepcopy(ss["vault"])
            candidate["settings"]["medication_groups"] = set_group_rule(candidate["settings"]["medication_groups"], edited, edited["group_mode"])
            commit(candidate, store)
            reapply_open_mappings()
            note("Medication display group remembered." + (" Saved to encrypted GitHub." if store else " Session-only test mode."), "success")
        elif field == "gi_mode":
            candidate = deepcopy(ss["vault"])
            if edited["gi_mode"] not in ("auto", "other"):
                candidate["settings"]["medication_groups"] = set_group_rule(candidate["settings"]["medication_groups"], edited, "auto")
            candidate["settings"]["medication_gi_groups"] = set_gi_rule(candidate["settings"]["medication_gi_groups"], edited, edited["gi_mode"])
            commit(candidate, store)
            reapply_open_mappings()
            note("FEN/GI display choice remembered." + (" Saved to encrypted GitHub." if store else " Session-only test mode."), "success")
        elif field == "infusion_mode":
            candidate = deepcopy(ss["vault"])
            candidate["settings"]["medication_infusions"] = set_infusion_rule(
                candidate["settings"]["medication_infusions"], edited, edited["infusion_mode"])
            commit(candidate, store)
            reapply_open_mappings()
            note("Infusion display choice remembered for this formulation, route and frequency." +
                 (" Saved to encrypted GitHub." if store else " Session-only test mode."), "success")
        elif field == "section":
            rules = ss["vault"]["settings"]["medication_mappings"]
            name, match = rule_for_inline_mapping(edited["name"], rules)
            new_rules = upsert_rule(rules, name, edited["section"], match)
            candidate = deepcopy(ss["vault"])
            candidate["settings"]["medication_mappings"] = new_rules
            if edited["section"] != "FEN / GI" and group_for(original):
                candidate["settings"]["medication_gi_groups"] = set_gi_rule(candidate["settings"]["medication_gi_groups"], edited, "other")
            group = special_group(original)
            if group and edited["section"] != GROUP_SECTIONS[group]:
                candidate["settings"]["medication_groups"] = set_group_rule(candidate["settings"]["medication_groups"], edited, "other")
            if candidate != ss["vault"]:
                commit(candidate, store)  # Persist the rule, not any draft clinical text.
            reapply_open_mappings()
            ss["admin_rule_index"] = -1
            for key in ("mapping_name", "mapping_destination", "mapping_match", "mapping_original"):
                ss.pop(key, None)
            note("Medication destination remembered in Admin." + (" Saved to encrypted GitHub." if store else " Session-only test mode."), "success")
        else:
            if field in ("name", "route", "frequency"):
                edited["infusion_mode"] = infusion_mode_for(edited, ss["vault"]["settings"]["medication_infusions"])
                edited["gi_mode"] = gi_mode_for(edited, ss["vault"]["settings"]["medication_gi_groups"])
                edited["group_mode"] = group_mode_for(edited, ss["vault"]["settings"]["medication_groups"])
                ss.pop("med_draft_" + row_id + "_group_mode", None)
                ss.pop("med_draft_" + row_id + "_gi_mode", None)
                ss.pop("med_draft_" + row_id + "_section", None)
                ss.pop("med_draft_" + row_id + "_infusion_mode", None)
            if field == "name":
                edited["hidden"] = hidden_for(edited["name"], ss["vault"]["settings"]["medication_visibility"])
            # Dose edits can change heparin grouping without changing its signature.
            if field == "dose":
                ss.pop("med_draft_" + row_id + "_section", None)
            original.update(edited)
    except (ValueError, ValidationError, StorageError) as exc:
        # Do not claim a remembered mapping or move orders after a rejected save.
        ss[widget_key] = old_value
        note(str(exc) + " The change was not saved.", "error")


def ventilation_change(room: str, label: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room") or key not in st.session_state:
        return
    ss = st.session_state
    old = ss["drafts"][room]["ventilation"]
    if old is None:
        return
    updated = deepcopy(old)
    value = ss[key].strip()
    if label == "Vent Mode":
        updated["mode"] = value
    elif value:
        updated["values"][label] = value
    else:
        updated["values"].pop(label, None)
    try:
        validate_ventilation(updated)
    except ValueError as exc:
        ss[key] = old["mode"] if label == "Vent Mode" else old["values"].get(label, "")
        note(str(exc), "error")
        return
    ss["drafts"][room]["ventilation"] = updated


def clear_ventilation() -> None:
    if require_session():
        ss = st.session_state
        ss["drafts"][ss["current_room"]]["ventilation"] = None
        for key in list(ss):
            if key.startswith("vent_"):
                ss.pop(key, None)


def upgrade_existing_session() -> None:
    ss = st.session_state
    vault = ss.get("vault")
    if not vault or vault.get("schema") == SCHEMA_VERSION:
        return
    old_schema, old_settings = vault["schema"], deepcopy(vault["settings"])
    converted = upgrade_vault(vault)
    changes = {}
    for key in ("drafts", "base_sheets"):
        changes[key] = {}
        for room, sheet in ss.get(key, {}).items():
            canonical = normalize_room(room)
            if canonical in changes[key]:
                raise ValidationError("Two open room aliases conflict. Save and resolve them before upgrading.")
            changes[key][canonical] = None if sheet is None else upgrade_vault({"schema": old_schema, "settings": old_settings, "rooms": {room: sheet}})["rooms"][canonical]
    ss.update(vault=converted, **changes)
    for key in ("current_room", "room_choice"):
        if ss.get(key) and ss[key] not in ("Choose a room", "Other room"):
            ss[key] = normalize_room(ss[key])
    for key in ("admin_rooms", "print_rooms", "print_room_options", "removed_room"):
        ss.pop(key, None)
    for key in ("pending", "diagnosis_preview", "medication_pending"):
        ss.pop(key, None)
    discard_editor_widget_values()

def load_config() -> tuple[dict, GitHubVault | None]:
    try:
        config = st.secrets.to_dict()
    except Exception:
        st.error("Deployment secrets have not been configured. Follow START_HERE.html and create_secrets.py. There is no default password.")
        st.stop()
    app = config.get("app", {})
    if not valid_password_hash(app.get("password_hash", "")):
        st.error("Set a valid app.password_hash in deployment secrets. Use create_secrets.py to generate it.")
        st.stop()
    app["idle_minutes"] = max(5, min(120, int(app.get("idle_minutes", 15))))
    store = None
    if app.get("github_enabled", False):
        gh = config.get("github", {})
        key = app.get("encryption_key", "")
        try:
            Fernet(key.encode("ascii"))
            store = GitHubVault(GitHubConfig(token=gh.get("token", ""), repository=gh.get("repository", ""),
                                            branch=gh.get("branch", "main"), api_base=gh.get("api_base", "https://api.github.com"),
                                            api_version=gh.get("api_version", "2022-11-28")), key)
        except (ValueError, StorageError):
            st.error("The GitHub or encryption-key settings are incomplete. Check deployment secrets. No archive was opened.")
            st.stop()
    return app, store


@st.fragment(run_every=30)
def idle_guard(minutes: int) -> None:
    if st.session_state.get("authenticated"):
        now = time.monotonic()
        if now - st.session_state.get("last_activity", now) > minutes * 60 or now - st.session_state.get("login_at", now) > 8 * 3600:
            clear_session()
            st.rerun()



def reload_archive(store: GitHubVault | None) -> None:
    if not require_session() or store is None:
        return
    try:
        fresh, sha = store.load()
        st.session_state.update(vault=fresh, vault_sha=sha)
        note("Saved archive reloaded. Open drafts were kept.")
    except (StorageError, ValidationError) as exc:
        note(str(exc), "error")


def main() -> None:
    app, store = load_config()
    now = time.monotonic()
    if st.session_state.get("authenticated") and (now - st.session_state.get("last_activity", now) > app["idle_minutes"] * 60 or now - st.session_state.get("login_at", now) > 8 * 3600):
        clear_session()
    if not st.session_state.get("authenticated"):
        st.title("PICU Handoff")
        with st.form("login"):
            st.text_input("App password", type="password", key="login_password", max_chars=1024)
            st.form_submit_button("Open app", on_click=authenticate, args=(app["password_hash"],))
        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])
        return
    st.session_state["last_activity"] = now
    st.session_state["idle_seconds"] = app["idle_minutes"] * 60
    idle_guard(app["idle_minutes"])
    if "vault" not in st.session_state:
        try:
            vault, sha = store.load() if store else (new_vault(), None)
        except (StorageError, ValidationError) as exc:
            st.error(str(exc))
            st.button("Try loading again")
            st.button("Log out", on_click=clear_session)
            return
        st.session_state.update(vault=vault, vault_sha=sha, drafts={}, base_sheets={})
    upgrade_existing_session()
    with st.sidebar:
        st.header("PICU Handoff")
        st.caption("Version 6.21 | Unified DVT Prophylaxis group")
        page = st.radio("Workspace", ["Handoff", "Print all", "Admin", "Import errors"], key="page")
        st.caption("Encrypted GitHub storage" if store else "Session-only testing. No persistence.")
        st.button("Reload saved archive", on_click=reload_archive, args=(store,), disabled=store is None)
        st.button("Log out", on_click=clear_session)
        if st.session_state.get("pending_error_events"):
            st.warning("Technical error reports are not saved. Open Import errors to retry before closing this session.")
        st.caption("Room changes automatically save the current handoff. Use Save before logout. Medication mappings save immediately.")
        if not app.get("clinical_use_approved", False):
            st.caption("Use synthetic data unless your hosting and storage have institutional approval. See the setup guide.")
    if "notice" in st.session_state:
        kind, text = st.session_state.pop("notice")
        getattr(st, kind)(text)
    if page == "Admin":
        admin_page(store)
    elif page == "Import errors":
        import_errors_page(store)
    elif page == "Print all":
        print_all_page(store)
    else:
        handoff_page(store)


def medication_editor(rows: list[dict], room: str, store: GitHubVault | None) -> None:
    for number, row in enumerate(rows, 1):
        prefix = "med_draft_" + row["id"] + "_"
        summary, destination = st.columns([3, 1])
        with summary:
            suffix = " [HIDDEN]" if row["hidden"] else "" if row["include"] else " [EXCLUDED]"
            if supports_infusion_display(row) and is_infusion(row):
                st.markdown('<div style="white-space:pre-wrap;border-left:3px solid #555;padding-left:8px">' +
                            str(number) + '. <b>Infusion</b>' + suffix + '\n' +
                            infusion_entry(row, True) + '</div>', unsafe_allow_html=True)
            else:
                st.text(f"{number}. " + format_medication(row) + suffix)
        with destination:
            key = prefix + "section"
            if key not in st.session_state:
                st.session_state[key] = effective_section(row)
            st.selectbox("System for order " + str(number), DESTINATIONS, key=key, format_func=section_label,
                         on_change=medication_row_change, args=(room, row["id"], "section", key, store))
        if effective_section(row) == "FEN / GI" or automatic_group(row):
            key = prefix + "gi_mode"
            if key not in st.session_state:
                st.session_state[key] = row.get("gi_mode", "auto")
            st.selectbox("FEN/GI display for order " + str(number), GI_MODES, key=key,
                         format_func=lambda value: GI_MODE_LABELS[value], on_change=medication_row_change,
                         args=(room, row["id"], "gi_mode", key, store))
        if supports_infusion_display(row):
            key = prefix + "infusion_mode"
            if key not in st.session_state:
                st.session_state[key] = row.get("infusion_mode", "auto")
            st.selectbox(DISPLAY_LABELS[effective_section(row)] + " display for order " + str(number), MODES, key=key,
                         format_func=lambda value: MODE_LABELS[value], on_change=medication_row_change,
                         args=(room, row["id"], "infusion_mode", key, store))
        if effective_section(row) in ("Neurologic", "Hematology") or automatic_special_group(row) or row.get("group_mode", "auto") != "auto":
            key = prefix + "group_mode"
            if key not in st.session_state:
                st.session_state[key] = row.get("group_mode", "auto")
            st.selectbox("Medication group for order " + str(number), GROUP_MODES, key=key,
                         format_func=lambda value: GROUP_MODE_LABELS[value], on_change=medication_row_change,
                         args=(room, row["id"], "group_mode", key, store))
        st.button("Restore to handoff" if row["hidden"] else "Hide from handoff", key="hide_med_" + row["id"], on_click=hide_medication, args=(room, row["id"], not row["hidden"], store))
        with st.expander("Edit details for order " + str(number), expanded=False):
            def widget(field: str, label: str, kind: str = "text"):
                key = prefix + field
                if key not in st.session_state:
                    st.session_state[key] = row[field]
                args = (room, row["id"], field, key, store)
                if kind == "check":
                    st.checkbox(label, key=key, on_change=medication_row_change, args=args)
                elif kind == "area":
                    st.text_area(label, key=key, height=90, max_chars=4000, on_change=medication_row_change, args=args)
                else:
                    st.text_input(label, key=key, max_chars=4000, on_change=medication_row_change, args=args)
            widget("include", "Include order", "check")
            widget("name", "Medication / formulation")
            left, right = st.columns(2)
            with left:
                widget("dose", "Dose")
                widget("frequency", "Frequency")
            with right:
                widget("route", "Route")
                widget("last_rate", "Last recorded rate")
            widget("rate_time", "Rate timestamp")
            widget("custom_text", "Custom handoff wording", "area")
            name, match = rule_for_inline_mapping(row["name"], st.session_state["vault"]["settings"]["medication_mappings"])
            st.caption("Changing the system remembers this rule: " + name + " [" + match + "].")
            for warning in row["warnings"]:
                st.caption(warning)


def invasive_editor(sheet: dict) -> None:
    data = sheet["ventilation"]
    if data is None:
        st.caption("No automatic invasive-ventilation block is currently included.")
        return
    st.text(format_ventilation(data))
    with st.expander("Edit ventilator values"):
        for index, label in enumerate(LABELS):
            key = "vent_" + sheet["id"] + "_" + str(index)
            if key not in st.session_state:
                st.session_state[key] = data["mode"] if index == 0 else data["values"].get(label, "")
            st.text_input(label, key=key, max_chars=500, on_change=ventilation_change,
                          args=(sheet["room"], label, key))
        st.button("Clear ventilator block", on_click=clear_ventilation)



def noninvasive_change(room: str, device: str, label: str, widget_key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    devices = ss["drafts"][room]["noninvasive"]
    updated = deepcopy(devices)
    row = next((d for d in updated if d["device"] == device), None)
    if row is None:
        return
    old_value = row["values"].get(label, "")
    value = ss[widget_key].strip()
    if value:
        row["values"][label] = value
    else:
        row["values"].pop(label, None)
    try:
        validate_noninvasive(updated)
    except ValueError as exc:
        ss[widget_key] = old_value
        note(str(exc), "error")
        return
    ss["drafts"][room]["noninvasive"] = updated


def remove_support_device(room: str, device: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    sheet = ss["drafts"][room]
    sheet["noninvasive"] = [item for item in sheet["noninvasive"] if item["device"] != device]
    for key in list(ss):
        if key.startswith("niv_" + sheet["id"] + "_" + device + "_"):
            ss.pop(key, None)


def ventilation_editor(sheet: dict) -> None:
    if sheet["ventilation"] is not None:
        invasive_editor(sheet)
    if not sheet["ventilation"] and not sheet["noninvasive"]:
        st.caption("No automatic respiratory-support entries are currently included.")
    for device in sheet["noninvasive"]:
        st.text(format_noninvasive([device]))
        if device["pressure_inferred"]:
            st.caption("Pressure-based BiPAP: Vent Mode was absent, but both IPAP and EPAP were documented. These may be carried-forward settings rather than current support. Remove the entry below if it no longer applies.")
        if device["flow_inferred"]:
            st.caption("Flow-based HFNC: the source delivery label is a CPAP/Bi-PAP mask. Your mask-plus-flow rule adds this entry, but it does not confirm concurrent HFNC. Remove it below when it does not apply.")
        with st.expander("Edit " + device["device"] + " settings"):
            for index, label in enumerate(DEVICE_FIELDS[device["device"]]):
                key = "niv_" + sheet["id"] + "_" + device["device"] + "_" + str(index)
                if key not in st.session_state:
                    st.session_state[key] = device["values"].get(label, "")
                st.text_input(label, key=key, max_chars=500, on_change=noninvasive_change,
                              args=(sheet["room"], device["device"], label, key))
            st.button("Remove " + device["device"], key="remove_niv_" + sheet["id"] + "_" + device["device"],
                      on_click=remove_support_device, args=(sheet["room"], device["device"]))

def display_room_save_status(room: str, store: GitHubVault | None):
    """Read confirmed save metadata, independent of display or print timestamps."""
    ss = st.session_state
    kwargs = {"session_only": store is None}
    if room in ss.get("base_sheets", {}):
        kwargs["base_sheet"] = ss["base_sheets"][room]
    return room_save_status(room, ss["vault"]["rooms"].get(room),
                            ss.get("drafts", {}).get(room), **kwargs)


def render_room_save_table(rooms: list[str], store: GitHubVault | None) -> None:
    statuses = [display_room_save_status(room, store) for room in rooms]
    st.markdown(save_status_table(statuses, session_only=store is None), unsafe_allow_html=True)


def handoff_page(store: GitHubVault | None) -> None:
    st.title("Room handoff")
    ss = st.session_state
    settings = ss["vault"]["settings"]
    choices = list(dict.fromkeys(settings["rooms"] + list(ss["vault"]["rooms"]) + list(ss.get("drafts", {}))))
    if "room_choice" not in ss:
        ss["room_choice"] = ss.get("current_room", "Choose a room")
    st.selectbox("Room", ["Choose a room"] + choices + ["Other room"], key="room_choice", on_change=room_changed, args=(store,))
    with st.expander("Save status for all rooms", expanded=False):
        render_room_save_table(choices, store)
        st.caption("Times are Eastern (EST/EDT). Reload saved archive to see saves made in another session." if store else
                   "Session-only testing: these times do not indicate a save to GitHub.")
    if ss.get("removed_room"):
        st.button("Undo last room removal", key="undo_room_handoff", on_click=undo_room_removal, args=(store,))
    if ss.get("room_choice") == "Other room":
        st.text_input("Other room number", key="other_room", max_chars=16)
        st.button("Open room", on_click=open_room, args=(store,))
        st.info("Enter the other room number and click Open room.")
        return
    if ss.get("room_choice") == "Choose a room":
        st.info("Select a room to begin.")
        return
    room = ss.get("current_room")
    if not room:
        st.info("Select a room to begin.")
        return
    sheet = ss["drafts"][room]
    st.subheader("Room " + room)
    status = display_room_save_status(room, store)
    st.caption(status.caption)
    st.caption(status.status + (". Changes save automatically when you change rooms." if status.unsaved else ""))
    import_review_editor(sheet)
    if room not in DEFAULT_ROOMS:
        with st.expander("Custom room options"):
            st.caption("Remove this custom room and its current saved handoff. Undo is available during this session. Medication rules are unchanged.")
            st.button("Remove custom room", key="remove_current_room", on_click=remove_custom_room, args=(room, store))
    saved = ss["vault"]["rooms"].get(room)
    if ss.get("base_sheets", {}).get(room) != saved:
        st.warning("A newer saved handoff exists for this room. Reload it before saving your edits.")
    top1, top2 = st.columns(2)
    top1.button("Save handoff", on_click=save_room, args=(store,), type="primary")
    top2.caption("Use Print all in the sidebar for the complete packet.")
    with st.expander("Start over / reload"):
        st.button("Start blank for new patient", on_click=start_new_patient)
        st.button("Load saved handoff", on_click=load_saved_into_editor)
        st.caption("These actions replace the open draft immediately. Saving replaces the room's current saved sheet.")
    paste_tab, meds_tab, labs_tab, cultures_tab, orders_tab, edit_tab, preview_tab = st.tabs(["Paste / create", "Medications", "Labs / Vitals", "Cultures", "Labs/Imaging", "Edit handoff", "Preview / print"])
    with paste_tab:
        st.caption("Paste your SmartPhrase and click Create / update handoff. Imported results and edits save automatically before you change rooms.")
        st.button("Clear pasted text", on_click=clear_paste)
        with st.form("parse_smartphrase"):
            st.text_area("SmartPhrase text", key="paste", height=240, max_chars=MAX_PASTE)
            st.form_submit_button("Create / update handoff", on_click=create_handoff, args=(store,), type="primary")
        result = ss.get("import_result", {})
        if result.get("room") == room:
            for error in result["errors"]:
                st.warning(error)
            if result["errors"] and result["imported"]:
                st.caption("Other sections were imported. Skipped sections are listed in the review warning above.")
            if ss.get("last_error_reference"):
                st.caption("Technical error reference: " + ss["last_error_reference"][:12] + ". See Import errors.")
            if ss.get("error_log_notice"):
                st.warning(ss["error_log_notice"])
            if result["imported"]:
                st.caption("Updated: " + ", ".join(result["imported"]) + ". Edit below or save the handoff.")
            for message in result["notices"]:
                st.info(message)
        st.subheader("Respiratory support to RESP")
        ventilation_editor(sheet)
    with meds_tab:
        st.caption("Choose a system beside an order. It is remembered immediately in Admin and reused on future imports. The named GI/bowel medications group automatically in FEN/GI. Other unmapped orders remain in Other Medications.")
        if sheet["medications"]:
            active = [row for row in sheet["medications"] if not row["hidden"]]
            hidden = [row for row in sheet["medications"] if row["hidden"]]
            medication_editor(active, room, store)
            with st.expander("Hidden medications (" + str(len(hidden)) + ")", expanded=False):
                st.caption("These entries are retained but omitted from every printed/exported handoff. Restore here or change the rule in Admin. Exact-formulation hiding does not suppress other orders for the same drug.")
                medication_editor(hidden, room, store)
        else:
            st.info("Paste a B block and create the handoff to add medications.")
    with labs_tab:
        labs_vitals_editor(sheet)
    with cultures_tab:
        cultures_editor(sheet)
    with orders_tab:
        recurring_orders_editor(sheet)
    with edit_tab:
        st.caption("These are your separate notes. Re-pasting medications or ventilation does not erase them.")
        for section in SYSTEMS:
            key = edit_key(sheet, section)
            if key not in ss:
                ss[key] = sheet["fields"][section]
            with st.expander(section_label(section), expanded=section == "Diagnoses"):
                if section == "FEN / GI":
                    intake_output_editor(sheet)
                if section == "Labs" and orders_text(sheet["recurring_orders"]):
                    st.text(orders_text(sheet["recurring_orders"]) + "\n-----")
                    st.caption("Edit the imported recurring orders in Labs/Imaging. Notes below stay separate.")
                if section in automatic_vitals(sheet):
                    st.text(automatic_vitals(sheet)[section] + "\n-----")
                if section == "Demographics / Weight" and sheet["admission_date"]:
                    st.text("Admission: " + sheet["admission_date"])
                if section == "Infectious Disease" and id_labs_text(sheet["labs"]):
                    st.text(id_labs_text(sheet["labs"]) + "\n------")
                if section == "Cardiovascular" and lactate_text(sheet["labs"]):
                    st.text(lactate_text(sheet["labs"]) + "\n-----")
                if section == "Respiratory" and respiratory_text(sheet):
                    st.text(respiratory_text(sheet) + "\n-----")
                    st.caption("Vital signs print first, then support settings. Edit support under Paste / create.")
                if section == "Respiratory" and theophylline_text(sheet["labs"]):
                    st.text(theophylline_text(sheet["labs"]) + "\n-----")
                    st.caption("Latest included THEOPH result. Edit or exclude its original row in Labs / Vitals.")
                if section == "Diagnoses" and viral_text(sheet["viral_panel"]):
                    st.markdown('<div style="white-space:pre-wrap">----\n' + viral_markup(sheet["viral_panel"]) + '</div>', unsafe_allow_html=True)
                    st.caption("Positive O-block results print below the demographics / weight information. Edit under Labs / Vitals.")
                st.text_area("Notes: " + section_label(section), key=key, height=100, max_chars=MAX_FIELD,
                             on_change=update_field, args=(room, section, key))
                if section == "Infectious Disease" and cultures_text(sheet["cultures"]):
                    st.markdown('<div style="white-space:pre-wrap">------\n' + culture_markup(sheet["cultures"]) + '</div>', unsafe_allow_html=True)
                    st.caption("Edit imported specimens and results in Cultures. Temperature stays first in the printed ID column.")
                if section == "FEN / GI":
                    st.markdown('<div style="white-space:pre-wrap">' + fen_gi_body("", sheet["medications"], None, True) + "</div>", unsafe_allow_html=True)
                    st.caption("Printed order: Intake/Output/Net, GI prophylaxis, Bowel Regimen, Diuretics, then separate notes and remaining FEN/GI medications.")
                elif section in INFUSION_SECTIONS:
                    render_body = {"Neurologic": neuro_body, "Cardiovascular": cardiovascular_body, "Hematology": hematology_body, "Respiratory": respiratory_body}[section]
                    st.markdown('<div style="white-space:pre-wrap">' + render_body("", sheet["medications"], True) + '</div>', unsafe_allow_html=True)
                else:
                    for row in sheet["medications"]:
                        if visible(row) and effective_section(row) == section:
                            st.text(format_medication(row))
                if section == "Diagnoses" and demographic_weight_text(sheet["nutrition"], sheet["dosing_weight"]):
                    st.text("----\n" + demographic_weight_text(sheet["nutrition"], sheet["dosing_weight"]))
                    st.caption("Edit measured weight, Z-score, dosing weight and admission date in Labs / Vitals.")
    with preview_tab:
        import streamlit.components.v1 as components
        st.caption("Compact landscape. The upper-left stamp uses Eastern time. PDFs are stamped when downloaded. Printable HTML refreshes its stamp when printed.")
        components.html(handoff_html(sheet), height=650, scrolling=True)
        try:
            layout = print_layout_info(sheet)
            st.caption(("Fits on one PDF page" if layout["fits_one_page"] else "Needs continuation pages to keep all content") + " | Body text: " + str(layout["font_size"]) + " pt. HTML pagination can differ.")
            st.download_button("Download this handoff (PDF)", download_payload([sheet], "pdf", download_deadline()), "handoff.pdf", "application/pdf", key="download_single_pdf", on_click="ignore")
        except (ValueError, ImportError):
            st.error("PDF export could not be created. Confirm requirements.txt is installed or use HTML.")
        st.download_button("Download printable handoff (HTML)", download_payload([sheet], "html", download_deadline()), "handoff.html", "text/html", key="download_single_html", on_click="ignore")
        st.download_button("Download handoff text", download_payload([sheet], "text", download_deadline()), "handoff.txt", "text/plain", key="download_single_text", on_click="ignore")



def download_deadline() -> float:
    ss = st.session_state
    return min(ss.get("last_activity", time.monotonic()) + ss.get("idle_seconds", 900),
               ss.get("login_at", time.monotonic()) + 8 * 3600)


def print_all_page(store: GitHubVault | None) -> None:
    st.title("Print all handoffs")
    ss = st.session_state
    ready = available_handoffs(ss["vault"], ss.get("drafts", {}))
    if not ready:
        st.info("Create a handoff first. Saved handoffs will also appear here after sign-in.")
        return
    st.caption("Includes saved rooms and the latest open drafts. Printing does not save changes. Blank sheets are omitted.")
    st.button("Save all open handoffs", on_click=save_all_rooms, args=(store,))
    st.caption(most_recent_save_caption(ss["vault"]["rooms"], session_only=store is None))
    options = list(ready)
    # A fresh room list selects all rooms. Explicit selections survive normal reruns.
    if ss.get("print_room_options") != options or "print_rooms" not in ss:
        ss["print_room_options"] = options
        ss["print_rooms"] = options
    selected = st.multiselect("Rooms to print", options, key="print_rooms")
    selected_sheets = [ready[r] for r in options if r in selected]
    if not selected_sheets:
        st.info("Select at least one room.")
        return
    unsaved = sum(sheet != ss["vault"]["rooms"].get(sheet["room"]) for sheet in selected_sheets)
    st.caption(str(len(selected_sheets)) + " handoffs selected. " + str(unsaved) + " include unsaved draft changes. Each room starts on a new page.")
    render_room_save_table([sheet["room"] for sheet in selected_sheets], store)
    st.caption("Save times are Eastern (EST/EDT) and come from the loaded archive. Reload saved archive to see saves from another session." if store else
               "Session-only testing: these save times are not durable GitHub saves.")
    if unsaved:
        st.warning("Some selected handoffs have unsaved changes. Save all open handoffs before printing to store them. Downloading alone does not save.")
    try:
        st.download_button("Download all selected handoffs (PDF)", download_payload(selected_sheets, "pdf", download_deadline()), "all_handoffs.pdf", "application/pdf", type="primary", key="download_all_pdf", on_click="ignore")
    except (ValueError, ImportError):
        st.error("The combined PDF could not be created. Use HTML or check the export requirements.")
    st.download_button("Download all selected handoffs (printable HTML)", download_payload(selected_sheets, "html", download_deadline()), "all_handoffs.html", "text/html", key="download_all_html", on_click="ignore")
    st.caption("Compact PDF is preferred for printing. Each room starts on its own page. Exceptionally long handoffs continue rather than losing content. Downloads are not encrypted.")


def select_admin_rule() -> None:
    if not require_session():
        return
    ss = st.session_state
    index = ss.get("admin_rule_index", -1)
    rules = ss["vault"]["settings"]["medication_mappings"]
    rule = rules[index] if isinstance(index, int) and 0 <= index < len(rules) else None
    ss["mapping_name"] = rule["name"] if rule else ""
    ss["mapping_destination"] = rule["destination"] if rule else "Other Medications"
    ss["mapping_match"] = rule["match"] if rule else "prefix"
    ss["mapping_original"] = (rule["name"], rule["match"]) if rule else None


def save_admin_rule(store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    candidate = deepcopy(ss["vault"])
    rules = candidate["settings"]["medication_mappings"]
    original = ss.get("mapping_original")
    if original:
        rules = [r for r in rules if (r["name"], r["match"]) != tuple(original)]
    try:
        candidate["settings"]["medication_mappings"] = upsert_rule(rules, ss.get("mapping_name", ""), ss.get("mapping_destination", "Other Medications"), ss.get("mapping_match", "prefix"))
        commit(candidate, store)
        reapply_open_mappings()
        ss["admin_rule_index"] = -1
        ss["mapping_original"] = None
        note("Medication mapping saved. Open drafts use the updated mappings.", "success")
    except (ValueError, ValidationError, StorageError) as exc:
        note(str(exc), "error")


def remove_admin_rule(store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    index = ss.get("admin_rule_index", -1)
    rules = ss["vault"]["settings"]["medication_mappings"]
    if not isinstance(index, int) or not 0 <= index < len(rules):
        return
    candidate = deepcopy(ss["vault"])
    candidate["settings"]["medication_mappings"].pop(index)
    try:
        commit(candidate, store)
        reapply_open_mappings()
        ss["admin_rule_index"] = -1
        select_admin_rule()
        note("Mapping removed. Open drafts have been remapped.")
    except (StorageError, ValidationError) as exc:
        note(str(exc), "error")


def save_admin_settings(store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    try:
        rooms = list(dict.fromkeys(normalize_room(line) for line in ss.get("admin_rooms", "").splitlines() if line.strip()))
        candidate = deepcopy(ss["vault"])
        candidate["settings"].update(diagnoses_destination=ss["admin_diagnosis_dest"], rooms=rooms)
        commit(candidate, store)
        ss["admin_rooms"] = "\n".join(rooms)
        note("Room and diagnosis settings saved.", "success")
    except (ValidationError, StorageError) as exc:
        note(str(exc), "error")


def custom_room_names() -> list[str]:
    ss = st.session_state
    return [r for r in dict.fromkeys(ss["vault"]["settings"]["rooms"] +
            list(ss["vault"]["rooms"]) + list(ss.get("drafts", {}))) if r not in DEFAULT_ROOMS]


def remove_custom_room(room: str, store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    try:
        room = normalize_room(room)
        if room in DEFAULT_ROOMS:
            raise ValidationError("This control removes custom rooms only. Preset rooms are kept.")
        if room not in custom_room_names():
            raise ValidationError("The custom room is no longer present.")
        if room in ss.get("drafts", {}) and ss.get("base_sheets", {}).get(room) != ss["vault"]["rooms"].get(room):
            raise ValidationError("A newer saved sheet exists for this room. Reload and compare before removing it.")
        draft = (editor_snapshot(room) if room == ss.get("current_room") else
                 deepcopy(ss.get("drafts", {}).get(room)))
        removed = {"room": room, "saved": deepcopy(ss["vault"]["rooms"].get(room)),
                   "draft": draft, "base": deepcopy(ss.get("base_sheets", {}).get(room)),
                   "listed": room in ss["vault"]["settings"]["rooms"]}
        candidate = deepcopy(ss["vault"])
        candidate["rooms"].pop(room, None)
        candidate["settings"]["rooms"] = [r for r in candidate["settings"]["rooms"] if r != room] or list(DEFAULT_ROOMS)
        commit(candidate, store)
    except (StorageError, ValueError, KeyError, TypeError) as exc:
        note("The room was not removed. " + str(exc), "error")
        return
    except Exception:
        note("Room removal was not confirmed. Keep your draft and reload the saved archive before retrying.", "error")
        return
    ss["removed_room"] = removed
    ss.get("drafts", {}).pop(room, None)
    ss.get("base_sheets", {}).pop(room, None)
    ss["admin_rooms"] = "\n".join(candidate["settings"]["rooms"])
    for key in ("print_rooms", "print_room_options", "custom_room_remove_choice"):
        ss.pop(key, None)
    if ss.get("current_room") == room:
        discard_editor_widget_values()
        ss.pop("current_room", None)
        ss["room_choice"] = "Choose a room"
        ss["paste"] = ""
        ss.pop("import_result", None)
    note("Custom room and current saved handoff removed. Undo is available during this session. Earlier encrypted Git history is not erased.", "success")


def undo_room_removal(store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    removed = ss.get("removed_room")
    if not removed:
        return
    room = removed["room"]
    if room in custom_room_names():
        note("That room has been added again. Undo will not overwrite it.", "error")
        return
    candidate = deepcopy(ss["vault"])
    if removed["listed"] or removed["saved"] is None:
        candidate["settings"]["rooms"].append(room)
    if removed["saved"] is not None:
        candidate["rooms"][room] = deepcopy(removed["saved"])
    try:
        commit(candidate, store)
    except (ValueError, StorageError) as exc:
        note("Undo was not saved. " + str(exc), "error")
        return
    if removed["draft"] is not None:
        ss.setdefault("drafts", {})[room] = deepcopy(removed["draft"])
        ss.setdefault("base_sheets", {})[room] = deepcopy(removed["base"])
    ss.pop("removed_room", None)
    ss["admin_rooms"] = "\n".join(candidate["settings"]["rooms"])
    for key in ("print_rooms", "print_room_options", "custom_room_remove_choice"):
        ss.pop(key, None)
    note("Room restored. Any prior unsaved draft is retained separately from its saved handoff.", "success")


def remove_selected_custom_room(store: GitHubVault | None) -> None:
    room = st.session_state.get("custom_room_remove_choice")
    if room:
        remove_custom_room(room, store)


def custom_room_admin(store: GitHubVault | None) -> None:
    st.subheader("Custom rooms")
    names = custom_room_names()
    if names:
        if st.session_state.get("custom_room_remove_choice") not in names:
            st.session_state["custom_room_remove_choice"] = names[0]
        st.selectbox("Custom room to remove", names, key="custom_room_remove_choice")
        st.caption("Removes the room and its current saved handoff, not medication rules. Preset rooms are not listed here.")
        st.button("Remove selected custom room", on_click=remove_selected_custom_room, args=(store,))
    else:
        st.caption("No custom rooms to remove.")
    if st.session_state.get("removed_room"):
        st.button("Undo last room removal", key="undo_room_admin", on_click=undo_room_removal, args=(store,))


def reset_infusion_rule(key: tuple[str, str, str], store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    candidate = deepcopy(ss["vault"])
    candidate["settings"]["medication_infusions"] = [r for r in candidate["settings"]["medication_infusions"]
        if (r["name"], r["route"], r["frequency"]) != key]
    try:
        commit(candidate, store)
        reapply_open_mappings()
        note("Infusion display restored to Automatic. System assignments are unchanged.", "success")
    except (ValueError, StorageError) as exc:
        note(str(exc), "error")


def edit_saved_infusion_rule(key: tuple[str, str, str], widget: str, store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    rules = ss["vault"]["settings"]["medication_infusions"]
    existing = next((r for r in rules if (r["name"], r["route"], r["frequency"]) == key), None)
    if existing is None:
        note("The selected infusion rule changed. Reload Admin before editing it.", "error")
        return
    candidate = deepcopy(ss["vault"])
    try:
        row = dict(zip(("name", "route", "frequency"), key))
        candidate["settings"]["medication_infusions"] = set_infusion_rule(rules, row, ss[widget])
        commit(candidate, store)
        reapply_open_mappings()
        for k in list(ss):
            if k.startswith("infusion_rule_mode_"):
                ss.pop(k, None)
        note("Infusion display rule updated. System assignments are unchanged.", "success")
    except (ValueError, StorageError) as exc:
        ss[widget] = existing["mode"]
        note(str(exc), "error")


def infusion_admin(store: GitHubVault | None) -> None:
    with st.expander("Infusion display choices"):
        st.caption("Automatic recognizes continuous parenteral orders and continuous nebulized/inhaled orders mapped to Respiratory, not PRN boluses. Overrides remember the exact formulation, route and frequency. No dose is copied to another order. Display grouping applies in Neurologic, Cardiovascular, Respiratory and Hematology. DVT infusion labels are retained. Named PRN and fever-control groups remain separate.")
        for index, rule in enumerate(st.session_state["vault"]["settings"]["medication_infusions"]):
            st.text(rule["name"] + " | " + rule["route"] + " | " + rule["frequency"] + " -> " + MODE_LABELS[rule["mode"]])
            key = "infusion_rule_mode_" + str(index)
            if key not in st.session_state:
                st.session_state[key] = rule["mode"]
            st.selectbox("Display choice " + str(index + 1), MODES, key=key,
                         format_func=lambda v: MODE_LABELS[v], on_change=edit_saved_infusion_rule,
                         args=((rule["name"], rule["route"], rule["frequency"]), key, store))


def admin_page(store: GitHubVault | None) -> None:
    st.title("Admin")
    ss = st.session_state
    settings = ss["vault"]["settings"]
    rules = settings["medication_mappings"]
    st.caption("Medication destinations chosen in a handoff appear here automatically. Edit these rules at any time, even with no handoff open.")
    st.subheader("Medication mappings")
    choices = [-1] + list(range(len(rules)))
    if ss.get("admin_rule_index", -1) not in choices:
        ss["admin_rule_index"] = -1
    st.selectbox("Edit a rule or add one", choices, key="admin_rule_index", on_change=select_admin_rule,
                 format_func=lambda i: "Add a new rule" if i == -1 else rules[i]["name"] + " -> " + rules[i]["destination"])
    if "mapping_name" not in ss:
        select_admin_rule()
    with st.form("medication_mapping"):
        st.text_input("Medication name / prefix", key="mapping_name", max_chars=250)
        st.selectbox("System", DESTINATIONS, key="mapping_destination", format_func=section_label)
        st.selectbox("Match", ["prefix", "exact"], key="mapping_match", format_func=lambda value: "Name starts with this text" if value == "prefix" else "Exact complete name")
        st.form_submit_button("Save mapping", on_click=save_admin_rule, args=(store,))
    if ss.get("admin_rule_index", -1) != -1:
        st.button("Delete selected mapping", on_click=remove_admin_rule, args=(store,))
    if rules:
        with st.expander("All saved mappings", expanded=True):
            for rule in rules:
                st.text(rule["name"] + " [" + rule["match"] + "] -> " + rule["destination"])
    else:
        st.info("No saved mappings yet. Unmapped medications go to Other Medications.")
    visibility_admin(store)
    infusion_admin(store)
    gi_admin(store)
    group_admin(store)
    custom_room_admin(store)
    st.subheader("Room and diagnosis settings")
    if "admin_rooms" not in ss:
        ss["admin_rooms"] = "\n".join(settings["rooms"])
    if "admin_diagnosis_dest" not in ss:
        ss["admin_diagnosis_dest"] = settings["diagnoses_destination"]
    with st.form("admin_settings"):
        st.selectbox("Diagnosis destination", SYSTEMS, key="admin_diagnosis_dest", format_func=section_label)
        st.text_area("Rooms, one per line", key="admin_rooms", height=150)
        st.form_submit_button("Save settings", on_click=save_admin_settings, args=(store,))
    with st.expander("Section imports"):
        for key, heading in SECTION_NAMES.items():
            st.text(key * 8 + " = " + heading + (" | automatic import" if key in SUPPORTED_SECTIONS else " | not imported yet"))
        st.caption("C/D rules control the display, not bedside device status. BiPAP needs both D-block pressures. CPAP needs EPAP or PEEP. Explicit HFNC or the documented mask-plus-flow convention can add HFNC. Inferred HFNC is labeled flow-based. No previous-paste values are reused.")



def order_widget_value(field: str, value):
    if field == "occurrences":
        value = str(value).strip()
        if not value:
            return None
        if not value.isascii() or not value.isdigit():
            raise ValueError("Enter a whole-number occurrence count, or leave it blank when not supplied.")
        return int(value)
    return value.strip() if isinstance(value, str) else value


def recurring_order_change(room: str, row_id: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    ss = st.session_state
    current = ss["drafts"][room]["recurring_orders"]
    if current is None:
        return
    candidate = deepcopy(current)
    row = next((r for r in candidate["rows"] if r["id"] == row_id), None)
    if row is None or field not in ("name", "timing", "occurrences", "include"):
        return
    old = row[field]
    try:
        row[field] = order_widget_value(field, ss[key])
        validate_orders(candidate)
    except ValueError as exc:
        ss[key] = ("" if old is None else str(old)) if field == "occurrences" else old
        note(str(exc) + " The order was not changed.", "error")
        return
    ss["drafts"][room]["recurring_orders"] = candidate


def recurring_orders_editor(sheet: dict) -> None:
    st.subheader("Labs/Imaging")
    st.caption("R-section scheduled orders only. Counts are the Number of Occurrences in the paste, not a calculation of remaining draws.")
    data = sheet["recurring_orders"]
    if "r" in sheet["import_warnings"]:
        st.warning("The R section was skipped. Any list below is the previous snapshot for review only and is hidden from the printed handoff.")
    if data is None:
        st.info("Paste the R section and click Create / update handoff to add recurring lab and chest X-ray orders.")
        return
    chosen = selected_orders(data)
    if chosen:
        st.text(orders_text(data))
    else:
        st.caption("No included recurring orders match the selected tests. One-time and STAT orders are omitted.")
    st.caption("Matching test and schedule: highest occurrence count wins. Different schedules, specimens and panels remain separate. Older CBC and gas result displays are unchanged.")
    if not data["rows"]:
        return
    selected_ids = {row["id"] for row in chosen}
    with st.expander("Edit recurring orders / review duplicates", expanded=False):
        for index, row in enumerate(data["rows"], 1):
            status = "shown" if row["id"] in selected_ids else "excluded" if not row["include"] else "duplicate not shown"
            st.text(str(index) + ". " + order_line(row) + " [" + status + "]")
            with st.expander("Order " + str(index) + " details", expanded=False):
                for field, label in (("include", "Include order"), ("name", "Order name"),
                                     ("timing", "Timing, for example Recurring (Daily)"),
                                     ("occurrences", "Number of occurrences")):
                    key = "rorder_" + row["id"] + "_" + field
                    if key not in st.session_state:
                        st.session_state[key] = ("" if row[field] is None else str(row[field])) if field == "occurrences" else row[field]
                    kwargs = dict(key=key, on_change=recurring_order_change, args=(sheet["room"], row["id"], field, key))
                    if field == "include":
                        st.checkbox(label, **kwargs)
                    else:
                        st.text_input(label, max_chars=500 if field != "occurrences" else 8, **kwargs)



def intake_output_change(room: str, field: str, key: str) -> None:
    if not require_session() or room != st.session_state.get("current_room") or key not in st.session_state:
        return
    ss = st.session_state
    original = ss["drafts"][room]["intake_output"]
    if original is None or field not in IO_FIELDS + IO_META_FIELDS + ("include",):
        return
    candidate = deepcopy(original)
    candidate[field] = ss[key].strip() if isinstance(ss[key], str) else ss[key]
    try:
        validate_balance(candidate)
        ss["drafts"][room]["intake_output"] = candidate
    except ValueError as exc:
        ss[key] = original[field]
        note(str(exc), "error")


def intake_output_editor(sheet: dict) -> None:
    st.subheader("Intake / Output / Net")
    data = sheet["intake_output"]
    if data is None:
        st.caption("Paste the paired S section to place its totals at the top of FEN/GI.")
        return
    meta = " | ".join(x for x in (data["period"], "As of " + data["as_of"] if data["as_of"] else "", "Last filed " + data["last_filed"] if data["last_filed"] else "") if x)
    if meta:
        st.caption(meta)
    for field in IO_FIELDS:
        key = "io_" + sheet["id"] + "_" + field
        if key not in st.session_state:
            st.session_state[key] = data[field]
        st.text_input(field.capitalize(), key=key, max_chars=120, on_change=intake_output_change, args=(sheet["room"], field, key))
    key = "io_" + sheet["id"] + "_include"
    if key not in st.session_state:
        st.session_state[key] = data["include"]
    st.checkbox("Show intake/output totals", key=key, on_change=intake_output_change, args=(sheet["room"], "include", key))
    st.caption("Values are copied from S. Missing values are not zero. Net is not recalculated.")


def update_gi_admin(rule_key: tuple, key: str, store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    old = next((r for r in ss["vault"]["settings"]["medication_gi_groups"] if (r["name"], r["route"], r["frequency"]) == rule_key), None)
    if old is None or key not in ss:
        return
    try:
        candidate = deepcopy(ss["vault"])
        row = dict(zip(("name", "route", "frequency"), rule_key))
        candidate["settings"]["medication_gi_groups"] = set_gi_rule(candidate["settings"]["medication_gi_groups"], row, ss[key])
        if ss[key] not in ("auto", "other"):
            candidate["settings"]["medication_groups"] = set_group_rule(candidate["settings"]["medication_groups"], row, "auto")
        commit(candidate, store)
        reapply_open_mappings()
        note("FEN/GI display choice saved.", "success")
    except (ValueError, StorageError) as exc:
        ss[key] = old["mode"]
        note(str(exc), "error")


def gi_admin(store: GitHubVault | None) -> None:
    with st.expander("FEN/GI display choices", expanded=False):
        st.caption("Automatic GI prophylaxis: famotidine, omeprazole, pantoprazole. Automatic Bowel Regimen: docusate, lactulose, polyethylene glycol, glycerin suppositories, sennosides. Diuretics: bumetanide, chlorothiazide, furosemide. These are display groups, not inferred indications.")
        st.caption("To override a default, use a medication's FEN/GI display control. Choosing another system turns off its automatic GI grouping. The original order and hidden-medication choice stay intact.")
        rules = st.session_state["vault"]["settings"]["medication_gi_groups"]
        for index, rule in enumerate(rules):
            st.text(rule["name"] + " | " + rule["route"] + " | " + rule["frequency"])
            key = "gi_rule_mode_" + str(index)
            if key not in st.session_state:
                st.session_state[key] = rule["mode"]
            st.selectbox("GI display choice " + str(index + 1), GI_MODES, key=key, format_func=lambda value: GI_MODE_LABELS[value], on_change=update_gi_admin, args=((rule["name"], rule["route"], rule["frequency"]), key, store))
        if not rules:
            st.caption("No overrides saved. The automatic defaults apply.")



def update_group_admin(rule_key: tuple, key: str, store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    old = next((r for r in ss["vault"]["settings"]["medication_groups"] if (r["name"], r["route"], r["frequency"]) == rule_key), None)
    if old is None or key not in ss:
        return
    try:
        candidate = deepcopy(ss["vault"])
        row = dict(zip(("name", "route", "frequency"), rule_key))
        candidate["settings"]["medication_groups"] = set_group_rule(candidate["settings"]["medication_groups"], row, ss[key])
        commit(candidate, store)
        reapply_open_mappings()
        note("Medication display group saved.", "success")
    except (ValueError, StorageError) as exc:
        ss[key] = old["mode"]
        note(str(exc), "error")


def group_admin(store: GitHubVault | None) -> None:
    with st.expander("Medication subgroup choices", expanded=False):
        st.caption("DVT Prophylaxis: enoxaparin, cangrelor and heparin with an explicit Units/kg/hr Dose. Fever Control: acetaminophen and ibuprofen. PRN: the requested sedative PRNs. Paralytic PRN: rocuronium, cisatracurium and vecuronium PRNs.")
        st.caption("These are user-defined display labels, not inferred indications or a determination that a dose is prophylactic. Original orders and hidden-medication choices are preserved. Overrides use the formulation, route and frequency.")
        rules = st.session_state["vault"]["settings"]["medication_groups"]
        for index, rule in enumerate(rules):
            st.text(rule["name"] + " | " + rule["route"] + " | " + rule["frequency"])
            key = "group_rule_mode_" + str(index)
            if key not in st.session_state:
                st.session_state[key] = rule["mode"]
            st.selectbox("Medication group choice " + str(index + 1), GROUP_MODES, key=key,
                         format_func=lambda value: GROUP_MODE_LABELS[value], on_change=update_group_admin,
                         args=((rule["name"], rule["route"], rule["frequency"]), key, store))
        if not rules:
            st.caption("No overrides saved. The automatic defaults apply.")


def acknowledge_import_warning(room: str, section: str) -> None:
    if not require_session() or room != st.session_state.get("current_room"):
        return
    sheet = st.session_state["drafts"][room]
    sheet["import_warnings"].pop(section, None)
    note("Review acknowledged. No clinical value was changed. The reviewed handoff will save when you change rooms.")


def import_review_editor(sheet: dict) -> None:
    summary = review_summary(sheet)
    if not summary:
        return
    st.warning(summary)
    with st.expander("Review skipped or incomplete imports", expanded=False):
        st.caption("Valid sections were updated. An unreadable section keeps its previous values with this warning. Failed R orders are retained only for review and are hidden from print. Do not treat skipped values as refreshed.")
        for section, items in sheet["import_warnings"].items():
            for item in items:
                st.text(diagnostic_text(item))
            label = ("Use retained orders after checking Epic" if section == 'r' else
                     "Acknowledge reviewed omissions" if any(i['action'].endswith('omitted') for i in items) else
                     "Accept retained values after checking Epic")
            st.button(label + " (" + REVIEW_SECTIONS[section] + ")", key="accept_import_" + sheet["id"] + "_" + section,
                      on_click=acknowledge_import_warning, args=(sheet["room"], section))


def send_pending_errors(store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    pending = ss.setdefault("pending_error_events", {})
    if not pending:
        ss.pop("error_log_notice", None)
        return
    if store is None:
        ss["error_log_notice"] = "Technical errors are session-only. GitHub storage is not enabled."
        return
    try:
        journal = ErrorJournal(store)
        for ident, record in list(pending.items()):
            sha = journal.save_new(record)
            ss.setdefault("saved_error_events", {})[ident] = {"record": record, "sha": sha}
            pending.pop(ident, None)
        ss.pop("error_log_notice", None)
        ss["error_log_saved"] = True
    except Exception:
        # Logging failure must not discard a clinical draft or leak raw details.
        ss["error_log_notice"] = "The shared error log was not saved. Your imported handoff is still available. Retry in Import errors before closing this session."


def refresh_error_log(store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    if store is None:
        note("Shared error storage is not enabled. Only this session's records are available.")
        return
    try:
        records, notices = ErrorJournal(store).load_month(ss.get("error_log_month", datetime.now(timezone.utc).strftime("%Y-%m")), limit=100)
        ss["loaded_error_events"] = {x['record']['id']: x for x in records}
        ss["loaded_error_month"] = ss["error_log_month"]
        ss["error_list_notices"] = notices
    except (StorageError, ValueError):
        note("The shared error log could not be refreshed. The previous displayed list has not been changed.", "error")


def set_error_review(ident: str, status: str, store: GitHubVault | None) -> None:
    if not require_session():
        return
    ss = st.session_state
    records = dict(ss.get("saved_error_events", {}))
    records.update(ss.get("loaded_error_events", {}))
    record = records.get(ident)
    if record is None or store is None:
        note("Load the saved error record before changing its status.", "error")
        return
    try:
        updated = ErrorJournal(store).set_status(record['record'], record['sha'], status)
        for key in ('saved_error_events', 'loaded_error_events'):
            ss.setdefault(key, {})[ident] = updated
        note("Shared error review status saved.", "success")
    except (StorageError, ValueError):
        note("The review change was not saved. Another team member may have changed it. Refresh the shared log and retry.", "error")


def import_errors_page(store: GitHubVault | None) -> None:
    st.title("Import errors")
    ss = st.session_state
    st.caption("Shared technical reports in the existing private GitHub repository. These reports contain app version, event time, section, error code and row/column positions only. No patient text, clinical values, rooms, names, MRNs, or staff identity are logged.")
    st.caption("This uses the app's existing sign-in. It is not an individual staff audit trail. Marking a report resolved does not change any handoff or remove Git history.")
    if "error_log_month" not in ss:
        ss["error_log_month"] = datetime.now(timezone.utc).strftime("%Y-%m")
    st.text_input("Error log month (UTC, YYYY-MM)", key="error_log_month", max_chars=7)
    st.button("Refresh shared errors", key="refresh_shared_errors", on_click=refresh_error_log, args=(store,), disabled=store is None)
    pending = ss.get("pending_error_events", {})
    if pending:
        st.warning(str(len(pending)) + " technical report(s) are not saved to GitHub and exist only in this session.")
        st.button("Retry saving errors", key="retry_error_upload", on_click=send_pending_errors, args=(store,), disabled=store is None)
    for message in ss.get("error_list_notices", []):
        st.warning(message)
    records = dict(ss.get("saved_error_events", {}))
    records.update(ss.get("loaded_error_events", {}))
    records.update({key: {"record": value, "sha": None} for key, value in pending.items()})
    month = ss.get("error_log_month", "")
    rows = sorted((value for value in records.values() if value["record"]["created_at"].startswith(month)), key=lambda x: x["record"]["created_at"], reverse=True)
    if not rows:
        st.info("No error records loaded for this month. Refresh to retrieve reports from other sessions.")
        return
    safe_report = [value["record"] for value in rows]
    st.download_button("Download technical error report (JSON)", json.dumps(safe_report, indent=2).encode("utf-8"),
                       "import_errors.json", "application/json")
    for value in rows:
        record = value["record"]
        ident = record["id"]
        saved = bool(value["sha"])
        title = record["created_at"] + " | " + record["status"] + " | " + ident[:12] + ("" if saved else " | NOT SAVED")
        with st.expander(title, expanded=False):
            st.caption("App version " + record["app_version"] + " | " + ident)
            for item in record["diagnostics"]:
                st.text(diagnostic_text(item))
                st.caption("Code: " + item["code"])
            status = "resolved" if record["status"] == "open" else "open"
            st.button("Mark resolved" if status == "resolved" else "Reopen", key="resolve_error_" + ident,
                      on_click=set_error_review, args=(ident, status, store), disabled=not saved or store is None)

if __name__ == "__main__":
    try:
        main()
    except (ValidationError, StorageError) as error:
        st.error(str(error))
    except Exception:
        st.error("The app encountered an unexpected problem. No save is confirmed. Keep your draft and reproduce with the synthetic example when troubleshooting.")
