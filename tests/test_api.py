"""Интеграционные проверки реальных контрактов FastAPI."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def restore_catalog():
    assert client.post('/api/reset').status_code == 200
    yield
    assert client.post('/api/reset').status_code == 200


def test_html_catalog_and_assets():
    response = client.get('/')
    assert response.status_code == 200
    assert 'Каталог устройств' in response.text
    assert client.get('/static/app.js').status_code == 200
    assert client.get('/static/style.css').status_code == 200


def test_list_contains_ids_and_metadata():
    response = client.get('/api/products')
    assert response.status_code == 200
    body = response.json()
    assert [p['id'] for p in body['data']] == [1,2,3,4,5]
    assert body['meta'] == {'count': 5, 'total': 5}


def test_get_existing_product_by_id():
    result = client.get('/api/products/5')
    assert result.status_code == 200
    assert result.json()['name'] == 'Relay Controller'


def test_nonexistent_product_404():
    assert client.get('/api/products/999').status_code == 404


def test_path_parameter_validation_422():
    assert client.get('/api/products/0').status_code == 422
    assert client.get('/api/products/abc').status_code == 422


def test_list_filter_and_limit():
    result = client.get('/api/products', params={'type':'sensor', 'limit':2})
    assert result.status_code == 200
    assert result.json()['meta'] == {'count':2,'total':5}
    assert all(p['type']=='sensor' for p in result.json()['data'])


def test_post_creates_resource_and_location():
    response = client.post('/api/products', json={
        'name': 'CO2 Sensor', 'type':'sensor', 'price':35.5, 'tags':['climate']
    })
    assert response.status_code == 201
    assert response.headers['location'] == '/api/products/6'
    assert response.json()['id'] == 6
    assert client.get('/api/products/6').status_code == 200
    assert client.get('/api/products').json()['meta']['total'] == 6


def test_duplicate_name_causes_conflict():
    result = client.post('/api/products',json={
        'name':'humidity sensor', 'type':'sensor','price':10
    })
    assert result.status_code == 409


def test_post_validation_error():
    result = client.post('/api/products',json={
        'name':'X', 'type':'sensor','price':-5
    })
    assert result.status_code == 422


def test_put_replaces_all_fields():
    response = client.put('/api/products/5',json={
        'name':'Relay Controller 2','type':'controller', 'price':77.5,
        'status':'inactive', 'tags':['updated']
    })
    assert response.status_code == 200
    assert response.json()['name'] == 'Relay Controller 2'
    assert response.json()['tags'] == ['updated']


def test_patch_changes_selected_fields_only():
    response = client.patch('/api/products/5', json={'price':80.0})
    assert response.status_code == 200
    assert response.json()['name'] == 'Relay Controller'
    assert response.json()['price'] == 80.0


def test_patch_null_is_rejected():
    assert client.patch('/api/products/5',json={'name':None}).status_code == 422


def test_delete_returns_204_and_resource_disappears():
    response = client.delete('/api/products/5')
    assert response.status_code == 204
    assert response.content == b''
    assert client.get('/api/products/5').status_code == 404
    assert client.get('/api/products').json()['meta']['total'] == 4


def test_missing_resource_cannot_be_updated_or_deleted():
    assert client.patch('/api/products/999',json={'price':2}).status_code == 404
    assert client.put('/api/products/999',json={'name':'Xyz','type':'sensor','price':2}).status_code == 404
    assert client.delete('/api/products/999').status_code == 404


def test_reset_restores_original_data_and_id_sequence():
    client.post('/api/products',json={'name':'CO2 Sensor','type':'sensor','price':2})
    client.delete('/api/products/5')
    response = client.post('/api/reset')
    assert response.status_code == 200
    assert response.json()['restored'] == 5
    assert client.get('/api/products').json()['meta']['total'] == 5
    result = client.post('/api/products',json={'name':'CO2 Sensor','type':'sensor','price':2})
    assert result.json()['id'] == 6


def test_openapi_lists_crud_operations():
    assert client.get('/docs').status_code == 200
    schema=client.get('/openapi.json')
    assert schema.status_code == 200
    paths=schema.json()['paths']
    assert set(paths['/api/products']) == {'get','post'}
    assert set(paths['/api/products/{product_id}']) == {'get','put','patch','delete'}
    assert set(paths['/api/reset']) == {'post'}
