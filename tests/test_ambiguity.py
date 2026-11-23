from app.blend.balance import settle
from app.blend.replay import rebuild
from app.receipts.packet import read_sample
from app.job import MixingJob


def _row(job, ticket):
    return next(r for r in job.recovery['rows'] if r['data']['ticket'] == ticket)


def test_same_minute_keeps_feasible_span(ambiguous):
    recovery = ambiguous.recovery
    assert recovery['scenarios'] == {'A12': 2}
    assert recovery['ambiguous'] is True and recovery['truncated'] is False
    assert recovery['ambiguity'] == [{'minute': '2026-11-08T01:00', 'pot': 'A12',
                                      'lines': [3, 4], 'scenarios': 2}]


def test_baseline_does_not_feed_new_material_into_earlier_apply(ambiguous):
    # 同刻的领用（票 0003）排在先前的上件（票 0002）之后，基准方案里
    # 上件不应分到新入罐的白料。
    row = _row(ambiguous, '0002')
    assert row['parts_mg'] == {'R-017': 60000}
    assert row['parts_min_mg'] == {'R-017': 42857, 'W-041': 0}
    assert row['uncertain_mg'] == {'R-017': 17143, 'W-041': 17143}
    assert row['provisional'] is True


def test_later_splits_do_not_pretend_guessed_ratio_is_real(ambiguous):
    # 回桶在另一分钟，但其成分分摊仍跨着两种可行先后，不能写成唯一实数。
    row = _row(ambiguous, '0005')
    assert row['parts_mg'] == {'R-017': 25000, 'W-041': 25000}
    assert row['parts_range_mg'] == {'R-017': [25000, 35714], 'W-041': [14286, 25000]}
    assert row.get('order_ambiguous') is None
    assert row['provisional'] is True


def test_claim_inside_span_is_reported_uncertain(ambiguous):
    lines = {line['lot']: line for line in ambiguous.balance['lines']}
    assert (lines['R-017']['code'], lines['R-017']['difference_mg']) == ('UNCERTAIN', None)
    assert lines['R-017']['difference_range_mg'] == [-5000, 5714]
    assert lines['R-017']['provisional'] is True


def test_claim_outside_span_still_reports_range(ambiguous):
    line = {item['lot']: item for item in ambiguous.balance['lines']}['W-041']
    assert (line['code'], line['difference_mg']) == ('MISMATCH', -1000)
    assert line['difference_range_mg'] == [-11714, -1000]


def test_span_never_becomes_a_signed_match(ambiguous):
    # 申报正好落在区间中段也不得判 MATCH，否则就是把猜到的配比当实数。
    notes = [row for row in ambiguous.data['claims'][0]]
    for row in notes:
        row['data'] = row['data'] | {'mass': '32'}
    result = settle(ambiguous.recovery, [notes[0]])
    assert result['lines'][0]['code'] == 'UNCERTAIN'
    assert result['lines'][0]['difference_mg'] is None


def test_every_feasible_plan_is_balanced(ambiguous):
    for line in ambiguous.balance['lines']:
        assert line['check_mg'] == 0
        assert line['check_range_mg'] == [0, 0]


def test_ambiguous_totals_keep_joint_span(ambiguous):
    totals = ambiguous.balance['totals_range_mg']
    assert totals['opening_mg'] == [100000, 100000]
    assert totals['returned_mg'] == [50000, 50000]
    assert ambiguous.balance['provisional'] is True


def test_distinct_minutes_are_not_blended(ambiguous):
    # 不同分钟的记录先后明确，票 0004、0005 不额外标记先后不定。
    assert _row(ambiguous, '0004').get('order_ambiguous') is None
    assert _row(ambiguous, '0003').get('order_ambiguous') is True


def test_rebuild_does_not_need_at_field():
    # 旧调用方只有逐站记录，没有 at：按登记位置顺序复算。
    records = [
        {'line': 2, 'net_mg': 100000, 'lot': 'R-017', 'pigment': '铁红',
         'data': {'pot': 'A12', 'action': 'OPEN', 'ticket': '0001'}},
        {'line': 3, 'net_mg': 40000, 'lot': 'W-041', 'pigment': '钛白',
         'data': {'pot': 'A12', 'action': 'ISSUE', 'ticket': '0002'}},
        {'line': 4, 'net_mg': 50000,
         'data': {'pot': 'A12', 'action': 'APPLY', 'ticket': '0003'}},
    ]
    result = rebuild(records)
    assert result['scenarios'] == {'A12': 1}
    assert result['rows'][2]['parts_mg'] == {'R-017': 35714, 'W-041': 14286}


def test_ambiguous_sample_is_replayable_from_the_workbench(client):
    page = client.get('/studio/recovery?sample=ambiguous')
    assert page.status_code == 200
    assert '先后不定' in page.get_data(as_text=True)


def test_ambiguous_work_order_seals_once_and_keeps_note(client):
    first = client.post('/api/books', json={'sample': 'ambiguous'}).json
    again = client.post('/api/books', json={'sample': 'ambiguous'}).json
    assert (first['reused'], again['reused'], first['key'] == again['key']) == (False, True, True)
    receipt = client.get('/api/export/' + first['key']).json
    assert receipt['uncertainty']['provisional'] is True
    assert [line['lot'] for line in receipt['uncertainty']['lines']] == ['R-017', 'W-041']
    assert 'R-017' in {line['lot'] for line in receipt['snapshot']['balance']['lines']}


def test_sample_registry_keeps_old_codes_working():
    for name in ('dirty', 'clean', 'ambiguous'):
        assert MixingJob(read_sample(name)).balance['lines']
