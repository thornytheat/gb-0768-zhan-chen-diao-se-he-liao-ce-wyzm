import json
from hashlib import sha256

from app.faults import LedgerError
from app.receipts.contract import Workshop
from app.receipts.sheet import scan
from app.settings import DATA, SHEETS

NAMES = ('job', *SHEETS)


def read_sample(name):
    if name not in ('dirty','clean'):
        raise LedgerError('SAMPLE_ABSENT','找不到样例收据',404)
    return {key:(DATA/name/(key+('.json' if key=='job' else '.csv'))).read_bytes().decode()
            for key in NAMES}


def open_packet(payload):
    if isinstance(payload,dict) and set(payload)=={'sample'}:
        name=str(payload['sample'])
        return read_sample(name),name
    files=payload.get('sheets') if isinstance(payload,dict) and set(payload)=={'sheets'} else None
    if not isinstance(files,dict) or set(files)!=set(NAMES) or any(
        not isinstance(v,str) or len(v)>150_000 for v in files.values()
    ):
        raise LedgerError('PACKET_INVALID','需提供工单与四份 UTF-8 表单')
    try:
        for value in files.values():
            value.encode()
    except UnicodeEncodeError:
        raise LedgerError('PACKET_INVALID','表单字符编码错误') from None
    return files,'upload'


def parse_packet(files):
    try:
        job=json.loads(files['job'].removeprefix('\ufeff'))
    except (json.JSONDecodeError,RecursionError):
        raise LedgerError('JOB_INVALID','工单 JSON 无效') from None
    return Workshop.parse(job), {key:scan(files[key],key) for key in SHEETS}


def checksums(files):
    return {key:sha256(value.encode()).hexdigest() for key,value in files.items()}
