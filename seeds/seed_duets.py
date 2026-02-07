from app import app
from models import db, DuetParticipant
from data.duets import DUETS

inserted = 0

with app.app_context():
    # Inserimento (idempotente)
    for name in DUETS:
        if not DuetParticipant.query.filter_by(name=name).first():
            db.session.add(DuetParticipant(name=name))
            inserted += 1

    db.session.commit()

    print(f"\n✅ Duetti inseriti: {inserted}\n")

    # Stampa stato DB
    print("🎶 DUETTI NEL DB:")
    duets = DuetParticipant.query.order_by(DuetParticipant.name).all()

    for d in duets:
        print(f" - [{d.id}] {d.name}")

    print(f"\nTotale duetti: {len(duets)}")

