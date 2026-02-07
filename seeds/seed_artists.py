from app import app
from models import db, Participant
from data.artists import ARTISTS

inserted = 0

with app.app_context():
    # Inserimento (idempotente)
    for name in ARTISTS:
        if not Participant.query.filter_by(name=name).first():
            db.session.add(Participant(name=name))
            inserted += 1

    db.session.commit()

    print(f"\n✅ Partecipanti inseriti: {inserted}\n")

    # Stampa stato DB
    print("📋 PARTECIPANTI NEL DB:")
    participants = Participant.query.order_by(Participant.name).all()

    for p in participants:
        print(f" - [{p.id}] {p.name}")

    print(f"\nTotale partecipanti: {len(participants)}")





