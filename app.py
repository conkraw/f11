"""PICU SmartPhrase handoff foundation. Version 1 imports Diagnoses only."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import time
import uuid

import streamlit as st
from cryptography.fernet import Fernet

from exports import handoff_html, handoff_text
from github_store import GitHubConfig, GitHubVault, StorageError, ConflictError
from models import (MAX_FIELD, SYSTEMS, ValidationError, apply_diagnoses, new_sheet,
                    new_vault, normalize_room, save_sheet_in, validate_vault)
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


def set_editor(room: str, sheet: dict) -> None:
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


def clear_paste() -> None:
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
    set_editor(room, updated)
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
    st.caption("Version 1 imports Diagnoses only. All other handoff sections can be edited manually.")
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
    if saved is None or saved["fields"] != sheet["fields"] or saved["id"] != sheet["id"]:
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
    import_tab, edit_tab, preview_tab = st.tabs(["Paste / Diagnoses", "Edit handoff", "Preview / export"])
    with import_tab:
        st.caption("Paste the complete separated SmartPhrase or just the paired Diagnoses section. No OCR is needed for text.")
        left, right = st.columns(2)
        left.button("Load synthetic example", on_click=load_sample)
        right.button("Clear pasted text", on_click=clear_paste)
        with st.form("parse_smartphrase"):
            st.text_area("SmartPhrase text", key="paste", height=250, max_chars=MAX_PASTE)
            st.form_submit_button("Read Diagnoses", on_click=read_diagnoses)
        pending = st.session_state.get("pending")
        if pending and pending["room"] == room:
            for issue in pending["issues"]:
                st.warning(issue)
            with st.expander("Detected section boundaries"):
                for key, status in pending["status"]:
                    suffix = "Diagnosis import available" if key == "a" else "Boundary detection only, not imported in version 1"
                    st.text(f"{key.upper()} | {SECTION_NAMES[key]} | {status} | {suffix}")
            if pending["error"]:
                st.error(pending["error"])
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
    with edit_tab:
        st.caption("Changes here stay in this session until you click Save handoff. Medication routing is not implemented in this version.")
        for section in SYSTEMS:
            key = edit_key(sheet, section)
            if key not in st.session_state:
                st.session_state[key] = sheet["fields"][section]
            with st.expander(section, expanded=section == "Diagnoses"):
                st.text_area(section, key=key, height=130, max_chars=MAX_FIELD,
                             on_change=update_field, args=(room, section, key))
    with preview_tab:
        st.text(handoff_text(sheet))
        st.caption("Downloads are unencrypted copies. Store them only in an approved location. Open the HTML in a browser and use Print to print or save as PDF.")
        st.download_button("Download printable handoff (HTML)", handoff_html(sheet).encode("utf-8"), "handoff.html", "text/html")
        st.download_button("Download handoff text", handoff_text(sheet).encode("utf-8"), "handoff.txt", "text/plain")
    st.divider()
    st.checkbox("I checked this room's current patient and all included handoff text against Epic.", key="reviewed")
    st.button("Save handoff to encrypted GitHub" if store else "Save handoff in this session only",
              on_click=save_room, args=(store,), disabled=not st.session_state.get("reviewed"), type="primary")


def admin_page(store: GitHubVault | None) -> None:
    st.title("Admin")
    settings = st.session_state["vault"]["settings"]
    st.caption("The app password protects this workspace too. There is no second Admin password.")
    with st.form("admin_settings"):
        destination = st.selectbox("Default destination for Diagnoses", SYSTEMS, index=SYSTEMS.index(settings["diagnoses_destination"]))
        rooms_text = st.text_area("Room dropdown, one room per line", "\n".join(settings["rooms"]), height=230)
        submit = st.form_submit_button("Save Admin settings")
    if submit:
        try:
            rooms = [normalize_room(line) for line in rooms_text.splitlines() if line.strip()]
            candidate = deepcopy(st.session_state["vault"])
            candidate["settings"] = {"diagnoses_destination": destination, "rooms": rooms}
            commit(candidate, store)
        except (StorageError, ValidationError) as exc:
            st.error(str(exc))
        else:
            st.success("Encrypted Admin settings saved." if store else "Admin settings saved for this session only.")
    st.subheader("Separator contract")
    st.caption("Use matching repeated-letter lines, at least eight letters long, on lines of their own. Counts do not need to match.")
    for key, heading in SECTION_NAMES.items():
        st.text(f"{key * 8}  =  {heading}" + ("  | imports diagnosis text" if key == "a" else "  | reserved for a later parser"))
    st.info("Version 1 recognizes boundaries for B through J but does not extract medications, doses, ventilation, vitals, cultures, labs, intake/output, nutrition, or wounds. Nothing from those sections is silently added to the handoff.")
    st.caption("Changing a default affects future imports only. It does not move or overwrite text already in a handoff.")


if __name__ == "__main__":
    try:
        main()
    except (ValidationError, StorageError) as error:
        st.error(str(error))
    except Exception:
        # Do not send exception strings, local variables, or patient text to logs/UI.
        st.error("The app encountered an unexpected problem. No save is confirmed. Keep your draft, reload the saved archive, and compare before retrying. Reproduce with the synthetic example when troubleshooting.")
