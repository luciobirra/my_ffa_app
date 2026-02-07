def test_register_user(client):
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@test.com",
            "password": "1234"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Registrazione completata" in response.data


def test_login_user(client, create_user):
    create_user("pippo", "pippo@test.com", "1234")

    response = client.post(
        "/login",
        data={
            "email": "pippo@test.com",
            "password": "1234"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

