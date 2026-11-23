from time import perf_counter

from app.job import MixingJob
from app.ledger.identity import docket, seal_id
from app.receipts.packet import open_packet


def close(book,payload):
    started=perf_counter()
    files,source=open_packet(payload)
    key,hashes=seal_id(files)
    existing=book.find(key)
    if existing:
        return existing,True
    job=MixingJob(files)
    snapshot=job.snapshot()
    packet={'manifest':docket(job.job,key,source,hashes,started),'sheets':files,'snapshot':snapshot}
    return book.write(key,packet)
