from datetime import UTC, datetime
from hashlib import sha256
import json
from time import perf_counter

from app.receipts.packet import checksums
from app.settings import EDITION


def encoded(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()


def seal_id(files):
    hashes=checksums(files)
    return sha256(encoded({'edition':EDITION,'files':hashes})).hexdigest(),hashes


def docket(job, key, source, hashes, started):
    return {'key':key,'order':job.order,'source':source,'edition':EDITION,'files':hashes,
            'issued_at':datetime.now(UTC).isoformat(timespec='seconds'), 'elapsed_ms':round((perf_counter()-started)*1000),
            'start':job.start.isoformat(),'end':job.end.isoformat(),'cutoff':job.cutoff.isoformat()}
