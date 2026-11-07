"""Patient-free diagnostics and durable section-level import review flags.

Only allowlisted codes, field names and numeric source positions are retained.
No source text, clinical values, room identifiers or stack traces belong here.
"""
from __future__ import annotations

SECTIONS = {
    'a': 'Diagnoses', 'b': 'Medications', 'cd': 'Respiratory support',
    'e': 'Vitals', 'f': 'Cultures', 'g': 'Labs', 'i': 'Weight',
    'k': 'Arousal target', 'l': 'WAT', 'm': 'ICP / CPP', 'n': 'Admission',
    'o': 'Viral panel', 'p': 'Blood gas', 'q': 'CBC', 'r': 'Orders',
    's': 'Intake / output', 'document': 'Paste',
}
CODES = {
    'section_parse_failed': 'This section was not updated. Previous values are retained for review.',
    'section_boundary': 'Section boundaries were not reliable. This section was not updated.',
    'parser_exception': 'An unexpected parser problem occurred. This section was not updated.',
    'orders_count': 'The recurring-order occurrence count could not be read reliably. The R section was skipped.',
    'orders_timing': 'Conflicting recurring-order schedules were supplied. The R section was skipped.',
    'orders_structure': 'The R section did not match the supported order structure. It was skipped.',
    'orders_skipped': 'Orders were not imported. The previous automatic order list is hidden from the handoff until reviewed.',
    'cbc_multiple_values': 'More than one result occupies this CBC cell. The ambiguous cell is excluded, not guessed.',
    'cbc_invalid_cell': 'A CBC cell could not be read. That cell was omitted.',
    'cbc_row_columns': 'A CBC row did not match the dated columns. That row was omitted.',
    'cbc_conflict': 'Conflicting CBC results were excluded from the affected cell.',
    'cbc_percentage': 'A percentage-labelled row was omitted from absolute counts.',
    'document_rejected': 'The paste could not be assigned safely to one handoff. Nothing was changed.',
}
FIELDS = {'', 'WBC', 'HGB', 'HGB_ISTAT', 'HCT', 'HCT_ISTAT', 'MCV', 'PLT', 'ANC', 'ALC'}
ACTIONS = {'not_updated', 'orders_hidden', 'cell_omitted', 'row_omitted', 'nothing_changed'}


def diagnostic(section: str, code: str, *, line: int = 0, column: int = 0,
               field: str = '', action: str = 'not_updated') -> dict:
    value = dict(section=section, code=code, line=line, column=column, field=field, action=action)
    validate_diagnostic(value)
    return value


def validate_diagnostic(value: dict) -> None:
    if not isinstance(value, dict) or set(value) != {'section', 'code', 'line', 'column', 'field', 'action'}:
        raise ValueError('The import diagnostic has an invalid structure.')
    if (value['section'] not in SECTIONS or value['code'] not in CODES
            or value['field'] not in FIELDS or value['action'] not in ACTIONS):
        raise ValueError('The import diagnostic contains an unsupported code.')
    for key in ('line', 'column'):
        if type(value[key]) is not int or not 0 <= value[key] <= 150000:
            raise ValueError('The import diagnostic source position is invalid.')


def validate_import_warnings(value: dict) -> None:
    if not isinstance(value, dict) or len(value) > len(SECTIONS):
        raise ValueError('Import review flags are invalid.')
    for section, items in value.items():
        if section not in SECTIONS or not isinstance(items, list) or not 1 <= len(items) <= 100:
            raise ValueError('An import review flag is invalid.')
        for item in items:
            validate_diagnostic(item)
            if item['section'] != section:
                raise ValueError('An import review flag does not match its section.')


def diagnostic_text(item: dict) -> str:
    validate_diagnostic(item)
    position = (' | line ' + str(item['line']) if item['line'] else '')
    position += (' | column ' + str(item['column']) if item['column'] else '')
    field = (' | ' + item['field']) if item['field'] else ''
    return SECTIONS[item['section']] + field + position + ': ' + CODES[item['code']] + (' Previous automatic orders are hidden from print.' if item['action'] == 'orders_hidden' and item['code'] != 'orders_skipped' else '')


def review_summary(sheet: dict) -> str:
    parts = []
    for section, items in sheet.get('import_warnings', {}).items():
        if section == 'r':
            note = 'orders skipped; prior list hidden'
        elif any(item['action'] == 'not_updated' for item in items):
            note = 'not updated; verify retained values'
        else:
            note = 'incomplete; some results omitted'
        parts.append(SECTIONS[section] + ': ' + note)
    return 'IMPORT REVIEW: ' + ' | '.join(parts) if parts else ''


def orders_for_output(sheet: dict):
    return None if 'r' in sheet.get('import_warnings', {}) else sheet.get('recurring_orders')
