from collections import Counter, defaultdict

from app.blend.claims import declared

FLOW={'OPEN':'opening_mg','ISSUE':'issued_mg','APPLY':'applied_mg','LOSS':'loss_mg','RETURN':'returned_mg'}
MASS_FIELDS=(*FLOW.values(),'disputed_mg')


def settle(blend, notes):
    flows=defaultdict(Counter)
    for row in blend['rows']:
        for lot, amount in row['parts_mg'].items():
            flows[lot][FLOW[row['data']['action']]]+=amount
    for pot in blend['pending_mg'].values():
        for lot, amount in pot.items():
            flows[lot]['disputed_mg']+=amount
    claims,invalid=declared(notes)
    lines=[]
    for lot in sorted(flows.keys()|claims.keys()):
        values={key:flows[lot][key] for key in MASS_FIELDS}
        evidence=claims[lot]
        declared_masses={row['declared_mg'] for row in evidence}
        claim=next(iter(declared_masses)) if len(declared_masses)==1 else None
        delta=None if claim is None else values['returned_mg']-claim
        code=('CLAIM_CONFLICT' if len(declared_masses)>1 else 'NO_CLAIM' if claim is None
              else 'MATCH' if delta==0 else 'MISMATCH')
        lines.append({'lot':lot, **values, 'claimed_mg':claim,'difference_mg':delta,'code':code,'receipts':evidence,
                      'check_mg':values['opening_mg']+values['issued_mg']-sum(values[k] for k in MASS_FIELDS[2:])})
    return {'lines':lines,'invalid_receipts':invalid,'totals':{key:sum(r[key] for r in lines) for key in MASS_FIELDS},
            'difference_lines':sum(r['code']!='MATCH' for r in lines)}
