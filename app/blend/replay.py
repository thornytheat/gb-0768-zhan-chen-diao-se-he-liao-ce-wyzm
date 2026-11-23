"""按批号回分回桶料。

旧秤只记到分钟：同一罐、同一分钟内的入罐（期初／领用）与出罐（上件／
损耗／回桶）分不清先后。先算领用再算上件，会把同刻新入罐的料算进更早的
上件；把整罐压着不摊，又交不出实称用量。

所以这里不替原件挑一种先后：同一分钟的可行先后全部保留，每一次分摊都
落在可行区间内，后续出罐也按全部可行方案复算，不把猜到的配比当成实数。
基准方案先把罐内既有料出完再入罐——它是不把新料算进前一件的那一端，
只用于交代实数，不被当成唯一真相。
"""

from collections import defaultdict
from itertools import groupby

from app.blend.share import split_mass
from app.receipts.contract import ACTIONS

INBOUND = frozenset({'OPEN', 'ISSUE'})
FLOW = {'OPEN': 'opening_mg', 'ISSUE': 'issued_mg', 'APPLY': 'applied_mg',
        'LOSS': 'loss_mg', 'RETURN': 'returned_mg'}
MASS_FIELDS = (*FLOW.values(), 'disputed_mg')
CHECKED = ('opening_mg', 'issued_mg')
MAX_ORDERS = 256
MAX_RUNS = 256
EXPANSION_BUDGET = 4096


def _moment(index, step):
    """记录时刻；旧秤只到分钟，同一分钟内的记录无法再分先后。

    没有 `at` 的原件（旧调用方）按登记位置各自成组，保持原有先后。
    """
    at = step.get('at')
    return ('at', at[:16]) if at is not None else ('line', index)


def _baseline(group):
    """同一分钟内的登记次序；期初/领用在前，同种动作按票号。"""
    return tuple(sorted(group, key=lambda step: (
        ACTIONS.index(step['data']['action']), step['data']['ticket'])))


def _orders(group):
    """同一分钟内的可行先后。

    同分钟里真正分不清的是“新料入罐”与“从罐里取料”谁在前；入罐与出罐
    各自内部的登记次序由期初／领用、上件／损耗／回桶的先后给出，不必再翻。
    所以对两条序列做全部交错：第一序先把出罐排完，作为“不把新料算进前
    一件”的基准；另一种“先入罐再出罐”也保留为可行方案。整分钟只有单一
    方向时，次序唯一。
    """
    base = _baseline(group)
    inbound = [step for step in base if step['data']['action'] in INBOUND]
    outbound = [step for step in base if step['data']['action'] not in INBOUND]
    if not inbound or not outbound:
        return [base], False
    orders, truncated = [], [False]

    def walk(i, j, chosen):
        if len(orders) >= MAX_ORDERS:
            truncated[0] = True
            return
        if i == len(inbound) and j == len(outbound):
            orders.append(tuple(chosen))
            return
        if j < len(outbound):
            walk(i, j + 1, chosen + [outbound[j]])
        if i < len(inbound):
            walk(i + 1, j, chosen + [inbound[i]])

    walk(0, 0, [])
    if truncated[0]:
        # 全交错被截断时，补上另一端“先入罐后出罐”，保证区间两端都在。
        mirror = tuple(inbound + outbound)
        if mirror not in orders:
            orders.append(mirror)
    return orders, truncated[0]


def _new_run():
    return {'stock': {}, 'prov': {}, 'rows': {}, 'isolated': []}


def _clone(run):
    return {'stock': dict(run['stock']),
            'prov': {lot: list(lines) for lot, lines in run['prov'].items()},
            'rows': dict(run['rows']), 'isolated': list(run['isolated'])}


def _signature(run):
    return (tuple(sorted((lot, mass) for lot, mass in run['stock'].items() if mass)),
            tuple(sorted((lot, tuple(lines)) for lot, lines in run['prov'].items() if lines)),
            tuple(sorted((line, tuple(sorted(evidence['parts_mg'].items())))
                         for line, evidence in run['rows'].items())),
            tuple(sorted((row['line'], row.get('code')) for row in run['isolated'])))


def _dedupe(runs):
    seen, unique = set(), []
    for run in runs:
        key = _signature(run)
        if key not in seen:
            seen.add(key)
            unique.append(run)
    return unique


def _execute(run, step):
    action = step['data']['action']
    net = step['net_mg']
    stock = run['stock']
    before = dict(stock)
    if action in INBOUND:
        lot = step['lot']
        parts = {lot: net}
        stock[lot] = stock.get(lot, 0) + net
        run['prov'].setdefault(lot, []).append(step['line'])
        lines = {lot: list(run['prov'][lot])}
    else:
        if net > sum(stock.values()):
            return False
        parts = split_mass(net, stock)
        prior = {lot: list(lines) for lot, lines in run['prov'].items()}
        for lot, amount in parts.items():
            stock[lot] -= amount
            if stock[lot] == 0:
                run['prov'][lot] = []
        lines = {lot: prior.get(lot, []) for lot in parts}
    run['rows'][step['line']] = step | {'before_mg': before, 'parts_mg': parts,
                                        'after_mg': dict(stock), 'issue_lines': lines}
    return True


def _fallback(run, order):
    """整分钟没有任何可行先后时，沿基准次序逐票隔离超用票，保持现存量。"""
    candidate = _clone(run)
    for step in order:
        if (step['data']['action'] not in INBOUND
                and step['net_mg'] > sum(candidate['stock'].values())):
            candidate['isolated'].append(step | {'code': 'OVERDRAW',
                                                 'before_mg': dict(candidate['stock'])})
            continue
        _execute(candidate, step)
    return candidate


def _replay(steps):
    sequenced = sorted(enumerate(steps),
                       key=lambda item: (_moment(*item),
                                         ACTIONS.index(item[1]['data']['action']),
                                         item[1]['data']['ticket']))
    runs, moments, truncated = [_new_run()], [], False
    for moment, grouped in groupby(sequenced, key=lambda item: _moment(*item)):
        group = [step for _, step in grouped]
        orders, capped = _orders(group)
        truncated = truncated or capped
        # 方案数乘以已有状态数可能很大；按状态均分预算，避免只展开前几个状态。
        share = max(1, EXPANSION_BUDGET // max(1, len(runs)))
        chosen = orders
        if share < len(orders):
            truncated = True
            # 截断时保住基准端与另一端，区间才不会只剩一侧。
            chosen = (orders[:share - 1] + [orders[-1]]) if share > 1 else orders[:1]
        expanded, viable = [], 0
        for run in runs:
            feasible = 0
            for order in chosen:
                candidate = _clone(run)
                if all(_execute(candidate, step) for step in order):
                    expanded.append(candidate)
                    feasible += 1
            if feasible:
                viable = max(viable, feasible)
            else:
                # 这一状态下填不出任何可行先后：逐票隔离超用票，其余照基准。
                expanded.append(_fallback(run, orders[0]))
        if viable > 1:
            moments.append({'minute': moment[1],
                            'lines': sorted(step['line'] for step in group)})
        runs = _dedupe(expanded)
        if len(runs) > MAX_RUNS:
            truncated = True
            # 抽稀时保住最后一个方案：截断前 _orders 把“先入罐后出罐”的
            # 另一端补在了末尾，丢掉它会只剩区间一侧。
            runs = runs[:MAX_RUNS - 1] + [runs[-1]]
    return runs, moments, truncated


def _flows(run):
    flows = defaultdict(lambda: defaultdict(int))
    for evidence in run['rows'].values():
        field = FLOW[evidence['data']['action']]
        for lot, amount in evidence['parts_mg'].items():
            flows[lot][field] += amount
    for lot, amount in run['stock'].items():
        if amount:
            flows[lot]['disputed_mg'] += amount
    return flows


def _imbalance(flows):
    """逐批号勾稽差额：期初 + 领用 − 其余各项；每个可行方案都应为零。"""
    return {lot: sum(amount.get(key, 0) for key in CHECKED)
            - sum(amount.get(key, 0) for key in MASS_FIELDS[2:])
            for lot, amount in flows.items()}


def _span(values):
    keys = set().union(*(value.keys() for value in values)) if values else set()
    return {key: [min(value.get(key, 0) for value in values),
                  max(value.get(key, 0) for value in values)] for key in keys}


def _split(span):
    """把区间拆成 range/min/max 三份别名，便于收据与页面各取所需。"""
    return ({lot: list(pair) for lot, pair in span.items()},
            {lot: pair[0] for lot, pair in span.items()},
            {lot: pair[1] for lot, pair in span.items()})


def rebuild(records):
    pots = defaultdict(list)
    for row in records:
        pots[row['data']['pot']].append(row)
    rows_by_line, isolated_by_line = {}, {}
    pending, pending_span = {}, {}
    flow_ranges = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    totals_range = {field: [0, 0] for field in MASS_FIELDS}
    imbalance = defaultdict(lambda: [0, 0])
    scenarios, ambiguity = {}, []
    ambiguous = truncated = False
    for pot, steps in sorted(pots.items()):
        runs, moments, capped = _replay(steps)
        truncated = truncated or capped
        scenarios[pot] = len(runs)
        canonical = runs[0]
        rows_by_line.update(canonical['rows'])
        isolated_by_line.update({row['line']: row for row in canonical['isolated']})
        pending[pot] = {lot: mass for lot, mass in canonical['stock'].items() if mass}
        stock_span = _span([run['stock'] for run in runs])
        pending_span[pot] = {lot: span for lot, span in stock_span.items() if span[1]}
        if any(span[0] != span[1] for span in pending_span[pot].values()):
            ambiguous = True
        uncertain_lines = set()
        for line, evidence in canonical['rows'].items():
            span = _span([run['rows'].get(line, {}).get('parts_mg', {}) for run in runs])
            ranges, lows, highs = _split(span)
            uncertain = {lot: high - low for lot, (low, high) in span.items() if high > low}
            evidence.update(parts_range_mg={lot: rng for lot, rng in ranges.items() if rng[1]},
                            parts_min_mg=lows, parts_max_mg=highs,
                            uncertain_mg=uncertain, provisional=bool(uncertain))
            if uncertain:
                uncertain_lines.add(line)
        # 某些先后下这一票可行、另一些下超用时，也不得只挑一种说法交出去。
        for other in runs[1:]:
            for line in other['rows'].keys() - canonical['rows'].keys():
                if line in isolated_by_line:
                    row = isolated_by_line[line]
                    row.update(order_ambiguous=True, provisional=True)
                    ambiguity.append({'pot': pot, 'lines': [line],
                                      'scenarios': len(runs), 'code': 'ORDER_AMBIGUOUS'})
                    ambiguous = True
            for line in canonical['rows'].keys() - other['rows'].keys():
                evidence = canonical['rows'][line]
                if line not in uncertain_lines:
                    evidence.update(order_ambiguous=True, provisional=True)
                    uncertain_lines.add(line)
                    ambiguity.append({'pot': pot, 'lines': [line],
                                      'scenarios': len(runs), 'code': 'ORDER_AMBIGUOUS'})
                    ambiguous = True
        for entry in moments:
            if not uncertain_lines.intersection(entry['lines']):
                continue
            ambiguity.append(entry | {'pot': pot, 'scenarios': len(runs)})
            for line in entry['lines']:
                if line in canonical['rows']:
                    canonical['rows'][line]['order_ambiguous'] = True
        ambiguous = ambiguous or bool(uncertain_lines)
        pot_flows = [_flows(run) for run in runs]
        lots = set().union(*(flows.keys() for flows in pot_flows))
        for lot in lots:
            for field in MASS_FIELDS:
                values = [flows.get(lot, {}).get(field, 0) for flows in pot_flows]
                if any(values):
                    flow_ranges[lot][field][0] += min(values)
                    flow_ranges[lot][field][1] += max(values)
            checks = [_imbalance(flows).get(lot, 0) for flows in pot_flows]
            imbalance[lot][0] += min(checks)
            imbalance[lot][1] += max(checks)
        for field in MASS_FIELDS:
            values = [sum(flows[lot].get(field, 0) for lot in flows) for flows in pot_flows]
            totals_range[field][0] += min(values)
            totals_range[field][1] += max(values)
    rows = [rows_by_line[row['line']] for row in records if row['line'] in rows_by_line]
    isolated = [isolated_by_line[row['line']] for row in records if row['line'] in isolated_by_line]
    pending_ranges, pending_min, pending_max = {}, {}, {}
    for pot, span in pending_span.items():
        ranges, lows, highs = _split(span)
        pending_ranges[pot], pending_min[pot], pending_max[pot] = ranges, lows, highs
    unique, seen = [], set()
    for entry in ambiguity:
        key = (entry.get('pot'), entry.get('minute'), entry.get('code'),
               tuple(entry.get('lines', ())))
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return {'rows': rows, 'isolated': isolated,
            'pending_mg': pending, 'pending_range_mg': pending_ranges,
            'pending_min_mg': pending_min, 'pending_max_mg': pending_max,
            'scenarios': scenarios, 'ambiguity': unique,
            'ambiguous': ambiguous, 'truncated': truncated,
            'totals_range_mg': totals_range,
            'flow_ranges': {lot: {field: list(span) for field, span in spans.items()}
                            for lot, spans in flow_ranges.items()},
            'imbalance_mg': {lot: list(span) for lot, span in imbalance.items()}}
