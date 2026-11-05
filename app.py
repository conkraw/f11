"""PICU SmartPhrase v6: dated labs, routed vitals and reversible medication hiding."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import time

import streamlit as st
from cryptography.fernet import Fernet
from exports import handoff_html, handoff_text, handoff_pdf, handoffs_pdf, handoffs_html
from github_store import GitHubConfig, GitHubVault, StorageError
from models import (MAX_FIELD, SYSTEMS, ValidationError, new_sheet, new_vault,
                    normalize_room, save_sheet_in, validate_vault, validate_sheet,
                    upgrade_vault, fields_with_medications, respiratory_text)
from medications import (DESTINATIONS, format_medication, suggested_key, upsert_rule,
                         remap, rule_for_inline_mapping, validate_medication, visible, hidden_for, set_visibility_rule)
from ventilation import LABELS, format_ventilation, validate_ventilation
from noninvasive import DEVICE_FIELDS, format_noninvasive, validate_noninvasive
from importing import import_sections
from batching import available_handoffs
from parser import MAX_PASTE, SECTION_NAMES
from security import valid_password_hash, verify_password
from labs import validate_labs, lactate_text
from vitals import validate_vitals, text_by_system
from lab_layout import laboratory_html

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
        if key.startswith(("field_", "med_draft_", "med_pending_", "vent_", "niv_", "lab_", "vital_")):
            st.session_state.pop(key, None)


def set_editor(room: str, sheet: dict) -> None:
    validate_sheet(sheet)
    discard_editor_widget_values()
    st.session_state.setdefault("drafts", {})[room] = deepcopy(sheet)
    st.session_state["paste"] = ""
    st.session_state.pop("import_result", None)


def open_room() -> None:
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


def room_changed() -> None:
    if st.session_state.get("room_choice") not in ("Choose a room", "Other room"):
        open_room()


def update_field(room: str, section: str, key: str) -> None:
    if require_session():
        st.session_state["drafts"][room]["fields"][section] = st.session_state[key]


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


def labs_vitals_editor(sheet: dict) -> None:
    import streamlit.components.v1 as components
    st.subheader("Laboratory results")
    st.caption("CBC and BMP show the last two supplied results per component. Other tests show the latest result per component. Arterial and venous gases stay separate. Dates and source flags are preserved. No collection times or same-draw groupings are invented.")
    components.html('<style>.labcards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}.labcard{width:100%;border:1px solid #aaa}.labnote{font:13px sans-serif;margin:8px 0}</style>' + laboratory_html(sheet["labs"]), height=490, scrolling=True)
    if lactate_text(sheet["labs"]):
        st.text("Cardiovascular: " + lactate_text(sheet["labs"]))
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


def create_handoff() -> None:
    if not require_session():
        return
    ss = st.session_state
    room = ss.get("current_room")
    if not room:
        note("Select a room first.", "error")
        return
    result = import_sections(ss["drafts"][room], ss.get("paste", ""), ss["vault"]["settings"])
    if result.sheet is not None:
        set_editor(room, result.sheet)
    ss["import_result"] = {"room": room, "errors": result.errors,
                           "notices": result.notices, "imported": result.imported}


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
    note("Handoffs saved to encrypted GitHub." if store else "Saved in this session only. GitHub is not enabled.", "success")


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
        sheet["medications"] = remap(sheet["medications"], rules, ss["vault"]["settings"]["medication_visibility"])
    # These callbacks run before the widgets are instantiated on the next run.
    for key in list(ss):
        if key.startswith("med_") and key.endswith("_section"):
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
    old_value = original[field]
    edited = deepcopy(original)
    edited[field] = ss[widget_key]
    try:
        validate_medication(edited)
        if field == "section":
            rules = ss["vault"]["settings"]["medication_mappings"]
            name, match = rule_for_inline_mapping(edited["name"], rules)
            new_rules = upsert_rule(rules, name, edited["section"], match)
            if new_rules != rules:
                candidate = deepcopy(ss["vault"])
                candidate["settings"]["medication_mappings"] = new_rules
                commit(candidate, store)  # Persist the rule, not any draft clinical text.
            reapply_open_mappings()
            ss["admin_rule_index"] = -1
            for key in ("mapping_name", "mapping_destination", "mapping_match", "mapping_original"):
                ss.pop(key, None)
            note("Medication destination remembered in Admin." + (" Saved to encrypted GitHub." if store else " Session-only test mode."), "success")
        else:
            if field == "name":
                edited["hidden"] = hidden_for(edited["name"], ss["vault"]["settings"]["medication_visibility"])
            original.update(edited)
    except (ValueError, ValidationError, StorageError) as exc:
        # Do not claim a remembered mapping or move orders after a rejected save.
        ss[widget_key] = old_value
        note(str(exc) + " The change was not saved.", "error")


def ventilation_change(room: str, label: str, key: str) -> None:
    if not require_session():
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
    if not vault or vault.get("schema") == 6:
        return
    old_schema, old_settings = vault["schema"], deepcopy(vault["settings"])
    converted = upgrade_vault(vault)
    changes = {}
    for key in ("drafts", "base_sheets"):
        changes[key] = {}
        for room, sheet in ss.get(key, {}).items():
            changes[key][room] = None if sheet is None else upgrade_vault({"schema": old_schema, "settings": old_settings, "rooms": {room: sheet}})["rooms"][room]
    ss.update(vault=converted, **changes)
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
        st.caption("Version 6 | Labs, vitals and hidden medications")
        page = st.radio("Workspace", ["Handoff", "Print all", "Admin"], key="page")
        st.caption("Encrypted GitHub storage" if store else "Session-only testing. No persistence.")
        st.button("Reload saved archive", on_click=reload_archive, args=(store,), disabled=store is None)
        st.button("Log out", on_click=clear_session)
        st.caption("Save handoffs before logout. Medication mappings save when you change their destination.")
        if not app.get("clinical_use_approved", False):
            st.caption("Use synthetic data unless your hosting and storage have institutional approval. See the setup guide.")
    if "notice" in st.session_state:
        kind, text = st.session_state.pop("notice")
        getattr(st, kind)(text)
    if page == "Admin":
        admin_page(store)
    elif page == "Print all":
        print_all_page(store)
    else:
        handoff_page(store)


def medication_editor(rows: list[dict], room: str, store: GitHubVault | None) -> None:
    for number, row in enumerate(rows, 1):
        prefix = "med_draft_" + row["id"] + "_"
        summary, destination = st.columns([3, 1])
        with summary:
            st.text(f"{number}. " + format_medication(row) + (" [HIDDEN]" if row["hidden"] else "" if row["include"] else " [EXCLUDED]"))
        with destination:
            key = prefix + "section"
            if key not in st.session_state:
                st.session_state[key] = row["section"]
            st.selectbox("System for order " + str(number), DESTINATIONS, key=key,
                         on_change=medication_row_change, args=(room, row["id"], "section", key, store))
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

def handoff_page(store: GitHubVault | None) -> None:
    st.title("Room handoff")
    ss = st.session_state
    settings = ss["vault"]["settings"]
    choices = list(dict.fromkeys(settings["rooms"] + list(ss["vault"]["rooms"]) + list(ss.get("drafts", {}))))
    if "room_choice" not in ss:
        ss["room_choice"] = ss.get("current_room", "Choose a room")
    st.selectbox("Room", ["Choose a room"] + choices + ["Other room"], key="room_choice", on_change=room_changed)
    if ss.get("room_choice") == "Other room":
        st.text_input("Other room number", key="other_room", max_chars=16)
        st.button("Open room", on_click=open_room)
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
    saved = ss["vault"]["rooms"].get(room)
    st.caption("Saved" if saved == sheet else "Unsaved handoff changes")
    if ss.get("base_sheets", {}).get(room) != saved:
        st.warning("A newer saved handoff exists for this room. Reload it before saving your edits.")
    top1, top2 = st.columns(2)
    top1.button("Save handoff", on_click=save_room, args=(store,), type="primary")
    top2.caption("Use Print all in the sidebar for the complete packet.")
    with st.expander("Start over / reload"):
        st.button("Start blank for new patient", on_click=start_new_patient)
        st.button("Load saved handoff", on_click=load_saved_into_editor)
        st.caption("These actions replace the open draft immediately. Saving replaces the room's current saved sheet.")
    paste_tab, meds_tab, labs_tab, edit_tab, preview_tab = st.tabs(["Paste / create", "Medications", "Labs / Vitals", "Edit handoff", "Preview / print"])
    with paste_tab:
        st.caption("Paste the full SmartPhrase or only the paired sections you are updating. A/B import diagnoses and medications, C/D respiratory support, E vital signs and G labs. Omitted sections and separate notes stay unchanged.")
        left, right = st.columns(2)
        left.button("Load synthetic example", on_click=load_sample)
        left.button("Load labs / vitals example", on_click=load_labs_sample)
        left.button("Load nasal-cannula example", on_click=load_niv_sample)
        right.button("Clear pasted text", on_click=clear_paste)
        with st.form("parse_smartphrase"):
            st.text_area("SmartPhrase text", key="paste", height=240, max_chars=MAX_PASTE)
            st.form_submit_button("Create / update handoff", on_click=create_handoff, type="primary")
        result = ss.get("import_result", {})
        if result.get("room") == room:
            for error in result["errors"]:
                st.error(error)
            if result["imported"]:
                st.caption("Updated: " + ", ".join(result["imported"]) + ". Edit below or save the handoff.")
            for message in result["notices"]:
                st.info(message)
        st.subheader("Respiratory support to RESP")
        ventilation_editor(sheet)
    with meds_tab:
        st.caption("Choose a system beside an order. It is remembered immediately in Admin and reused on future imports. Unmapped orders remain in Other Medications.")
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
    with edit_tab:
        st.caption("These are your separate notes. Re-pasting medications or ventilation does not erase them.")
        for section in SYSTEMS:
            key = edit_key(sheet, section)
            if key not in ss:
                ss[key] = sheet["fields"][section]
            with st.expander(section, expanded=section == "Diagnoses"):
                if section in text_by_system(sheet["vitals"]):
                    st.text(text_by_system(sheet["vitals"])[section] + "\n-----")
                if section == "Cardiovascular" and lactate_text(sheet["labs"]):
                    st.text(lactate_text(sheet["labs"]) + "\n-----")
                if section == "Respiratory" and respiratory_text(sheet):
                    st.text(respiratory_text(sheet) + "\n-----")
                    st.caption("Vital signs print first, then support settings. Edit support under Paste / create.")
                st.text_area("Notes: " + section, key=key, height=100, max_chars=MAX_FIELD,
                             on_change=update_field, args=(room, section, key))
                for row in sheet["medications"]:
                    if visible(row) and row["section"] == section:
                        st.text(format_medication(row))
    with preview_tab:
        import streamlit.components.v1 as components
        st.caption("Landscape Letter. Vitals lead each system column, followed by support settings, notes and medications. Dated lab trees appear below the columns.")
        components.html(handoff_html(sheet), height=650, scrolling=True)
        try:
            st.download_button("Download this handoff (PDF)", handoff_pdf(sheet), "handoff.pdf", "application/pdf")
        except (ValueError, ImportError):
            st.error("PDF export could not be created. Confirm requirements.txt is installed or use HTML.")
        st.download_button("Download printable handoff (HTML)", handoffs_html([sheet]).encode("utf-8"), "handoff.html", "text/html")
        st.download_button("Download handoff text", handoff_text(sheet).encode("utf-8"), "handoff.txt", "text/plain")


def print_all_page(store: GitHubVault | None) -> None:
    st.title("Print all handoffs")
    ss = st.session_state
    ready = available_handoffs(ss["vault"], ss.get("drafts", {}))
    if not ready:
        st.info("Create a handoff first. Saved handoffs will also appear here after sign-in.")
        return
    st.caption("Includes saved rooms and the latest open drafts. Printing does not save changes. Blank sheets are omitted.")
    st.button("Save all open handoffs", on_click=save_all_rooms, args=(store,))
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
    try:
        st.download_button("Download all selected handoffs (PDF)", handoffs_pdf(selected_sheets), "all_handoffs.pdf", "application/pdf", type="primary")
    except (ValueError, ImportError):
        st.error("The combined PDF could not be created. Use HTML or check the export requirements.")
    st.download_button("Download all selected handoffs (printable HTML)", handoffs_html(selected_sheets).encode("utf-8"), "all_handoffs.html", "text/html")
    st.caption("Open the PDF and print it, or open the HTML file and click Print all handoffs. Downloaded files are not encrypted.")
    for sheet in selected_sheets:
        st.text("Room " + sheet["room"] + (" | draft" if sheet != ss["vault"]["rooms"].get(sheet["room"]) else " | saved"))


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
        rooms = [normalize_room(line) for line in ss.get("admin_rooms", "").splitlines() if line.strip()]
        candidate = deepcopy(ss["vault"])
        candidate["settings"].update(diagnoses_destination=ss["admin_diagnosis_dest"], rooms=rooms)
        commit(candidate, store)
        note("Room and diagnosis settings saved.", "success")
    except (ValidationError, StorageError) as exc:
        note(str(exc), "error")


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
        st.selectbox("System", DESTINATIONS, key="mapping_destination")
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
    st.subheader("Room and diagnosis settings")
    if "admin_rooms" not in ss:
        ss["admin_rooms"] = "\n".join(settings["rooms"])
    if "admin_diagnosis_dest" not in ss:
        ss["admin_diagnosis_dest"] = settings["diagnoses_destination"]
    with st.form("admin_settings"):
        st.selectbox("Diagnosis destination", SYSTEMS, key="admin_diagnosis_dest")
        st.text_area("Rooms, one per line", key="admin_rooms", height=150)
        st.form_submit_button("Save settings", on_click=save_admin_settings, args=(store,))
    with st.expander("Section imports"):
        for key, heading in SECTION_NAMES.items():
            st.text(key * 8 + " = " + heading + (" | automatic import" if key in "abcdeg" else " | not imported yet"))
        st.caption("C/D rules control the display, not bedside device status. BiPAP needs both D-block pressures. CPAP needs EPAP or PEEP. Explicit HFNC or the documented mask-plus-flow convention can add HFNC. Inferred HFNC is labeled flow-based. No previous-paste values are reused.")


if __name__ == "__main__":
    try:
        main()
    except (ValidationError, StorageError) as error:
        st.error(str(error))
    except Exception:
        st.error("The app encountered an unexpected problem. No save is confirmed. Keep your draft and reproduce with the synthetic example when troubleshooting.")
