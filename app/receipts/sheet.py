import csv
from io import StringIO

from app.faults import LedgerError
from app.receipts.contract import COLUMNS


def scan(text, sheet):
    records, issues = [], []
    headers = COLUMNS[sheet].split(',')
    reader = csv.reader(StringIO(text.removeprefix('\ufeff'), newline=''), strict=True)
    count = repeats = 0
    try:
        first = next(reader, None)
        if first is None:
            raise LedgerError('EMPTY_SHEET', f'{sheet} 原件缺表头')
        if len(first) != len(headers) or set(first) != set(headers):
            raise LedgerError('HEADER_INVALID', f'{sheet} 的列与定义不符')
        while True:
            line = reader.line_num + 1
            raw = next(reader, None)
            if raw is None:
                break
            count += 1
            evidence = {'sheet':sheet,'line':line,'raw':raw}
            if raw == first:
                repeats += 1
            elif not any(cell.strip() for cell in raw):
                issues.append(evidence | {'code':'BLANK'})
            elif len(raw) != len(first):
                issues.append(evidence | {'code':'WIDTH'})
            else:
                records.append(evidence | {'data':dict(zip(first,raw,strict=True))})
    except csv.Error:
        raise LedgerError('CSV_INVALID', f'{sheet} 第 {reader.line_num} 行引号错误') from None
    return records, {'sheet':sheet,'submitted':count,'parsed':len(records),'repeated_headers':repeats,
                     'isolated':issues,'state':'rows' if records else 'blank_rows' if count else 'header_only'}
