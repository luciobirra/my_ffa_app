from models import AppSettings
from conftest import login


def test_user_blocked_when_predictions_open(client, create_user):
    create_user("user1", "u1@test.com", "1234")

    login(client, "u1@test.com", "1234")

    response = client.get("/ranking", follow_redirects=True)

    assert b"Calma" in response.data


def test_user_can_access_when_predictions_closed(client, create_user, app):
    create_user("user2", "u2@test.com", "1234")

    with app.app_context():
        settings = AppSettings.query.first()
        settings.predictions_open = False
        from models import db
        db.session.commit()

    login(client, "u2@test.com", "1234")

    response = client.get("/ranking")

    assert response.status_code == 200


def test_admin_can_always_access_ranking(client, create_user):
    create_user("admin", "admin@test.com", "1234", role="admin")

    login(client, "admin@test.com", "1234")

    response = client.get("/ranking")

    assert response.status_code == 200

def test_anonymous_cannot_access_ranking(client):
    response = client.get("/ranking", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data
