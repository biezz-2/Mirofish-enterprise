import pytest
from flask import Flask, jsonify
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.auth import require_auth, require_resource_ownership

app = Flask(__name__)
app.testing = True
app.config['AUTH_REQUIRED'] = True

@app.route('/protected')
@require_auth
def protected_route():
    return jsonify({"success": True})

@app.route('/project/<project_id>')
@require_auth
@require_resource_ownership('project')
def project_route(project_id):
    return jsonify({"success": True, "project_id": project_id})

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_missing_auth_returns_401(client):
    response = client.get('/protected')
    assert response.status_code == 401
    assert not response.json['success']
    assert response.json['error']['code'] == 'UNAUTHORIZED'

def test_invalid_auth_format_returns_401(client):
    response = client.get('/protected', headers={'Authorization': 'Token'})
    assert response.status_code == 401
    assert not response.json['success']
    assert response.json['error']['code'] == 'UNAUTHORIZED'

def test_empty_token_returns_401(client):
    response = client.get('/protected', headers={'Authorization': 'Bearer '})
    assert response.status_code == 401
    assert not response.json['success']
    assert response.json['error']['code'] == 'UNAUTHORIZED'

def test_valid_auth_returns_200(client):
    response = client.get('/protected', headers={'Authorization': 'Bearer valid_token'})
    assert response.status_code == 200
    assert response.json['success']

def test_project_route_without_auth_returns_401(client):
    response = client.get('/project/123')
    assert response.status_code == 401

def test_project_route_with_auth_returns_200(client):
    response = client.get('/project/123', headers={'Authorization': 'Bearer valid_token'})
    assert response.status_code == 200
    assert response.json['success']

def test_idor_prevention_forbidden_id_returns_403(client):
    response = client.get('/project/forbidden_id', headers={'Authorization': 'Bearer valid_token'})
    assert response.status_code == 403
    assert not response.json['success']
    assert response.json['error']['code'] == 'FORBIDDEN'
