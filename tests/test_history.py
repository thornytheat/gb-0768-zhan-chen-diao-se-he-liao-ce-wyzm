from concurrent.futures import ThreadPoolExecutor
from app.ledger.bookshelf import Bookshelf
from app.ledger.closeout import close
from app.main import create_app
from app.receipts.packet import read_sample


def test_same_payload_reuses_one_record(client):
    a,b=[client.post('/api/books',json={'sample':'dirty'}).json for _ in range(2)]
    assert (a['reused'],b['reused'],a['manifest']==b['manifest'])==(False,True,True)
    assert [i['key'] for i in client.get('/api/books').json['books']]==[a['key']]


def test_invalid_upload_leaves_no_files(client,tmp_path):
    response=client.post('/api/books',json={'sheets':read_sample('clean') | {'claims':'no,col'}})
    assert (response.status_code,response.json['code'],list(tmp_path.iterdir()))==(422,'HEADER_INVALID',[])


def test_concurrent_commit_is_atomic(tmp_path):
    book=Bookshelf(tmp_path)
    with ThreadPoolExecutor(2) as executor:
        results=list(executor.map(lambda _:close(book,{'sample':'dirty'}),range(2)))
    assert sorted(r[1] for r in results)==[False,True]
    assert results[0][0]==results[1][0] and len(list(tmp_path.iterdir()))==1


def test_restart_retrieves_exact_book(client,tmp_path):
    key=client.post('/api/books',json={'sample':'dirty'}).json['key']
    path='/api/books/'+key
    assert create_app(tmp_path).test_client().get(path).data==client.get(path).data


def test_different_inputs_form_different_keys(client):
    keys=[client.post('/api/books',json={'sample':n}).json['key'] for n in ('clean','dirty')]
    assert len(set(keys))==2


def test_invalid_payload_is_recoverable(client):
    r=client.post('/api/books',json={'sheets':{}})
    assert (r.status_code,r.json['code'])==(422,'PACKET_INVALID')
    assert client.post('/api/books',json={'sample':'clean'}).json['totals']['returned_mg']==180010
