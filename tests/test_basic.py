import pytest
from app import create_app, db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_register_page(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_dashboard_redirects_unauthenticated(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
