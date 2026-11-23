from hashlib import sha256

from app.faults import LedgerError
from app.ledger.identity import encoded
from app.receipts.packet import checksums


def certify(record):
    if checksums(record['sheets'])!=record['manifest']['files']:
        raise LedgerError('HASH_DISAGREEMENT','原件与收据摘要不一致',409)
    report=record['snapshot']['balance']
    for row in report['lines']:
        if row['opening_mg']+row['issued_mg']!=row['applied_mg']+row['loss_mg']+row['returned_mg']+row['disputed_mg']:
            raise LedgerError('MASS_UNBALANCED','至少一个成分重量不平',409)
    return {'document':'调色收据证据', 'sha256':sha256(encoded(record)).hexdigest(),
            'key':record['manifest']['key'],'mass_check_mg':0,**record}
