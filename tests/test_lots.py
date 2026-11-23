from app.blend.lots import identify


def test_alias_is_resolved(clean):
    row=next(r for r in clean.lots['rows'] if r['data']['ticket']=='0002')
    assert (row['lot'],row['pigment'],row['lot_sources'][0]['line'])==('W-041','钛白',3)


def test_unknown_alias(dirty):
    assert [(r['data']['lot'],r['code']) for r in dirty.lots['isolated'] if not r['lot_sources']]==[('无登记','LOT_UNKNOWN')]


def test_conflicting_alias_keeps_both_codes(dirty):
    result=next(r for r in dirty.lots['isolated'] if r['code']=='LOT_CONFLICT')
    assert [r['data']['lot'] for r in result['lot_sources']]==['C-001','C-002']


def test_repeated_identical_alias_is_not_conflict(clean):
    catalog=clean.data['lots'][0]
    result=identify(clean.tares['rows'],catalog+[catalog[0] | {'line':7}])
    source=next(r for r in result['rows'] if r['data']['ticket']=='0001')
    assert (source['lot'],[r['line'] for r in source['lot_sources']])==('R-017',[2,7])


def test_mixed_action_cannot_silently_use_stated_lot(clean):
    row=next(r for r in clean.tares['rows'] if r['data']['action']=='RETURN')
    out=identify([row | {'data':row['data'] | {'lot':'青'}}],clean.data['lots'][0])
    assert out['isolated'][0]['code']=='MIXED_OUTPUT'


def test_bad_catalog_key_is_isolated(clean):
    row=clean.data['lots'][0][0]
    out=identify([], [row | {'data':row['data'] | {'alias':'　'}}])
    assert [(r['line'],r['code']) for r in out['invalid_catalog']]==[(2,'BAD_KEY')]
