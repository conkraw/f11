"""Combine saved rooms and current-session drafts without cross-room merging."""
from copy import deepcopy
import re
from models import validate_sheet


def room_order(room: str):
    room = room[1:] if room.startswith("P") and room[1:].isdigit() else room
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"(\d+)", room) if part)


def available_handoffs(vault: dict, drafts: dict) -> dict:
    rooms = deepcopy(vault["rooms"])
    rooms.update(deepcopy(drafts))  # An open draft is the latest displayed version.
    ready = {}
    for room, sheet in rooms.items():
        validate_sheet(sheet)
        if any(v.strip() for v in sheet["fields"].values()) or any(r["include"] for r in sheet["medications"]) or sheet["ventilation"]:
            ready[room] = sheet
    return {room: ready[room] for room in sorted(ready, key=room_order)}
