from hashlib import sha256

from app.faults import LedgerError
from app.ledger.identity import encoded
from app.receipts.packet import checksums

FIELDS = ('opening_mg', 'issued_mg', 'applied_mg', 'loss_mg', 'returned_mg', 'disputed_mg')


def _verify(report, recovery=None):
    """逐批号重算勾稽，并要求区间里确实含有已签发的实数。

    同分钟先后不定时，实数只是基准方案的一端；还要核对它确实落在区间内，
    且每个可行方案都勾稽平，避免把猜到的配比签成唯一实数。
    """
    for row in report['lines']:
        check = row['opening_mg'] + row['issued_mg'] - sum(row[field] for field in FIELDS[2:])
        if check != 0:
            raise LedgerError('MASS_UNBALANCED', '至少一个成分重量不平', 409)
        spans = row.get('range_mg', {})
        for field in FIELDS:
            span = spans.get(field)
            if span is not None and not span[0] <= row[field] <= span[1]:
                raise LedgerError('MASS_UNBALANCED', '签发的实数落在可行区间之外', 409)
        span = row.get('check_range_mg')
        if span is not None and not span[0] <= 0 <= span[1]:
            raise LedgerError('MASS_UNBALANCED', '至少一个成分重量不平', 409)
    for row in (recovery or {}).get('rows', []):
        spans = row.get('parts_range_mg') or {}
        for lot, amount in row.get('parts_mg', {}).items():
            span = spans.get(lot)
            if span is not None and not span[0] <= amount <= span[1]:
                raise LedgerError('MASS_UNBALANCED', '签发的分摊落在可行区间之外', 409)


def _uncertainty(report, recovery=None):
    """把同刻先后不定的部分提出来，收据要能交代这些重量并非实数。"""
    lines = []
    for row in report['lines']:
        spans = {field: span for field, span in row.get('range_mg', {}).items()
                 if span[1] > span[0]}
        if row.get('provisional') or spans:
            lines.append({'lot': row['lot'], 'code': row['code'],
                          'range_mg': spans,
                          'claimed_mg': row['claimed_mg'],
                          'difference_mg': row['difference_mg'],
                          'difference_range_mg': row.get('difference_range_mg')})
    rows = [{'line': row['line'], 'pot': row['data']['pot'], 'ticket': row['data']['ticket'],
             'action': row['data']['action'], 'before_mg': row.get('before_mg'),
             'parts_mg': row.get('parts_mg'), 'parts_range_mg': row.get('parts_range_mg'),
             'uncertain_mg': row.get('uncertain_mg', {}),
             'order_ambiguous': row.get('order_ambiguous', False)}
            for row in (recovery or {}).get('rows', [])
            if row.get('provisional') or row.get('uncertain_mg')]
    return {'provisional': bool(lines), 'lines': lines,
            'totals_range_mg': {field: span for field, span in
                                report.get('totals_range_mg', {}).items() if span[1] > span[0]},
            'recovery': rows,
            'ambiguity': report.get('ambiguity', []),
            'scenarios': report.get('scenarios', {}),
            'truncated': bool(report.get('truncated'))}


def certify(record):
    if checksums(record['sheets']) != record['manifest']['files']:
        raise LedgerError('HASH_DISAGREEMENT', '原件与收据摘要不一致', 409)
    report = record['snapshot']['balance']
    recovery = record['snapshot'].get('recovery')
    _verify(report, recovery)
    uncertainty = _uncertainty(report, recovery)
    return {'document': '调色收据证据', 'sha256': sha256(encoded(record)).hexdigest(),
            'key': record['manifest']['key'], 'mass_check_mg': 0,
            'uncertainty': uncertainty, **record}
