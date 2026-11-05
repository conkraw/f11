"""PICU SmartPhrase version 2: diagnoses, medication routing, landscape export."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import time
import uuid

import streamlit as st
from cryptography.fernet import Fernet

from exports import handoff_html, handoff_text, handoff_pdf
from github_store import GitHubConfig, GitHubVault, StorageError, ConflictError
from models import (MAX_FIELD, SYSTEMS, ValidationError, apply_diagnoses, new_sheet,
                    new_vault, normalize_room, save_sheet_in, validate_vault, apply_medications, fields_with_medications, upgrade_vault)
from medications import (DESTINATIONS, parse_medications, format_medication, suggested_key,
                         upsert_rule, remap, destination_for, normalized)
from parser import MAX_PASTE, SECTION_NAMES, parse_smartphrase
from security import valid_password_hash, verify_password

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="PICU Handoff", layout="wide", initial_sidebar_state="expanded")


def note(text: str, kind: str = "info") -> None:
    st.session_state["notice"] = (kind, text)


def clear_session() -> None:
    st.session_state.clear()


def require_session() -> bool:
    """Callbacks run before the main script, so enforce expiry here as well."""
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


def set_editor(room: str, sheet: dict, keep_medication_import: bool = False) -> None:
    old = st.session_state.setdefault("drafts", {}).get(room)
    if old:
        for section in SYSTEMS:
            st.session_state.pop(edit_key(old, section), None)
    st.session_state["drafts"][room] = deepcopy(sheet)
    for section in SYSTEMS:
        st.session_state[edit_key(sheet, section)] = sheet["fields"][section]
    st.session_state["reviewed"] = False
    st.session_state.pop("pending", None)
    st.session_state.pop("diagnosis_preview", None)
    if not keep_medication_import:
        clear_medication_preview()
    if not st.session_state.get("medication_pending"):
        st.session_state["paste"] = ""


def open_room() -> None:
    if not require_session():
        return
    chosen = st.session_state.get("room_choice", "")
    value = st.session_state.get("other_room", "") if chosen == "Other room" else chosen
    try:
        room = normalize_room(value)
    except ValidationError as exc:
        note(str(exc), "error")
        return
    st.session_state["current_room"] = room
    drafts = st.session_state.setdefault("drafts", {})
    if room not in drafts:
        saved = st.session_state["vault"]["rooms"].get(room)
        st.session_state.setdefault("base_sheets", {})[room] = deepcopy(saved)
        set_editor(room, saved if saved else new_sheet(room))
    else:
        st.session_state["reviewed"] = False
        st.session_state["paste"] = ""
        st.session_state.pop("pending", None)
    clear_medication_preview()
    st.session_state["confirm_new"] = False


def update_field(room: str, section: str, key: str) -> None:
    if not require_session():
        return
    st.session_state["drafts"][room]["fields"][section] = st.session_state[key]
    st.session_state["reviewed"] = False


def load_sample() -> None:
    if not require_session():
        return
    st.session_state["paste"] = (ROOT / "examples" / "synthetic_smartphrase.txt").read_text(encoding="utf-8")
    st.session_state.pop("pending", None)
    clear_medication_preview()


def clear_paste() -> None:
    clear_medication_preview()
    st.session_state["paste"] = ""
    st.session_state.pop("pending", None)
    st.session_state.pop("diagnosis_preview", None)


def read_diagnoses() -> None:
    if not require_session():
        return
    parsed = parse_smartphrase(st.session_state.get("paste", ""))
    status = []
    for key in SECTION_NAMES:
        status.append((key, "Check divider" if key in parsed.invalid else "Detected" if key in parsed.blocks else "Not included"))
    st.session_state["pending"] = {"room": st.session_state["current_room"], "issues": parsed.issues,
                                   "error": parsed.diagnosis_error, "status": status, "text": "\n".join(parsed.diagnoses)}
    st.session_state["diagnosis_preview"] = "\n".join(parsed.diagnoses)
    st.session_state["import_destination"] = st.session_state["vault"]["settings"]["diagnoses_destination"]
    st.session_state["replace_confirm"] = False


def update_diagnosis_preview() -> None:
    if require_session() and "pending" in st.session_state:
        st.session_state["pending"]["text"] = st.session_state.get("diagnosis_preview", "")


def apply_import() -> None:
    if not require_session():
        return
    room = st.session_state["current_room"]
    pending = st.session_state.get("pending", {})
    if pending.get("room") != room or pending.get("error"):
        note("Read and review the diagnoses for this room first.", "error")
        return
    destination = st.session_state["import_destination"]
    draft = st.session_state["drafts"][room]
    append = st.session_state.get("import_mode") == "Append"
    if draft["fields"][destination].strip() and not append and not st.session_state.get("replace_confirm"):
        note("Confirm replacement of the existing destination text, or choose Append.", "error")
        return
    try:
        updated = apply_diagnoses(draft, st.session_state.get("diagnosis_preview", ""), destination, append)
    except ValidationError as exc:
        note(str(exc), "error")
        return
    set_editor(room, updated, keep_medication_import=True)
    note("Diagnoses added to the editable handoff. They are not saved to GitHub yet.")


def start_new_patient() -> None:
    if not require_session():
        return
    if not st.session_state.get("confirm_new"):
        note("Confirm that this is a new patient in the selected room.", "error")
        return
    room = st.session_state["current_room"]
    st.session_state.setdefault("base_sheets", {})[room] = deepcopy(st.session_state["vault"]["rooms"].get(room))
    set_editor(room, new_sheet(room))
    st.session_state["confirm_new"] = False
    note("A blank handoff is open. Save it explicitly to replace the room's current saved sheet.")


def load_saved_into_editor() -> None:
    if not require_session():
        return
    if not st.session_state.get("confirm_discard"):
        note("Confirm that you want to discard the current draft.", "error")
        return
    room = st.session_state["current_room"]
    saved = st.session_state["vault"]["rooms"].get(room)
    st.session_state.setdefault("base_sheets", {})[room] = deepcopy(saved)
    set_editor(room, saved if saved else new_sheet(room))
    st.session_state["confirm_discard"] = False
    note("The saved version is now in the editor.")


def commit(candidate: dict, store: GitHubVault | None) -> None:
    validate_vault(candidate)
    if store is not None:
        new_sha = store.save(candidate, st.session_state.get("vault_sha"))
        st.session_state["vault_sha"] = new_sha
    st.session_state["vault"] = candidate


def save_room(store: GitHubVault | None) -> None:
    if not require_session():
        return
    room = st.session_state["current_room"]
    latest = st.session_state["vault"]["rooms"].get(room)
    baseline = st.session_state.get("base_sheets", {}).get(room)
    if baseline != latest:
        note("This room has a newer saved handoff. Compare it with your draft, then use Load saved handoff before applying your edits again.", "error")
        return
    if not st.session_state.get("reviewed"):
        note("Check the room, current patient, and handoff text before saving.", "error")
        return
    try:
        candidate = save_sheet_in(st.session_state["vault"], st.session_state["drafts"][room])
        commit(candidate, store)
    except (StorageError, ValidationError) as exc:
        note(str(exc), "error")
        return
    saved = deepcopy(candidate["rooms"][room])
    st.session_state["drafts"][room] = saved
    st.session_state["base_sheets"][room] = deepcopy(saved)
    note("Encrypted handoff saved to GitHub." if store else "Saved only in this browser session. GitHub is not enabled.", "success")


def clear_medication_preview() -> None:
    st.session_state.pop("medication_pending", None)
    st.session_state["med_import_reviewed"] = False
    st.session_state["med_replace_confirm"] = False
    for key in list(st.session_state):
        if key.startswith("med_pending_"):
            st.session_state.pop(key, None)


def read_medications() -> None:
    if not require_session():
        return
    clear_medication_preview()
    ss = st.session_state
    parsed = parse_smartphrase(ss.get("paste", ""))
    if "b" not in parsed.blocks or "b" in parsed.invalid:
        ss["medication_pending"] = {"room": ss["current_room"], "rows": [], "issues": [],
            "error": "No valid Medications block was found. Use one complete B-divider pair with Medications: inside.", "empty_confirmed": False}
        return
    result = parse_medications(parsed.blocks["b"], ss["vault"]["settings"]["medication_mappings"])
    ss["medication_pending"] = {"room": ss["current_room"], "rows": result.rows,
        "issues": result.issues, "error": result.error, "empty_confirmed": result.empty_confirmed}


def read_sections() -> None:
    if not require_session():
        return
    read_diagnoses()
    read_medications()


def apply_medication_import() -> None:
    if not require_session():
        return
    ss = st.session_state
    room = ss["current_room"]
    pending = ss.get("medication_pending", {})
    if pending.get("room") != room or pending.get("error"):
        note("Read and review a valid medication block for this room first.", "error")
        return
    if not ss.get("med_import_reviewed"):
        note("Review the medication names, doses, routes, frequencies, and rates before applying.", "error")
        return
    if ss["drafts"][room]["medications"] and not ss.get("med_replace_confirm"):
        note("Confirm replacement of the previous medication import. Your system notes will be kept.", "error")
        return
    try:
        ss["drafts"][room] = apply_medications(ss["drafts"][room], pending["rows"])
    except ValidationError as exc:
        note(str(exc), "error")
        return
    clear_medication_preview()
    ss["reviewed"] = False
    if not ss.get("pending") or ss["pending"].get("error"):
        ss["paste"] = ""
    note("Medications applied to this room's draft. Save the handoff explicitly to store it in GitHub.")


def medication_row_change(context: str, room: str, row_id: str, field: str, widget_key: str) -> None:
    if not require_session():
        return
    ss = st.session_state
    if room != ss.get("current_room"):
        return
    rows = ss.get("medication_pending", {}).get("rows", []) if context == "pending" else ss["drafts"][room]["medications"]
    for row in rows:
        if row["id"] == row_id:
            row[field] = ss[widget_key]
            break
    ss["reviewed"] = False
    ss["med_import_reviewed"] = False


def reapply_current_mappings() -> None:
    if not require_session():
        return
    ss = st.session_state
    room = ss.get("current_room")
    if not room:
        return
    rules = ss["vault"]["settings"]["medication_mappings"]
    ss["drafts"][room]["medications"] = remap(ss["drafts"][room]["medications"], rules)
    if ss.get("medication_pending", {}).get("room") == room:
        ss["medication_pending"]["rows"] = remap(ss["medication_pending"]["rows"], rules)
    # Update or discard widget backing values before rendering them on the next run.
    for key in list(ss):
        if key.startswith("med_") and key.endswith("_section"):
            ss.pop(key, None)
    ss["reviewed"] = False
    ss["med_import_reviewed"] = False
    note("Saved mappings reapplied to this room's medication draft. Per-order destinations were reset. Other saved handoffs were not changed.")


def medication_editor(rows: list[dict], context: str, room: str) -> None:
    for number, row in enumerate(rows, 1):
        st.text(f"{number}. [{row['section']}] " + format_medication(row) + ("" if row['include'] else " [EXCLUDED]"))
        label = f"Edit order {number}: {row['name']}"
        with st.expander(label, expanded=False):
            prefix = "med_" + context + "_" + row["id"] + "_"
            def widget(field: str, label: str, kind: str = "text"):
                key = prefix + field
                if key not in st.session_state:
                    st.session_state[key] = row[field]
                args = (context, room, row["id"], field, key)
                if kind == "check":
                    st.checkbox(label, key=key, on_change=medication_row_change, args=args)
                elif kind == "select":
                    st.selectbox(label, DESTINATIONS, key=key, on_change=medication_row_change, args=args)
                elif kind == "area":
                    st.text_area(label, key=key, height=85, max_chars=4000, on_change=medication_row_change, args=args)
                else:
                    st.text_input(label, key=key, max_chars=4000, on_change=medication_row_change, args=args)
            widget("include", "Include this order in the handoff", "check")
            widget("section", "Handoff destination for this order", "select")
            widget("name", "Medication / formulation")
            left, right = st.columns(2)
            with left:
                widget("dose", "Dose from the Dose column")
                widget("frequency", "Frequency")
            with right:
                widget("route", "Route")
                widget("last_rate", "Last recorded rate, value and units")
            widget("rate_time", "Rate timestamp from Epic")
            widget("custom_text", "Optional custom handoff wording, overrides generated wording", "area")
            for warning in row["warnings"]:
                st.caption(warning)
            st.caption("Preview")
            st.text(format_medication(row))
            st.caption("To remember a system for future imports, add its medication name in Admin. This dropdown changes only this order.")


def medications_page(room: str, sheet: dict) -> None:
    st.caption("Each Epic order stays separate. Providers and Last Admin are omitted. A blank Dose with a continuous Last Rate uses @ rate.")
    pending = st.session_state.get("medication_pending")
    if pending and pending["room"] == room:
        st.subheader("Medication import review")
        for issue in pending["issues"]:
            st.warning(issue)
        if pending["error"]:
            st.error(pending["error"])
        else:
            rows = pending["rows"]
            st.text(f"Detected {len(rows)} orders. Unmapped orders: {sum(r['section'] == 'Other Medications' for r in rows)}.")
            if pending["empty_confirmed"]:
                st.warning("The source explicitly says there are no medications. Applying it removes the previous imported medication list.")
            medication_editor(rows, "pending", room)
            st.checkbox("I checked the imported medication names, doses, routes, frequencies, and recorded rates against Epic.", key="med_import_reviewed")
            if sheet["medications"]:
                st.checkbox("Replace the previous imported medication list. Keep my system notes.", key="med_replace_confirm")
            st.button("Apply medications to handoff", on_click=apply_medication_import, disabled=not st.session_state.get("med_import_reviewed"), type="primary")
    st.subheader("Medications in this handoff")
    if sheet["medications"]:
        st.caption("Edit an order below, then save the handoff. Excluding an order hides it from the output without merging it with another order.")
        medication_editor(sheet["medications"], "draft", room)
        st.button("Reapply saved mappings to this room", on_click=reapply_current_mappings,
                  help="Resets per-order destinations to the current Admin rules. Unmatched orders move to Other Medications.")
    else:
        st.info("No medications have been applied to this handoff yet. Read the B block in Paste / import.")


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


def upgrade_existing_session() -> None:
    ss = st.session_state
    vault = ss.get("vault")
    if not vault or vault.get("schema") != 1:
        return
    legacy_settings = deepcopy(vault["settings"])
    converted = upgrade_vault(vault)
    drafts, bases = {}, {}
    for source_key, target in (("drafts", drafts), ("base_sheets", bases)):
        for room, sheet in ss.get(source_key, {}).items():
            if sheet is None:
                target[room] = None
            else:
                wrapper = {"schema": 1, "settings": legacy_settings, "rooms": {room: sheet}}
                target[room] = upgrade_vault(wrapper)["rooms"][room]
    ss.update(vault=converted, drafts=drafts, base_sheets=bases)
    ss["reviewed"] = False


def main() -> None:
    app, store = load_config()
    now = time.monotonic()
    if st.session_state.get("authenticated") and (now - st.session_state.get("last_activity", now) > app["idle_minutes"] * 60 or now - st.session_state.get("login_at", now) > 8 * 3600):
        clear_session()
    if not st.session_state.get("authenticated"):
        st.title("PICU Handoff")
        st.caption("SmartPhrase foundation | Sign in")
        with st.form("login"):
            st.text_input("App password", type="password", key="login_password", max_chars=1024)
            st.form_submit_button("Open app", on_click=authenticate, args=(app["password_hash"],))
        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])
        st.caption("Use synthetic data until the hosting and storage have institutional approval. No separate Admin password is required.")
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
        page = st.radio("Workspace", ["Handoff", "Admin"], key="page")
        st.caption("Encrypted GitHub storage" if store else "Session-only testing. No persistence.")
        if st.button("Reload saved archive", disabled=store is None):
            try:
                fresh, sha = store.load()
                st.session_state.update(vault=fresh, vault_sha=sha)
                note("Saved archive reloaded. Your open drafts were kept for comparison.")
            except (StorageError, ValidationError) as exc:
                note(str(exc), "error")
        st.button("Log out and clear session", on_click=clear_session)
        st.caption("Unsaved drafts are lost on logout, timeout, or browser-session loss.")
    if not app.get("clinical_use_approved", False):
        st.warning("Synthetic-data testing only. Do not paste clinical records until your institution has approved BOTH the Streamlit host and the GitHub storage arrangement. Encryption alone is not approval.")
    else:
        st.caption("Clinical-use approval is an administrator declaration, not a compliance certification. Confirm patient identity in Epic.")
    if "notice" in st.session_state:
        kind, text = st.session_state.pop("notice")
        getattr(st, kind)(text)
    if page == "Admin":
        admin_page(store)
    else:
        handoff_page(store)


def handoff_page(store: GitHubVault | None) -> None:
    st.title("Room handoff")
    st.caption("Import Diagnoses and Medications. Unmapped orders go to Other Medications. Print in landscape.")
    settings = st.session_state["vault"]["settings"]
    choices = list(dict.fromkeys(settings["rooms"] + list(st.session_state["vault"]["rooms"]) + list(st.session_state.get("drafts", {}))))
    st.selectbox("Choose room", ["Choose a room"] + choices + ["Other room"], key="room_choice")
    if st.session_state.get("room_choice") == "Other room":
        st.text_input("Other room number", key="other_room", max_chars=16)
    st.button("Open room", on_click=open_room, disabled=st.session_state.get("room_choice") == "Choose a room")
    room = st.session_state.get("current_room")
    if not room:
        st.info("Choose a room and click Open room before pasting text.")
        return
    sheet = st.session_state["drafts"][room]
    st.subheader("Editing room " + room)
    st.caption("Handoff reference: " + sheet["id"][:8] + " | Saved (UTC): " + (sheet["updated_at"] or "Not yet saved"))
    saved = st.session_state["vault"]["rooms"].get(room)
    if saved is None or saved != sheet:
        st.info("This handoff has unsaved changes.")
    if st.session_state.get("base_sheets", {}).get(room) != saved:
        st.warning("The saved handoff changed after you opened this draft. Review the latest version below before saving.")
    with st.expander("New patient / reload saved handoff"):
        st.checkbox("This is a NEW patient in this room. Start a blank handoff.", key="confirm_new")
        st.button("Start blank for new patient", on_click=start_new_patient)
        st.caption("The previous saved sheet is replaced only when you save the new sheet. GitHub history retains earlier encrypted versions.")
        if saved:
            st.text(handoff_text(saved))
        st.checkbox("Discard the current draft and load the saved handoff.", key="confirm_discard")
        st.button("Load saved handoff into editor", on_click=load_saved_into_editor)
    import_tab, medication_tab, edit_tab, preview_tab = st.tabs(["Paste / import", "Medications", "Edit handoff", "Preview / export"])
    with import_tab:
        st.caption("Paste the complete SmartPhrase, or the paired A and/or B blocks. Copy directly from Epic so medication columns retain their tabs. No OCR is needed.")
        left, right = st.columns(2)
        left.button("Load synthetic example", on_click=load_sample)
        right.button("Clear pasted text", on_click=clear_paste)
        with st.form("parse_smartphrase"):
            st.text_area("SmartPhrase text", key="paste", height=250, max_chars=MAX_PASTE)
            st.form_submit_button("Read Diagnoses + Medications", on_click=read_sections)
        medication_pending = st.session_state.get("medication_pending")
        if medication_pending and not medication_pending.get("error"):
            st.info("Medication results are ready in the Medications tab. Review and apply them there.")
        pending = st.session_state.get("pending")
        if pending and pending["room"] == room:
            for issue in pending["issues"]:
                st.warning(issue)
            with st.expander("Detected section boundaries"):
                for key, status in pending["status"]:
                    suffix = "Import available" if key in ("a", "b") else "Boundary detection only, not imported yet"
                    st.text(f"{key.upper()} | {SECTION_NAMES[key]} | {status} | {suffix}")
            if pending["error"]:
                st.info(pending["error"])
            else:
                if "diagnosis_preview" not in st.session_state:
                    st.session_state["diagnosis_preview"] = pending.get("text", "")
                if "import_destination" not in st.session_state:
                    st.session_state["import_destination"] = settings["diagnoses_destination"]
                st.text_area("Extracted diagnoses, editable", key="diagnosis_preview", height=120, max_chars=MAX_FIELD,
                             on_change=update_diagnosis_preview)
                st.selectbox("Place diagnoses in", SYSTEMS, key="import_destination")
                st.radio("When applying", ["Replace", "Append"], key="import_mode", horizontal=True)
                destination = st.session_state.get("import_destination", "Diagnoses")
                if sheet["fields"][destination].strip() and st.session_state.get("import_mode") == "Replace":
                    st.checkbox("Replace the existing text in the selected section.", key="replace_confirm")
                st.button("Apply diagnoses to handoff", on_click=apply_import)
    with medication_tab:
        medications_page(room, sheet)
    with edit_tab:
        st.caption("System notes are editable below. Medication wording and destinations are edited in the Medications tab, so reimporting cannot erase your notes.")
        display_fields = fields_with_medications(sheet)
        for section in SYSTEMS:
            key = edit_key(sheet, section)
            if key not in st.session_state:
                st.session_state[key] = sheet["fields"][section]
            with st.expander(section, expanded=section == "Diagnoses"):
                st.text_area("Notes: " + section, key=key, height=100, max_chars=MAX_FIELD,
                             on_change=update_field, args=(room, section, key))
                meds_here = [m for m in sheet["medications"] if m["include"] and m["section"] == section]
                if meds_here:
                    st.caption("Medications included below these notes. Edit them in the Medications tab.")
                    for row in meds_here:
                        st.text(format_medication(row))
    with preview_tab:
        import streamlit.components.v1 as components
        st.caption("Landscape Letter. Long content continues onto additional pages in the PDF rather than being cut off.")
        components.html(handoff_html(sheet), height=660, scrolling=True)
        st.caption("Downloads are unencrypted. Check all entries against Epic and store copies only in an approved location.")
        try:
            pdf = handoff_pdf(sheet)
            st.download_button("Download landscape handoff (PDF)", pdf, "handoff.pdf", "application/pdf")
        except (ValueError, ImportError):
            st.warning("PDF export is unavailable. Confirm requirements.txt was installed, or use printable HTML/text.")
        st.download_button("Download printable landscape handoff (HTML)", handoff_html(sheet).encode("utf-8"), "handoff.html", "text/html")
        st.download_button("Download handoff text", handoff_text(sheet).encode("utf-8"), "handoff.txt", "text/plain")
    st.divider()
    st.checkbox("I checked this room's current patient and all included handoff text against Epic.", key="reviewed")
    st.button("Save handoff to encrypted GitHub" if store else "Save handoff in this session only",
              on_click=save_room, args=(store,), disabled=not st.session_state.get("reviewed"), type="primary")


def select_mapping_candidate() -> None:
    if not require_session():
        return
    choice = st.session_state.get("mapping_candidate", "")
    if choice and choice != "Type a medication name":
        st.session_state["mapping_name"] = choice


def admin_page(store: GitHubVault | None) -> None:
    st.title("Admin")
    settings = st.session_state["vault"]["settings"]
    st.caption("The app password protects this workspace too. There is no second Admin password.")
    st.subheader("Medication-to-system mappings")
    st.caption("Save a name such as acetaminophen, not a patient's dose. Matching is case-insensitive and starts at the beginning of the medication name. A more specific matching rule takes priority.")
    room = st.session_state.get("current_room")
    detected = []
    if room:
        detected += st.session_state["drafts"][room]["medications"]
        if st.session_state.get("medication_pending", {}).get("room") == room:
            detected += st.session_state["medication_pending"]["rows"]
    candidates = sorted({suggested_key(row["name"]) for row in detected})
    choices = ["Type a medication name"] + candidates
    if st.session_state.get("mapping_candidate") not in choices:
        st.session_state["mapping_candidate"] = choices[0]
    st.selectbox("Choose a detected medication or type a name below", choices, key="mapping_candidate", on_change=select_mapping_candidate)
    with st.form("medication_mapping"):
        name = st.text_input("Medication name or name prefix", key="mapping_name", max_chars=250, placeholder="acetaminophen")
        destination = st.selectbox("Default system", DESTINATIONS, key="mapping_destination")
        match_label = st.selectbox("Match rule", ["Medication name starts with this text", "Exact complete medication name"])
        apply_now = st.checkbox("Reapply all saved mappings to the current room's draft and import preview", value=True,
                                help="This resets any per-order destination choices in the open room. It does not save the clinical handoff.")
        confirmed = st.checkbox("This rule contains only a medication name or formulation, not patient information.")
        submit_mapping = st.form_submit_button("Save medication mapping")
    if submit_mapping:
        if not confirmed:
            st.warning("Confirm that the rule does not contain patient information.")
        else:
            try:
                candidate = deepcopy(st.session_state["vault"])
                match = "exact" if match_label == "Exact complete medication name" else "prefix"
                candidate["settings"]["medication_mappings"] = upsert_rule(settings["medication_mappings"], name, destination, match)
                commit(candidate, store)
                settings = candidate["settings"]
                if apply_now and room:
                    reapply_current_mappings()
                st.success("Medication mapping saved." + (" It is encrypted in GitHub." if store else " Session-only test mode."))
            except (StorageError, ValidationError, ValueError) as exc:
                st.error(str(exc))
    rules = st.session_state["vault"]["settings"]["medication_mappings"]
    if rules:
        with st.expander("Saved medication mappings", expanded=True):
            for rule in rules:
                st.text(rule["name"] + " [" + rule["match"] + "] -> " + rule["destination"])
            labels = [r["name"] + " [" + r["match"] + "]" for r in rules]
            selected = st.selectbox("Mapping to remove", labels)
            remove_confirm = st.checkbox("Remove this mapping from future imports")
            if st.button("Remove selected mapping", disabled=not remove_confirm):
                candidate = deepcopy(st.session_state["vault"])
                candidate["settings"]["medication_mappings"].pop(labels.index(selected))
                try:
                    commit(candidate, store)
                    note("Mapping removed. Use Reapply saved mappings in the current handoff to update its destinations.")
                    st.rerun()
                except (StorageError, ValidationError) as exc:
                    st.error(str(exc))
    else:
        st.info("No medication mappings yet. All imported orders go to Other Medications until you assign them.")
    st.subheader("Room and diagnosis settings")
    with st.form("admin_settings"):
        destination = st.selectbox("Default destination for Diagnoses", SYSTEMS, index=SYSTEMS.index(settings["diagnoses_destination"]))
        rooms_text = st.text_area("Room dropdown, one room per line", "\n".join(settings["rooms"]), height=160)
        submit = st.form_submit_button("Save Admin settings")
    if submit:
        try:
            rooms = [normalize_room(line) for line in rooms_text.splitlines() if line.strip()]
            candidate = deepcopy(st.session_state["vault"])
            candidate["settings"].update(diagnoses_destination=destination, rooms=rooms)
            commit(candidate, store)
        except (StorageError, ValidationError) as exc:
            st.error(str(exc))
        else:
            st.success("Admin settings saved. Medication mappings were preserved.")
    with st.expander("Section separators"):
        for key, heading in SECTION_NAMES.items():
            st.text(f"{key * 8}  =  {heading}" + ("  | import available" if key in ("a", "b") else "  | not imported yet"))
        st.caption("Only Diagnoses and Medications are imported automatically in this version. Other sections remain editable manually.")


if __name__ == "__main__":
    try:
        main()
    except (ValidationError, StorageError) as error:
        st.error(str(error))
    except Exception:
        # Do not send exception strings, local variables, or patient text to logs/UI.
        st.error("The app encountered an unexpected problem. No save is confirmed. Keep your draft, reload the saved archive, and compare before retrying. Reproduce with the synthetic example when troubleshooting.")
