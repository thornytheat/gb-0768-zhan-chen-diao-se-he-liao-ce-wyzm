from dataclasses import dataclass
from datetime import datetime, timedelta

from app.faults import LedgerError
from app.receipts.clock import timepoint

COLUMNS = {
    'weights': 'ticket,pot,container,action,lot,gross,unit,occurred,received',
    'tares': 'container,version,start,end,mass,unit',
    'lots': 'alias,lot,pigment',
    'claims': 'lot,mass,unit,receipt',
}
ACTIONS = ('OPEN','ISSUE','APPLY','LOSS','RETURN')


@dataclass(frozen=True)
class Workshop:
    order: str
    start: datetime
    end: datetime
    cutoff: datetime

    @classmethod
    def parse(cls, obj):
        try:
            order = obj['order']
            a,b,c = (timepoint(obj[k]) for k in ('start','end','cutoff'))
            if not isinstance(order,str) or not 1 <= len(order.strip()) <= 64 or not a < b <= c or b-a > timedelta(days=31):
                raise ValueError
        except (TypeError,KeyError,ValueError):
            raise LedgerError('JOB_INVALID','工单编号或封账时间不合法') from None
        return cls(order,a,b,c)
