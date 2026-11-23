import pytest
from app.faults import LedgerError
from app.receipts.sheet import scan


def test_bom(dirty):
    # TRAP-02
    assert dirty.data['weights'][0][0]['data']['ticket']=='0005'


def test_repeat_and_input_balance(dirty):
    # TRAP-04
    assert dirty.weighings['count']=={'source':40,'kept':34,'isolated':5,'headers':1}


def test_ragged_row(dirty):
    # TRAP-05
    assert dirty.data['weights'][1]['isolated']==[{'sheet':'weights','line':31,'raw':['dangling','A12','EXTRA'],'code':'WIDTH'}]


def test_ticket_conflict(dirty):
    # TRAP-14
    rows=[r for r in dirty.weighings['isolated'] if r['code']=='TICKET_CONFLICT']
    assert [(r['line'],r['data']['gross']) for r in rows]==[(40,'25'),(41,'26')]
    assert not any(r['data']['ticket']=='0017' for r in dirty.weighings['tickets'])


def test_delayed_return_and_cutoff(dirty):
    # TRAP-13
    late=[r for r in dirty.weighings['tickets'] if r['delay']]
    assert [(r['data']['ticket'],r['data']['action']) for r in late]==[('0008','RETURN')]
    assert any(r['code']=='AFTER_CUTOFF' and r['data']['ticket']=='0015' for r in dirty.weighings['isolated'])


def test_empty_sheet_states():
    assert scan('lot,mass,unit,receipt','claims')[1]['state']=='header_only'
    assert scan('lot,mass,unit,receipt\n\n','claims')[1]['state']=='blank_rows'
    with pytest.raises(LedgerError) as err:
        scan('','claims')
    assert err.value.code=='EMPTY_SHEET'
