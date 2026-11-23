from collections import defaultdict

from app.receipts.clock import timepoint
from app.receipts.units import milligrams


def versions(rows):
    by_container=defaultdict(list)
    isolation=[]
    for row in rows:
        fields=row['data']
        try:
            start,end=(timepoint(fields[k]).isoformat() for k in ('start','end'))
            if end<=start:
                raise ValueError('TARE_RANGE')
            if not fields['container'].strip() or not fields['version'].strip():
                raise ValueError('BAD_KEY')
            weight=milligrams(fields['mass'],fields['unit'])
        except ValueError as error:
            isolation.append(row | {'code':str(error)})
            continue
        by_container[fields['container']].append((start,end,weight,row))
    return by_container,isolation


def weigh(tickets, tare_rows):
    configs, rejects=versions(tare_rows)
    matched, isolated=[],[]
    for row in tickets:
        fields=row['data']
        applicable=[(weight,source) for start,end,weight,source in configs[fields['container']] if start<=row['at']<end]
        base=row | {'tares':[source for _,source in applicable]}
        try:
            if not applicable:
                raise ValueError('TARE_MISSING')
            if len(applicable)>1:
                raise ValueError('TARE_OVERLAP')
            weight,_=applicable[0]
            gross=milligrams(fields['gross'],fields['unit'])
            base.update(gross_mg=gross,tare_mg=weight,net_mg=gross-weight)
            if gross<weight:
                raise ValueError('NEGATIVE_NET')
        except ValueError as error:
            isolated.append(base | {'code':str(error)})
            continue
        matched.append(base | {'code':'ACCEPTED'})
    return {'rows':matched,'isolated':isolated,'invalid_versions':rejects}
