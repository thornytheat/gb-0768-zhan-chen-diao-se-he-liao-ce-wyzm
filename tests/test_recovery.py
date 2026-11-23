from app.blend.share import split_mass


def test_actual_remaining_material(dirty):
    r=next(r for r in dirty.recovery['rows'] if r['data']['ticket']=='0005')
    assert r['before_mg']=={'R-017':50000,'W-041':100000}
    assert r['parts_mg']=={'R-017':40000,'W-041':80000}
    assert r['after_mg']=={'R-017':10000,'W-041':20000}


def test_exact_rounding_residue():
    # TRAP-10 and TRAP-24
    assert split_mass(2,{'B':1,'A':1,'C':1})=={'A':1,'B':1}
    assert split_mass(1,{'Z':9000,'A':1})=={'Z':1}


def test_overdraw_preserves_balance(dirty):
    assert [(r['data']['ticket'],r['code']) for r in dirty.recovery['isolated']]==[('0014','OVERDRAW')]
    assert dirty.recovery['pending_mg']['A12']=={'R-017':10000,'W-041':20000}


def test_draining_pot_keeps_source_lines(clean):
    r=next(r for r in clean.recovery['rows'] if r['data']['ticket']=='0005')
    assert r['issue_lines']=={'R-017':[2],'W-041':[3]}
    assert clean.recovery['pending_mg']['A12']=={}


def test_every_split_preserves_ticket_mass(dirty):
    assert len(dirty.recovery['rows'])==28
    assert all(sum(r['parts_mg'].values())==r['net_mg'] for r in dirty.recovery['rows'])


def test_late_bucket_rebuilt_in_event_order(dirty):
    rows=[r for r in dirty.recovery['rows'] if r['data']['pot']=='B08']
    assert [r['data']['ticket'] for r in rows]==['0006','0007','0008']
    assert rows[-1]['parts_mg']=={'B-003':26000}
