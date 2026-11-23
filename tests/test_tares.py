import pytest
from app.receipts.tare import weigh
from app.receipts.units import milligrams


def test_mass_units(dirty):
    # TRAP-15
    rows={r['data']['ticket']:r for r in dirty.tares['rows']}
    assert [(rows[k]['gross_mg'],rows[k]['net_mg']) for k in ('0002','0006')]==[(220000,200000),(60000,50000)]


def test_fullwidth_and_grouping(dirty):
    # TRAP-06
    row=next(r for r in dirty.tares['rows'] if r['data']['ticket']=='0008')
    assert (row['data']['gross'],row['net_mg'],milligrams('１，２３４.５','g'))==('３６',26000,1234500)


def test_sentinel(dirty):
    # TRAP-07
    assert [(r['data']['gross'],r.get('net_mg')) for r in dirty.tares['isolated'] if r['code']=='MISSING_MASS']==[('NULL',None)]


def test_overlapping_tare_versions(dirty):
    # TRAP-25
    r=next(r for r in dirty.tares['isolated'] if r['code']=='TARE_OVERLAP')
    assert (r['data']['ticket'],[v['data']['version'] for v in r['tares']])==('0010',['TB1','TB2'])


def test_negative_net_is_visible(dirty):
    r=next(r for r in dirty.tares['isolated'] if r['code']=='NEGATIVE_NET')
    assert (r['net_mg'],r['tare_mg'])==(-2000,10000)


def test_exact_version_boundary(clean):
    row=clean.weighings['tickets'][0]
    results=weigh([row | {'at':clean.job.end.isoformat()}],clean.data['tares'][0])
    assert results['isolated'][0]['code']=='TARE_MISSING'


def test_fractional_milligram_rejected():
    with pytest.raises(ValueError,match='BAD_MASS'):
        milligrams('0.0001','g')
