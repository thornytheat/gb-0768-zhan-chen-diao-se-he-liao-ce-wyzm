from collections import defaultdict
from datetime import timedelta

from app.receipts.clock import timepoint
from app.receipts.contract import ACTIONS


def eligible(rows, job):
    by_ticket=defaultdict(list)
    rejected=[]
    for row in rows:
        fields=row['data']
        try:
            event, arrived=(timepoint(fields[key]) for key in ('occurred','received'))
            if not all(fields[k].strip() for k in ('ticket','pot','container')):
                raise ValueError('BAD_KEY')
            if fields['action'] not in ACTIONS:
                raise ValueError('BAD_ACTION')
            if not job.start<=event<job.end:
                raise ValueError('OUTSIDE')
            if arrived<event:
                raise ValueError('BAD_TIME')
            if arrived>job.cutoff:
                raise ValueError('AFTER_CUTOFF')
        except ValueError as error:
            rejected.append(row | {'code':str(error)})
            continue
        by_ticket[fields['ticket']].append(row | {'at':event.isoformat(), 'delay':arrived-event>timedelta(hours=1),
                                                  'received_utc':arrived.isoformat()})
    accepted=[]
    for ticket, options in sorted(by_ticket.items()):
        options.sort(key=lambda row:(row['received_utc'],row['line']))
        distinct={tuple(row['data'][k] for k in ('pot','container','action','lot','gross','unit'))+(row['at'],) for row in options}
        if len(distinct)>1:
            rejected.extend(row | {'code':'TICKET_CONFLICT'} for row in options)
        else:
            accepted.append(options[0])
            rejected.extend(row | {'code':'TICKET_DUPLICATE'} for row in options[1:])
    accepted.sort(key=lambda row:(row['at'], ACTIONS.index(row['data']['action']), row['data']['ticket']))
    return accepted,rejected
