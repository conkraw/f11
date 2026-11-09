"""Observed State Behavioral Scale readings, separate from prescribed targets.

Only an explicit measured score with a source date AND time can print as a
recorded SBS in the last 24 hours. Undated readings remain editable but are not
timestamped at upload. Targets never become measured scores. UTC arithmetic
makes the rolling window independent of daylight-saving transitions.

Scale reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC1626525/
Time handling: https://docs.python.org/3/library/datetime.html
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from labs import date_parts
from lab_windows import clock, EASTERN

LABEL = r'(?:SBS(?:\s+(?:total\s+)?score)?|State\s+Behavio(?:u)?r(?:al)?\s+Scale(?:\s*\(SBS\))?(?:\s+score)?)'
LABEL_ONLY = re.compile(r'^' + LABEL + r'\s*:?$', re.I)
LABEL_FIND = re.compile(r'\b(?:SBS|State\s+Behavio(?:u)?r(?:al)?\s+Scale)\b', re.I)
TARGET = re.compile(r'\b(?:target|goal|desired)\b', re.I)
DATE = r'\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})(?!\d)'
TIME = r'(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?|\d{4}(?!\d))'
STAMP = re.compile(r'(?P<date>' + DATE + r')(?:[ T\t]+(?P<time>' + TIME + r'))?')
MISSING = re.compile(r'^(?:|none|--+|-|no data(?: recorded)?|not (?:recorded|documented|assessed)|n/?a|uta|unable to assess|<\s*>)\.?$', re.I)
ERROR = 'An observed SBS entry could not be read. Supply the recorded score with its source date and time.'
NO_TIME = 'SBS readings without a recording date and time are retained for editing but do not print as last-24-hour observations.'
TARGET_NOTE = 'The K section contains a target, not an observed SBS with a recording time. No measured score was inferred.'

@dataclass
class SBSResult:
    data: dict = field(default_factory=lambda: {'readings': [], 'notes': []})
    targets: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    error: str = ''


def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text.replace('\u00a0', ' ').replace('\u2212', '-').replace('\u2013', '-')).strip()


def score(value: str) -> str:
    text = re.sub(r'\s*(?:\*|\(!\))\s*$', '', clean(value))
    m = re.fullmatch(r'(?:SBS\s*:?[ ]*)?([+-]?[0-3])(?:\.0)?', text, re.I)
    if not m or not -3 <= int(m[1]) <= 2:
        raise ValueError('Enter a recorded SBS integer from -3 to 2.')
    return str(int(m[1]))


def validate_sbs(data: dict | None) -> None:
    if data is None:
        return
    if not isinstance(data, dict) or set(data) != {'readings', 'notes'}:
        raise ValueError('The observed SBS record has an invalid structure.')
    if not isinstance(data['readings'], list) or len(data['readings']) > 500:
        raise ValueError('The observed SBS history is invalid or too large.')
    for row in data['readings']:
        if not isinstance(row, dict) or set(row) != {'value', 'recorded_at', 'include'}:
            raise ValueError('An observed SBS row has an invalid structure.')
        score(row['value'])
        if not isinstance(row['recorded_at'], str) or len(row['recorded_at']) > 80:
            raise ValueError('The SBS recording time is invalid.')
        if row['recorded_at']:
            date_parts(row['recorded_at'])
        if type(row['include']) is not bool:
            raise ValueError('The SBS inclusion control is invalid.')
    if (not isinstance(data['notes'], list) or len(data['notes']) > 30
            or any(not isinstance(x, str) or len(x) > 500 for x in data['notes'])):
        raise ValueError('The observed SBS notes are invalid.')


def _stamp(value: str) -> str:
    value = clean(value)
    if value:
        date_parts(value)
    return value


def _add(out: SBSResult, value: str, when: str) -> None:
    if MISSING.fullmatch(clean(value)):
        return
    item = {'value': score(value), 'recorded_at': _stamp(when), 'include': True}
    # Different values at an identical known instant are not ordered by line position.
    if item['recorded_at']:
        dt, timed = date_parts(item['recorded_at'])
        for previous in out.data['readings']:
            if not previous['recorded_at']:
                continue
            pdt, ptimed = date_parts(previous['recorded_at'])
            if timed and ptimed and dt == pdt and previous['value'] != item['value']:
                raise ValueError('Conflicting observed SBS scores share a recording time. Check the source entries.')
    if item not in out.data['readings']:
        out.data['readings'].append(item)


def _matrix(lines: list[str], out: SBSResult) -> bool:
    """Explicit Lab/Units matrix, retaining its dated columns without backfill."""
    start = next((i for i, line in enumerate(lines) if re.match(r'^\s*Lab\s+Units\b', line, re.I)), None)
    if start is None:
        return False
    first = next((i for i in range(start + 1, len(lines)) if LABEL_FIND.search(lines[i]) and not TARGET.search(lines[i])), None)
    if first is None:
        return False
    # Reuse only the already-tested date header reader, not the gas data parser.
    from blood_gases import _headers
    try:
        stamps = _headers('\n'.join(lines[start:first]))
    except ValueError:
        raise ValueError('The SBS table dates or times could not be read. Copy the complete header.') from None
    for raw in lines[first:]:
        if not LABEL_FIND.search(raw) or TARGET.search(raw):
            continue
        cells = [s.strip() for s in raw.strip(' ').split('\t')] if '\t' in raw else re.split(r' {2,}', raw.strip())
        if not cells or not LABEL_ONLY.fullmatch(cells[0]):
            raise ValueError(ERROR)
        if len(cells) != len(stamps) + 2:
            raise ValueError('An SBS table row does not match its date columns. Preserve tabs and empty cells.')
        for when, value in zip(stamps, cells[2:]):
            _add(out, value, when)
    return True


def _dated_rows(lines: list[str], out: SBSResult) -> set[int]:
    """Vertical tables with explicit Date/Time and SBS column headings."""
    handled = set()
    header = None
    for i, raw in enumerate(lines):
        cells = [s.strip() for s in raw.split('\t')] if '\t' in raw else re.split(r' {2,}', raw.strip())
        labels = [c.casefold().rstrip(':') for c in cells]
        if len(cells) >= 2 and any(LABEL_ONLY.fullmatch(c) for c in cells) and any(re.search(r'\bdate\b|date/time', c, re.I) for c in cells):
            header = cells
            handled.add(i)
            continue
        if header is None or not raw.strip():
            continue
        if len(cells) != len(header) or not any(STAMP.search(c) for c in cells):
            continue
        value = cells[next(j for j, c in enumerate(header) if LABEL_ONLY.fullmatch(c))]
        dates = [cells[j] for j, c in enumerate(header) if re.search(r'\bdate\b|date/time|recorded|collected', c, re.I)]
        times = [cells[j] for j, c in enumerate(header) if c.casefold().strip() in {'time', 'recording time'}]
        _add(out, value, ' '.join(dates + times))
        handled.add(i)
    return handled


def parse_sbs(block: str) -> SBSResult:
    out = SBSResult()
    lines = block.replace('\r\n', '\n').replace('\r', '\n').replace('\u2212', '-').splitlines()
    target_context = False
    pending_when = ''
    pending_label = False
    try:
        # Targets remain editable separately and can never be selected as readings.
        for raw in lines:
            text = clean(raw)
            if TARGET.search(text) and (LABEL_FIND.search(text) or 'arousal level' in text.casefold()) and ':' in text:
                label, value = text.split(':', 1)
                if value.strip():
                    row = {'label': label.strip(), 'value': value.strip(), 'section': 'Neurologic', 'include': True}
                    if row not in out.targets:
                        out.targets.append(row)
        if not _matrix(lines, out):
            handled = _dated_rows(lines, out)
            for i, raw in enumerate(lines):
                if i in handled:
                    continue
                text = clean(raw)
                if not text or MISSING.fullmatch(text):
                    continue
                if TARGET.search(text) and (LABEL_FIND.search(text) or 'arousal level' in text.casefold()):
                    target_context = True
                    continue
                if re.fullmatch(r'(?:results? from|patient vitals? for|observations? (?:from|for)) (?:the )?(?:past|last) .+', text, re.I):
                    continue
                if re.fullmatch(r'(?:SBS observations|State Behavioral Scale|Last SBS|Recorded SBS|SBS)(?: \((?:past|last) 24 (?:hours|hrs)\))?:?', text, re.I):
                    target_context = False
                    pending_label = True
                    continue
                linked = re.fullmatch(r"(?:recorded at|recording time|date/time)\s*:\s*(.+)", text, re.I)
                if linked:
                    when = _stamp(linked[1])
                    if out.data['readings'] and not out.data['readings'][-1]['recorded_at']:
                        out.data['readings'][-1]['recorded_at'] = when
                    else:
                        pending_when = when
                    continue
                # A date/time on a separate line can label the following measurement.
                stamp = STAMP.fullmatch(text.strip('[]'))
                if stamp:
                    pending_when = stamp['date'] + (' ' + stamp['time'] if stamp['time'] else '')
                    continue
                has_label = bool(LABEL_FIND.search(text))
                explicit_observed = bool(re.search(r'\b(?:last|recorded|observed|actual)\b', text, re.I))
                stamp = STAMP.search(text)
                if has_label and target_context and not explicit_observed and not stamp:
                    # The historical Target Arousal Level heading also uses a bare SBS line.
                    out.targets.append({'label': 'Target Arousal Level (SBS)', 'value': text,
                                        'section': 'Neurologic', 'include': True})
                    continue
                if has_label or pending_label:
                    target_context = False
                    when = (stamp['date'] + (' ' + stamp['time'] if stamp['time'] else '')) if stamp else pending_when
                    value = text if not stamp else text[:stamp.start()] + text[stamp.end():]
                    value = re.sub(r'\b(?:last|recorded|observed|actual)\s*', '', value, flags=re.I)
                    for _ in range(4):
                        value = re.sub(r'^\s*' + LABEL + r'\s*:?\s*', '', value, flags=re.I)
                    value = re.sub(r'\b(?:at|on)\s*$', '', value, flags=re.I).strip(' :[]()|')
                    if MISSING.fullmatch(value):
                        pending_label = True
                        continue
                    _add(out, value, when)
                    pending_when, pending_label = '', False
                    continue
                if re.fullmatch(r'(?:date(?:/time)?|time|score|value|units|recorded at)(?:[ :|].*)?', text, re.I):
                    continue
                raise ValueError(ERROR)
        validate_sbs(out.data)
        if any(not r['recorded_at'] or not date_parts(r['recorded_at'])[1] for r in out.data['readings']):
            out.data['notes'].append(NO_TIME)
            out.issues.append(NO_TIME)
        if out.targets and not out.data['readings']:
            out.issues.append(TARGET_NOTE)
    except (ValueError, TypeError, IndexError):
        out.error = ERROR
        out.data = {'readings': [], 'notes': []}
    return out


def latest_sbs(data: dict | None, as_of: datetime | None = None) -> dict | None:
    validate_sbs(data)
    if data is None:
        return None
    now = clock(as_of).astimezone(timezone.utc)
    cutoff = now - timedelta(hours=24)
    candidates = []
    for row in data['readings']:
        if not row['include'] or not row['recorded_at']:
            continue
        recorded, timed = date_parts(row['recorded_at'])
        if not timed:
            continue
        instant = recorded.replace(tzinfo=EASTERN).astimezone(timezone.utc)
        # Ambiguous/nonexistent DST wall times cannot prove a most-recent reading.
        a = recorded.replace(tzinfo=EASTERN, fold=0)
        b = recorded.replace(tzinfo=EASTERN, fold=1)
        if a.utcoffset() != b.utcoffset():
            continue
        if cutoff <= instant <= now:
            candidates.append((instant, row))
    if not candidates:
        return None
    newest = max(t for t, _ in candidates)
    choices = [r for t, r in candidates if t == newest]
    if len({score(r['value']) for r in choices}) != 1:
        return None
    return choices[0]


def sbs_display_rows(sheet: dict, as_of: datetime | None = None) -> list[dict]:
    if 'k' in sheet.get('import_warnings', {}):
        return []
    row = latest_sbs(sheet.get('sbs_observations'), as_of)
    return [{'label': 'SBS', 'value': score(row['value']), 'section': 'Neurologic', 'include': True}] if row else []
