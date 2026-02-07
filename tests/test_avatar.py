import io


def test_register_with_avatar(client):
    data = {
        "username": "avataruser",
        "email": "avatar@test.com",
        "password": "1234",
        "avatar": (io.BytesIO(b"fake image"), "avatar.jpg"),
    }

    response = client.post(
        "/register",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Registrazione completata" in response.data
