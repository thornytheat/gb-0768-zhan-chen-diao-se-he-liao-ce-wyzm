from app.web import LINKS


def test_workbench_and_every_module_page(client):
    assert '克重收据' in client.get('/').get_data(as_text=True)
    for slug,label in LINKS.items():
        response=client.get('/studio/'+slug)
        assert response.status_code==200 and f'<h1>{label}</h1>' in response.get_data(as_text=True)


def test_backed_receipt_links_to_signed_artifact(client):
    key=client.post('/api/books',json={'sample':'dirty'}).json['key']
    assert f'href="/api/export/{key}"' in client.get('/studio/receipt?key='+key).get_data(as_text=True)


def test_failed_preview_has_explanation(client):
    response=client.get('/api/trial/unlisted/tares')
    assert (response.status_code,response.json['code'])==(404,'SAMPLE_ABSENT')
