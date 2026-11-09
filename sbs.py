"""Observed State Behavioral Scale readings, separate from prescribed targets.

Timestamped observations are filtered to a rolling 24-hour window. The explicit
Epic field "SBS Last 24 Hours" is a separately stored, source-filtered snapshot.
Its report time is NOT a measurement time. "Last SBS Ever" is never a fallback.
An explicitly labelled target keeps a target label. UTC arithmetic makes the
rolling window independent of daylight-saving transitions.

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
    if not isinstance(data, dict) or set(data) - {'source_window'} != {'readings', 'notes'}:
        raise ValueError('The observed SBS record has an invalid structure.')
    if 'source_window' in data:
        validate_source_window(data['source_window'])
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


def _parse_legacy_sbs(block: str) -> SBSResult:
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
    data = sheet.get('sbs_observations')
    validate_sbs(data)
    window = (data or {}).get('source_window')
    if window is not None and not window['include']:
        return []
    row = latest_sbs(data, as_of)
    label = 'SBS target' if window and window['kind'] == 'target' else 'SBS'
    if row:
        value = score(row['value'])
    elif window is not None:
        # An undated source-filtered value is only a snapshot. Never stamp it as
        # a measured reading, and do not extend its age on save or room changes.
        reported = datetime.fromisoformat(window['reported_as_of']).astimezone(timezone.utc)
        now = clock(as_of).astimezone(timezone.utc)
        value = window['value'] if timedelta(0) <= now - reported <= timedelta(hours=24) else ''
        if not value:
            label, value = 'SBS', 'None'
    else:
        return []
    return [{'label': label, 'value': value, 'section': 'Neurologic', 'include': True}]


# The explicit window label is authoritative even when its content is empty.
# Horizontal whitespace only: a blank recent field must not consume the next line.
RECENT_FIELD = re.compile(r'(?im)^[ \t]*(?:SBS[ \t]+(?:Last|Past)[ \t]+24[ \t]*(?:Hours?|Hrs?)|(?:Last|Past)[ \t]+24[ \t]*(?:Hours?|Hrs?)[ \t]+SBS)[ \t]*:')
EVER_FIELD = re.compile(r'(?i)\bLast[ \t]+SBS[ \t]+Ever[ \t]*:')


def validate_source_window(value: dict) -> None:
    if not isinstance(value, dict) or set(value) != {'value', 'reported_as_of', 'reference', 'kind', 'include'}:
        raise ValueError('The source-filtered SBS snapshot has an invalid structure.')
    if not isinstance(value['value'], str) or (value['value'] and score(value['value']) != value['value']):
        raise ValueError('The source-filtered SBS score is invalid.')
    if value['reference'] not in ('smartphrase', 'import') or value['kind'] not in ('score', 'target') or type(value['include']) is not bool:
        raise ValueError('The source-filtered SBS metadata is invalid.')
    if not isinstance(value['reported_as_of'], str) or len(value['reported_as_of']) > 80:
        raise ValueError('The SBS snapshot time is invalid.')
    try:
        when = datetime.fromisoformat(value['reported_as_of'])
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('The SBS snapshot time must include a timezone.') from None


def snapshot_reference(blocks: dict) -> tuple[datetime, str]:
    """Use a printed SmartPhrase snapshot time, never an observation time.

    The S summary is the user's primary I/O block. H remains a legacy fallback.
    This is only used for an explicitly source-filtered SBS field.
    """
    for key in ('s', 'h'):
        for line in blocks.get(key, '').splitlines():
            match = re.search(r'^\s*Intake/Output Summary.*?\bat\s+(' + DATE + r'\s+' + TIME + r')\s*$', line, re.I)
            if not match:
                continue
            try:
                when, timed = date_parts(match[1])
                if timed:
                    a, b = when.replace(tzinfo=EASTERN, fold=0), when.replace(tzinfo=EASTERN, fold=1)
                    if a.utcoffset() == b.utcoffset():
                        return a, 'smartphrase'
            except ValueError:
                pass
    return clock(), 'import'


def parse_sbs(block: str, *, window_as_of: datetime | None = None,
              window_reference: str = 'import') -> SBSResult:
    """Read the user's K structure without historical fallback or invented times."""
    source = block.replace('\r\n', '\n').replace('\r', '\n').replace('：', ':')
    recent = list(RECENT_FIELD.finditer(source))
    ever = EVER_FIELD.search(source)
    if not recent and not ever:
        return _parse_legacy_sbs(source)
    out = SBSResult()
    try:
        if len(recent) > 1:
            raise ValueError('More than one last-24-hour SBS field was supplied.')
        if recent:
            start = recent[0].end()
            following_ever = EVER_FIELD.search(source, start)
            body = source[start:following_ever.start() if following_ever else len(source)]
        else:
            # A historical-only field cannot refresh any current SBS display.
            body = ''
        window = {'value': '', 'reported_as_of': clock(window_as_of).astimezone(timezone.utc).isoformat(),
                  'reference': window_reference, 'kind': 'score', 'include': True}
        out.data['source_window'] = window
        body = body.strip()
        if not body or MISSING.fullmatch(clean(body)):
            validate_sbs(out.data)
            return out

        # Epic may insert its full nested field label. Do not turn a documented
        # target into an observed score. It is eligible by the window, but remains
        # explicitly labelled "SBS target" in the output and editor.
        target_lines = [line for line in body.splitlines() if TARGET.search(line)]
        if target_lines:
            window['kind'] = 'target'
            body = re.sub(r'(?im)^[ \t]*(?:Target Arousal Level(?:[ \t]*\(SBS\))?|(?:Target|Goal|Desired)[ \t]+SBS)[ \t]*:[ \t]*', '', body)
            if TARGET.search(body):
                raise ValueError('Unrecognized target label in the SBS 24-hour field.')
        parsed = _parse_legacy_sbs('SBS observations:\n' + body)
        if parsed.error:
            raise ValueError(parsed.error)
        readings = parsed.data['readings']
        timed = [r for r in readings if r['recorded_at'] and date_parts(r['recorded_at'])[1]]
        undated = [r for r in readings if not r['recorded_at']]
        date_only = [r for r in readings if r['recorded_at'] and not date_parts(r['recorded_at'])[1]]
        if (timed and (undated or date_only)) or (undated and date_only):
            raise ValueError('Mixed timed and untimed SBS readings cannot establish a latest result.')
        if timed:
            out.data['readings'] = timed
        elif date_only:
            # Keep explicit date-only history for editing, without bypassing it
            # based only on the "24 hours" label.
            out.data['readings'] = date_only
            out.data['notes'] = list(parsed.data['notes'])
            out.issues = list(parsed.issues)
        elif undated:
            values = {score(r['value']) for r in undated}
            if len(values) != 1:
                raise ValueError('Multiple untimed SBS scores need recording times to select the latest.')
            window['value'] = values.pop()
        validate_sbs(out.data)
    except (ValueError, TypeError, IndexError):
        out.error = 'The SBS Last 24 Hours field could not be read safely. Last SBS Ever was not used.'
        out.data = {'readings': [], 'notes': []}
    return out
