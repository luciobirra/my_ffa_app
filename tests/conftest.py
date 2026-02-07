import sys
import os

# aggiunge la root del progetto al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app import app as flask_app
from models import db, User, AppSettings


@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
    })

    with flask_app.app_context():
        db.create_all()

        # settings default: previsioni APERTE
        settings = AppSettings(predictions_open=True)
        db.session.add(settings)
        db.session.commit()

        yield flask_app

        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_user(app):
    def _create_user(username, email, password, role="user"):
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _create_user


def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True
    )
