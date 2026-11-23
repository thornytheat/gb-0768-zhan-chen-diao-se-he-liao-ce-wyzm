from collections import Counter, defaultdict

from app.blend.claims import declared

FLOW = {'OPEN': 'opening_mg', 'ISSUE': 'issued_mg', 'APPLY': 'applied_mg',
        'LOSS': 'loss_mg', 'RETURN': 'returned_mg'}
MASS_FIELDS = (*FLOW.values(), 'disputed_mg')


def _line_ranges(blend, lot):
    """该批号在各可行先后下的逐项区间；无区间时退回逐票实数。"""
    spans = blend.get('flow_ranges', {}).get(lot, {})
    return {field: list(spans[field]) if field in spans else None for field in MASS_FIELDS}


def _claim_code(claim, low, high):
    """申报与回桶的对照。

    区间跨过申报值时，只能交代“申报落在可行区间”，不签 MATCH：否则就把
    猜到的某一种配比当成了实数。
    """
    if claim is None:
        return 'NO_CLAIM', None, None
    if low is None:
        return 'MISMATCH', None, None
    if low == high:
        delta = low - claim
        return ('MATCH' if delta == 0 else 'MISMATCH'), delta, [delta, delta]
    span = [low - claim, high - claim]
    if span[0] <= 0 <= span[1]:
        return 'UNCERTAIN', None, span
    delta = span[0] if span[0] > 0 else span[1]
    return 'MISMATCH', delta, span


def settle(blend, notes):
    flows = defaultdict(Counter)
    for row in blend['rows']:
        for lot, amount in row['parts_mg'].items():
            flows[lot][FLOW[row['data']['action']]] += amount
    for pot in blend['pending_mg'].values():
        for lot, amount in pot.items():
            flows[lot]['disputed_mg'] += amount
    claims, invalid = declared(notes)
    lines = []
    for lot in sorted(flows.keys() | claims.keys()):
        values = {key: flows[lot][key] for key in MASS_FIELDS}
        evidence = claims[lot]
        declared_masses = {row['declared_mg'] for row in evidence}
        claim = next(iter(declared_masses)) if len(declared_masses) == 1 else None
        spans = _line_ranges(blend, lot)
        range_mg = {}
        for field in MASS_FIELDS:
            span = spans[field]
            if span is None or span[0] == span[1]:
                range_mg[field] = [values[field], values[field]]
            else:
                range_mg[field] = span
        uncertain = {field: span[1] - span[0] for field, span in range_mg.items()
                     if span[1] > span[0]}
        if len(declared_masses) > 1:
            code, delta, delta_span = 'CLAIM_CONFLICT', None, None
        else:
            code, delta, delta_span = _claim_code(claim, *range_mg['returned_mg'])
        checks = blend.get('imbalance_mg', {}).get(lot)
        check_span = list(checks) if checks else [0, 0]
        lines.append({'lot': lot, **values,
                      'range_mg': range_mg, 'uncertain_mg': uncertain,
                      'provisional': bool(uncertain),
                      'claimed_mg': claim, 'difference_mg': delta,
                      'difference_range_mg': delta_span,
                      'code': code, 'receipts': evidence,
                      'check_mg': values['opening_mg'] + values['issued_mg']
                                  - sum(values[k] for k in MASS_FIELDS[2:]),
                      'check_range_mg': check_span})
    totals = {key: sum(r[key] for r in lines) for key in MASS_FIELDS}
    # 各罐独立复算，合计区间由逐个可行方案相加得到，不能把各批号的端点拼起来。
    joint = blend.get('totals_range_mg') or {}
    totals_range = {key: [joint[key][0] if key in joint else totals[key],
                          joint[key][1] if key in joint else totals[key]]
                    for key in MASS_FIELDS}
    return {'lines': lines, 'invalid_receipts': invalid, 'totals': totals,
            'totals_range_mg': totals_range,
            'difference_lines': sum(r['code'] in ('MISMATCH', 'CLAIM_CONFLICT', 'NO_CLAIM')
                                    for r in lines),
            'uncertain_lines': sum(r['code'] == 'UNCERTAIN' for r in lines),
            'provisional': any(r['provisional'] for r in lines),
            'ambiguous': bool(blend.get('ambiguous')),
            'ambiguity': list(blend.get('ambiguity', [])),
            'scenarios': blend.get('scenarios', {}),
            'truncated': bool(blend.get('truncated'))}
