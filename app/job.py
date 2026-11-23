from functools import cached_property

from app.blend.balance import settle
from app.blend.lots import identify
from app.blend.replay import rebuild
from app.receipts.packet import parse_packet
from app.receipts.tare import weigh
from app.receipts.tickets import eligible

VIEWS=('weighings','tares','lots','recovery','balance')


class MixingJob:
    def __init__(self, files):
        self.job,self.data=parse_packet(files)

    @cached_property
    def weighings(self):
        tickets,isolated=eligible(self.data['weights'][0],self.job)
        stats = self.data['weights'][1]
        count = {'source':stats['submitted'], 'kept':len(tickets),
                 'isolated':len(isolated)+len(stats['isolated']), 'headers':stats['repeated_headers']}
        return {'sheets':[summary for _,summary in self.data.values()], 'tickets':tickets,
                'isolated':isolated, 'count':count}

    @cached_property
    def tares(self):
        return weigh(self.weighings['tickets'],self.data['tares'][0])

    @cached_property
    def lots(self):
        return identify(self.tares['rows'], self.data['lots'][0])

    @cached_property
    def recovery(self):
        return rebuild(self.lots['rows'])

    @cached_property
    def balance(self):
        return settle(self.recovery,self.data['claims'][0])

    def snapshot(self):
        return {stage:getattr(self,stage) for stage in VIEWS}
