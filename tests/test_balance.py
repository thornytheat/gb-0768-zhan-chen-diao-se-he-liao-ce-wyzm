from app.blend.balance import settle


def test_dirty_weight_conservation(dirty):
    assert dirty.balance['totals']=={'opening_mg':100000,'issued_mg':250010,'applied_mg':140000,
                                    'loss_mg':30000,'returned_mg':146010,'disputed_mg':34000}
    assert all(r['check_mg']==0 for r in dirty.balance['lines'])


def test_clean_receipts_match(clean):
    assert (clean.balance['difference_lines'],clean.balance['totals']['disputed_mg'])==(0,0)


def test_each_receipt_delta(dirty):
    assert [(r['lot'],r['difference_mg'],r['code']) for r in dirty.balance['lines']]==[
        ('B-003',-4000,'MISMATCH'),('R-017',1000,'MISMATCH'),('W-041',0,'MATCH')]


def test_conflicting_receipt_not_summed(clean):
    notes=clean.data['claims'][0]
    extra=notes[0] | {'line':9,'data':notes[0]['data'] | {'mass':'90'}}
    r=settle(clean.recovery,notes+[extra])['lines'][1]
    assert (r['code'],r['claimed_mg'],[n['line'] for n in r['receipts']])==('CLAIM_CONFLICT',None,[2,9])


def test_absent_claim_is_distinct_from_zero(clean):
    rows=settle(clean.recovery,[])['lines']
    assert {(r['code'],r['difference_mg']) for r in rows}=={('NO_CLAIM',None)}


def test_only_claim_is_a_reported_delta(clean):
    fake=clean.data['claims'][0][0]
    result=settle({'rows':[],'pending_mg':{}},[fake])['lines'][0]
    assert (result['returned_mg'],result['difference_mg'],result['check_mg'])==(0,-50010,0)
