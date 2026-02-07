import io
from conftest import login
from models import User, db


def test_profile_requires_login(client):
    response = client.get("/profile", follow_redirects=True)

    # redirect al login (o pagina login renderizzata)
    assert response.status_code == 200
    assert b"Login" in response.data


def test_profile_page_access(client, create_user):
    create_user("user1", "u1@test.com", "1234")

    login(client, "u1@test.com", "1234")

    response = client.get("/profile")

    assert response.status_code == 200
    assert b"Impostazioni profilo" in response.data


def test_profile_update_username_email(client, create_user):
    user = create_user("oldname", "old@test.com", "1234")

    login(client, "old@test.com", "1234")

    response = client.post(
        "/profile",
        data={
            "username": "newname",
            "email": "new@test.com",
            "password": ""
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    updated = db.session.get(User, user.id)
    assert updated.username == "newname"
    assert updated.email == "new@test.com"


def test_profile_update_avatar(client, create_user):
    user = create_user("avataruser", "avatar@test.com", "1234")

    login(client, "avatar@test.com", "1234")

    data = {
        "username": "avataruser",
        "email": "avatar@test.com",
        "password": "",
        "avatar": (io.BytesIO(b"fake image"), "avatar.jpg"),
    }

    response = client.post(
        "/profile",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )

    assert response.status_code == 200

    updated = db.session.get(User, user.id)
    assert updated.avatar is not None
    assert updated.avatar.startswith("user_")

