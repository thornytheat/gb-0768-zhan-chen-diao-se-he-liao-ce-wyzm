from collections import defaultdict
import unicodedata


def normalize(alias):
    return unicodedata.normalize('NFKC',alias).strip().casefold()


def identify(records, catalog):
    index=defaultdict(list)
    rejected=[]
    for row in catalog:
        fields=row['data']
        alias=normalize(fields['alias'])
        if not alias or not fields['lot'].strip() or not fields['pigment'].strip():
            rejected.append(row | {'code':'BAD_KEY'})
        else:
            index[alias].append(row)
    rows,isolated=[],[]
    for row in records:
        data=row['data']
        alias=normalize(data['lot'])
        inbound=data['action'] in {'OPEN','ISSUE'}
        contenders=index[alias] if inbound else []
        pairs={(r['data']['lot'],r['data']['pigment']) for r in contenders}
        base=row | {'lot_sources':contenders}
        if inbound and len(pairs)!=1:
            isolated.append(base | {'code':'LOT_CONFLICT' if pairs else 'LOT_UNKNOWN'})
        elif not inbound and alias:
            isolated.append(base | {'code':'MIXED_OUTPUT'})
        else:
            lot,pigment=next(iter(pairs)) if inbound else (None,None)
            rows.append(base | {'lot':lot,'pigment':pigment})
    return {'rows':rows,'isolated':isolated,'invalid_catalog':rejected}
