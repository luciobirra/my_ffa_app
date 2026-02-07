from models import (
    calculate_user_score,
    db,
    User,
    Prediction,
    PredictionRank,
    OfficialRank
)


def test_score_no_predictions(create_user):
    """
    Utente senza prediction → score totale = 0
    """
    user = create_user("nopred", "nopred@test.com", "1234")

    result = calculate_user_score(user.id)

    assert isinstance(result, dict)
    assert "total" in result
    assert result["total"] == 0


def test_score_structure(create_user):
    """
    La funzione deve sempre ritornare una struttura coerente
    """
    user = create_user("struct", "struct@test.com", "1234")

    result = calculate_user_score(user.id)

    assert "total" in result
    assert "breakdown" in result
    assert isinstance(result["breakdown"], (list, dict))


def test_score_admin_is_zero(create_user):
    """
    Admin non partecipa al gioco → score = 0
    """
    admin = create_user("admin", "admin@test.com", "1234", role="admin")

    result = calculate_user_score(admin.id)

    assert result["total"] == 0


def test_score_increases_with_correct_prediction(create_user):
    user = create_user("bonus", "bonus@test.com", "1234")

    # prediction utente
    pred = Prediction(user_id=user.id)
    db.session.add(pred)
    db.session.commit()

    db.session.add(
        PredictionRank(
            prediction_id=pred.id,
            participant_id=1,
            position=1
        )
    )

    # risultato ufficiale
    db.session.add(
        OfficialRank(
            participant_id=1,
            position=1
        )
    )

    db.session.commit()

    result = calculate_user_score(user.id)

    assert result["total"] > 0


def test_score_penalized_when_prediction_wrong(create_user):
    user = create_user("malus", "malus@test.com", "1234")

    pred = Prediction(user_id=user.id)
    db.session.add(pred)
    db.session.commit()

    # prediction sbagliata
    db.session.add(
        PredictionRank(
            prediction_id=pred.id,
            participant_id=1,
            position=5
        )
    )

    # risultato ufficiale
    db.session.add(
        OfficialRank(
            participant_id=1,
            position=1
        )
    )

    db.session.commit()

    result = calculate_user_score(user.id)

    assert result["total"] <= 0


def test_score_breakdown_contains_entries(create_user):
    user = create_user("break", "break@test.com", "1234")

    result = calculate_user_score(user.id)

    assert "breakdown" in result
    assert isinstance(result["breakdown"], (list, dict))
