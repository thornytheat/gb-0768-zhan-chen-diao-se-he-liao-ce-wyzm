import re
import unicodedata
from decimal import Decimal

SCALES = {'kg': 1_000_000, 'g': 1000, 'mg': 1}
SENTINELS = {'', '-', 'NULL', 'N/A', '未知'}
FORM = re.compile(r'[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,6})?')


def milligrams(raw, unit):
    raw = unicodedata.normalize('NFKC', raw).strip()
    unit = unicodedata.normalize('NFKC', unit).strip().lower()
    if raw.upper() in SENTINELS:
        raise ValueError('MISSING_MASS')
    if unit not in SCALES:
        raise ValueError('BAD_UNIT')
    if len(raw) > 24 or not FORM.fullmatch(raw):
        raise ValueError('BAD_MASS')
    value = Decimal(raw.replace(',', '')) * SCALES[unit]
    if not 0 <= value <= 10**10 or value != value.to_integral_value():
        raise ValueError('BAD_MASS')
    return int(value)


def grams(mg):
    return f'{Decimal(mg) / 1000:,.3f}' if mg is not None else '—'
