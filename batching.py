"""Combine saved rooms and current-session drafts without cross-room merging."""
from copy import deepcopy
import re
from models import validate_sheet
from medications import visible
from observations import neuro_rows, format_nutrition
from viral import viral_text
from blood_gases import latest_sample
from cbc import cbc_cards
from recurring_orders import selected_orders
from fluid_balance import balance_text
from feeds import feeds_text, feeds_for_output
from devices import devices_text, evd_text


def room_order(room: str):
    room = room[1:] if room.startswith("P") and room[1:].isdigit() else room
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"(\d+)", room) if part)


def available_handoffs(vault: dict, drafts: dict) -> dict:
    rooms = deepcopy(vault["rooms"])
    rooms.update(deepcopy(drafts))  # An open draft is the latest displayed version.
    ready = {}
    for room, sheet in rooms.items():
        validate_sheet(sheet)
        if sheet.get("import_warnings") or any(v.strip() for v in sheet["fields"].values()) or any(visible(r) for r in sheet["medications"]) or sheet["ventilation"] or sheet["noninvasive"] or any(r["include"] for r in sheet["vitals"]) or any(r["include"] for r in sheet["labs"]["rows"]) or sheet["labs"]["notes"] or cbc_cards(sheet["labs"], sheet["cbc"]) or latest_sample(sheet["blood_gas"])[0] or any(r["include"] for r in neuro_rows(sheet["neuro_vitals"])) or format_nutrition(sheet["nutrition"]) or sheet["dosing_weight"] or sheet["admission_date"] or viral_text(sheet["viral_panel"]) or any(r["include"] for r in sheet["cultures"]["rows"]) or selected_orders(sheet["recurring_orders"]) or balance_text(sheet["intake_output"]) or feeds_text(feeds_for_output(sheet)) or devices_text(sheet) or evd_text(sheet):
            ready[room] = sheet
    return {room: ready[room] for room in sorted(ready, key=room_order)}
