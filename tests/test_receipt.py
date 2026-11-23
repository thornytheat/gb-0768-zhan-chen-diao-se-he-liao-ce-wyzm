from copy import deepcopy
from hashlib import sha256
import pytest
from app.faults import LedgerError
from app.ledger.identity import encoded
from app.ledger.signoff import certify

@pytest.fixture
def file(client):
    key=client.post('/api/books',json={'sample':'dirty'}).json['key']
    return client.get('/api/export/'+key)


def test_attachment(file):
    assert file.headers['Content-Disposition'].startswith('attachment; filename="palette-')
    assert file.json['mass_check_mg']==0


def test_rehash(file):
    doc=file.json
    root={k:doc[k] for k in ('manifest','sheets','snapshot')}
    assert sha256(encoded(root)).hexdigest()==doc['sha256']
    assert doc['manifest']['files']['weights']==sha256(doc['sheets']['weights'].encode()).hexdigest()


def test_rejects_forged_sheets(file):
    record=deepcopy(file.json); record['sheets']['tares']+='bogus'
    with pytest.raises(LedgerError) as err:
        certify(record)
    assert err.value.code=='HASH_DISAGREEMENT'


def test_rejects_component_imbalance(file):
    record=deepcopy(file.json); record['snapshot']['balance']['lines'][0]['returned_mg']+=1
    with pytest.raises(LedgerError) as err:
        certify(record)
    assert err.value.code=='MASS_UNBALANCED'


def test_preserves_raw_ambiguous_tares(file):
    rejects=file.json['snapshot']['tares']['isolated']
    assert [row['line'] for row in rejects[0]['tares']]==[3,5]


def test_unissued_receipt_is_not_downloaded(client):
    response=client.get('/api/export/unknown')
    assert (response.status_code,response.json['code'],response.headers.get('Content-Disposition'))==(404,'BOOK_UNKNOWN',None)
