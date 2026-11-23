from collections import defaultdict

from app.receipts.units import milligrams


def declared(rows):
    claims=defaultdict(list)
    invalid=[]
    for row in rows:
        fields=row['data']
        try:
            if not fields['lot'].strip() or not fields['receipt'].strip():
                raise ValueError('BAD_KEY')
            amount=milligrams(fields['mass'],fields['unit'])
        except ValueError as error:
            invalid.append(row | {'code':str(error)})
            continue
        claims[fields['lot']].append(row | {'declared_mg':amount})
    return claims,invalid
