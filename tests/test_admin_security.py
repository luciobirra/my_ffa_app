from conftest import login


def test_admin_requires_login(client):
    """
    Utente NON loggato → redirect al login
    """
    response = client.get("/admin", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data


def test_user_cannot_access_admin_dashboard(client, create_user):
    """
    Utente normale → redirect alla dashboard
    """
    create_user("user1", "u1@test.com", "1234")

    login(client, "u1@test.com", "1234")

    response = client.get("/admin", follow_redirects=True)

    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_user_cannot_access_admin_results(client, create_user):
    """
    Utente normale → NON può accedere a /admin/results
    """
    create_user("user2", "u2@test.com", "1234")

    login(client, "u2@test.com", "1234")

    response = client.get("/admin/results", follow_redirects=True)

    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_admin_can_access_admin_dashboard(client, create_user):
    """
    Admin → accesso consentito
    """
    create_user("admin", "admin@test.com", "1234", role="admin")

    login(client, "admin@test.com", "1234")

    response = client.get("/admin")

    assert response.status_code == 200


def test_admin_can_access_admin_results(client, create_user):
    """
    Admin → accesso consentito a /admin/results
    """
    create_user("admin2", "admin2@test.com", "1234", role="admin")

    login(client, "admin2@test.com", "1234")

    response = client.get("/admin/results")

    assert response.status_code == 200


